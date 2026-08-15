#!/usr/bin/env python3
#===============================================================================
# COMMUNICATION INTERFACE SYSTEM
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Handle WebSocket/HTTP/GRPC communication for voice interface
#===============================================================================

import os
import json
import asyncio
import websockets
from typing import Dict, Optional, Callable
from pathlib import Path
from datetime import datetime
import jwt
import hashlib
from functools import wraps
import time

class AuthenticationManager:
    """JWT-based authentication manager"""
    
    def __init__(self, secret_key: str = "default_secret_key"):
        self.secret_key = secret_key
        self.token_expiry = 3600  # 1 hour
        self.refresh_enabled = True
        
    def generate_token(self, user_id: str, permissions: list = None) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user_id,
            "permissions": permissions or ["read", "write"],
            "exp": time.time() + self.token_expiry,
            "iat": time.time()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return token
    
    def validate_token(self, token: str) -> Dict:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return {
                "valid": True,
                "user_id": payload.get("user_id"),
                "permissions": payload.get("permissions"),
                "exp": payload.get("exp")
            }
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh expired token"""
        if not self.refresh_enabled:
            return None
        
        # Validate token (even if expired)
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"], options={"verify_exp": False})
            user_id = payload.get("user_id")
            permissions = payload.get("permissions")
            
            # Generate new token
            return self.generate_token(user_id, permissions)
        except:
            return None

class RateLimiter:
    """Rate limiting manager"""
    
    def __init__(self, requests_per_minute: int = 100, burst_size: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.user_requests: Dict[str, list] = {}
        
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limits"""
        current_time = time.time()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Remove requests older than 1 minute
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < 60
        ]
        
        # Check rate limit
        if len(self.user_requests[user_id]) >= self.requests_per_minute:
            return False
        
        # Check burst limit
        recent_requests = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < 1
        ]
        if len(recent_requests) >= self.burst_size:
            return False
        
        # Add current request
        self.user_requests[user_id].append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: str) -> Dict:
        """Get remaining request count for user"""
        current_time = time.time()
        
        if user_id not in self.user_requests:
            return {"remaining": self.requests_per_minute, "burst_remaining": self.burst_size}
        
        # Count requests in last minute
        minute_requests = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < 60
        ]
        
        # Count requests in last second
        second_requests = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < 1
        ]
        
        return {
            "remaining": self.requests_per_minute - len(minute_requests),
            "burst_remaining": self.burst_size - len(second_requests)
        }

class WebSocketHandler:
    """WebSocket communication handler"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.ws_config = self.config.get("communication_interface", {}).get("protocols", {}).get("websocket", {})
        
        self.port = self.ws_config.get("port", 8765)
        self.ssl_enabled = self.ws_config.get("ssl", True)
        self.auth_enabled = self.ws_config.get("authentication", True)
        
        self.auth_manager = AuthenticationManager()
        self.rate_limiter = RateLimiter()
        
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
        self.is_running = False
        
    def load_config(self, config_path: str) -> Dict:
        """Load communication configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "communication_interface": {
                "protocols": {
                    "websocket": {
                        "enabled": True,
                        "port": 8765,
                        "ssl": True,
                        "authentication": True
                    }
                }
            }
        }
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type] = handler
        print(f"Registered handler for: {message_type}")
    
    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection"""
        connection_id = str(id(websocket))
        print(f"New connection: {connection_id}")
        
        try:
            # Authenticate if required
            if self.auth_enabled:
                token = await websocket.recv()
                auth_result = self.auth_manager.validate_token(token)
                
                if not auth_result["valid"]:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Authentication failed"
                    }))
                    return
                
                user_id = auth_result["user_id"]
                print(f"Authenticated user: {user_id}")
            else:
                user_id = connection_id
            
            # Store connection
            self.active_connections[connection_id] = websocket
            
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "connection_id": connection_id,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Handle messages
            async for message in websocket:
                await self.handle_message(connection_id, user_id, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"Connection closed: {connection_id}")
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            # Remove connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
    
    async def handle_message(self, connection_id: str, user_id: str, message: str):
        """Handle incoming message"""
        try:
            # Rate limit check
            if not self.rate_limiter.check_rate_limit(user_id):
                await self.active_connections[connection_id].send(json.dumps({
                    "type": "error",
                    "message": "Rate limit exceeded"
                }))
                return
            
            # Parse message
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            # Handle message type
            if message_type in self.message_handlers:
                handler = self.message_handlers[message_type]
                response = await handler(connection_id, user_id, data)
                
                if response:
                    await self.active_connections[connection_id].send(json.dumps(response))
            else:
                await self.active_connections[connection_id].send(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
                
        except json.JSONDecodeError:
            await self.active_connections[connection_id].send(json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))
        except Exception as e:
            await self.active_connections[connection_id].send(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    async def broadcast_message(self, message: Dict, exclude_connection: str = None):
        """Broadcast message to all active connections"""
        message_str = json.dumps(message)
        
        for connection_id, websocket in self.active_connections.items():
            if connection_id != exclude_connection:
                try:
                    await websocket.send(message_str)
                except:
                    pass
    
    async def send_to_connection(self, connection_id: str, message: Dict):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send(json.dumps(message))
            except:
                pass
    
    async def start_server(self):
        """Start WebSocket server"""
        self.is_running = True
        
        server_address = f"0.0.0.0:{self.port}"
        if self.ssl_enabled:
            server_address = f"0.0.0.0:{self.port}"
        
        print(f"Starting WebSocket server on {server_address}")
        
        async with websockets.serve(self.handle_connection, "0.0.0.0", self.port):
            print(f"WebSocket server running on port {self.port}")
            await asyncio.Future()  # Run forever
    
    def stop_server(self):
        """Stop WebSocket server"""
        self.is_running = False
        print("WebSocket server stopped")
    
    def get_connection_statistics(self) -> Dict:
        """Get connection statistics"""
        return {
            "is_running": self.is_running,
            "active_connections": len(self.active_connections),
            "port": self.port,
            "ssl_enabled": self.ssl_enabled,
            "auth_enabled": self.auth_enabled,
            "registered_handlers": list(self.message_handlers.keys())
        }

class VoiceInterfaceServer:
    """Main voice interface server"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.ws_handler = WebSocketHandler(config_path)
        
        # Register default message handlers
        self.register_default_handlers()
        
    def load_config(self, config_path: str) -> Dict:
        """Load voice interface configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "communication_interface": {
                "protocols": {
                    "websocket": {
                        "enabled": True,
                        "port": 8765
                    }
                }
            }
        }
    
    def register_default_handlers(self):
        """Register default message handlers"""
        
        async def handle_audio_data(connection_id: str, user_id: str, data: Dict):
            """Handle audio data message"""
            # This would integrate with the audio processor
            return {
                "type": "audio_processed",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        
        async def handle_text_message(connection_id: str, user_id: str, data: Dict):
            """Handle text message"""
            text = data.get("text", "")
            
            # This would integrate with the agent orchestrator
            return {
                "type": "text_response",
                "response": f"Received: {text}",
                "timestamp": datetime.now().isoformat()
            }
        
        async def handle_status_request(connection_id: str, user_id: str, data: Dict):
            """Handle status request"""
            return {
                "type": "status",
                "status": "online",
                "connections": len(self.ws_handler.active_connections),
                "timestamp": datetime.now().isoformat()
            }
        
        self.ws_handler.register_message_handler("audio_data", handle_audio_data)
        self.ws_handler.register_message_handler("text_message", handle_text_message)
        self.ws_handler.register_message_handler("status_request", handle_status_request)
    
    async def start(self):
        """Start voice interface server"""
        print("Starting Voice Interface Server...")
        await self.ws_handler.start_server()
    
    def stop(self):
        """Stop voice interface server"""
        self.ws_handler.stop_server()
    
    def get_server_status(self) -> Dict:
        """Get server status"""
        return {
            "websocket": self.ws_handler.get_connection_statistics(),
            "config": self.config.get("communication_interface", {})
        }

async def main():
    """Main entry point for testing"""
    server = VoiceInterfaceServer()
    
    print("Voice Interface Server Status:")
    status = server.get_server_status()
    print(json.dumps(status, indent=2))
    
    # Test authentication
    print("\nTesting authentication...")
    auth_manager = server.ws_handler.auth_manager
    token = auth_manager.generate_token("test_user", ["read", "write"])
    print(f"Generated token: {token[:20]}...")
    
    validation = auth_manager.validate_token(token)
    print(f"Token validation: {validation}")
    
    # Test rate limiting
    print("\nTesting rate limiting...")
    rate_limiter = server.ws_handler.rate_limiter
    for i in range(5):
        allowed = rate_limiter.check_rate_limit("test_user")
        remaining = rate_limiter.get_remaining_requests("test_user")
        print(f"Request {i+1}: Allowed={allowed}, Remaining={remaining}")
    
    print("\nVoice Interface Server ready to start...")
    print("To start the server, call: await server.start()")

if __name__ == "__main__":
    asyncio.run(main())