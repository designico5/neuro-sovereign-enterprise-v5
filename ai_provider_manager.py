#!/usr/bin/env python3
#===============================================================================
# AI PROVIDER MANAGER
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Manage multiple AI providers (OpenCodezen, Ollama Local) with intelligent routing
#===============================================================================

import os
import json
import requests
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import sqlite3

class AIProviderManager:
    """Intelligent AI provider management with neuro-sovereign integration"""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.load_provider_config()
        self.init_provider_db()
        
    def load_provider_config(self):
        """Load provider configuration"""
        try:
            with open(self.config_dir / "ai_providers_config.json") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print("Provider configuration not found, using defaults")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default provider configuration"""
        return {
            "ai_providers": {
                "opencodezen": {
                    "enabled": True,
                    "api_endpoint": "https://api.opencodezen.com/v1",
                    "env_variable": "OPENCODEZEN_API_KEY"
                },
                "ollama_local": {
                    "enabled": True,
                    "api_endpoint": "http://localhost:11434"
                }
            },
            "provider_selection_strategy": {
                "default_provider": "ollama_local",
                "fallback_provider": "opencodezen"
            }
        }
    
    def init_provider_db(self):
        """Initialize provider usage database"""
        db_path = self.config_dir / "state" / "graph" / "provider_usage.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS provider_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                task_type TEXT,
                tokens_used INTEGER,
                response_time_ms REAL,
                success BOOLEAN,
                timestamp REAL NOT NULL,
                cost_usd REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS provider_health (
                provider TEXT NOT NULL,
                last_check REAL NOT NULL,
                is_available BOOLEAN,
                response_time_ms REAL,
                error_rate REAL,
                PRIMARY KEY (provider)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def select_provider(self, 
                     task_type: str = "general",
                     privacy_sensitivity: str = "medium",
                     task_complexity: str = "medium",
                     availability: str = "online",
                     cost_preference: str = "minimize_cost") -> str:
        """Select best provider based on criteria"""
        
        strategy = self.config["provider_selection_strategy"]
        
        # Apply selection criteria
        if privacy_sensitivity == "high":
            return "ollama_local"
        elif privacy_sensitivity == "medium":
            if task_complexity == "complex":
                return "opencodezen"
            return "ollama_local"
        
        if task_complexity == "complex":
            return "opencodezen"
        
        if availability == "offline":
            return "ollama_local"
        
        if cost_preference == "minimize_cost":
            return "ollama_local"
        elif cost_preference == "maximize_performance":
            return "opencodezen"
        
        # Default to configured default
        return strategy["default_provider"]
    
    def check_provider_health(self, provider: str) -> Dict:
        """Check if provider is available and healthy"""
        provider_config = self.config["ai_providers"][provider]
        
        if not provider_config["enabled"]:
            return {"available": False, "reason": "provider_disabled"}
        
        try:
            if provider == "ollama_local":
                # Check if Ollama is running
                response = requests.get(f"{provider_config['api_endpoint']}/api/tags", timeout=5)
                is_available = response.status_code == 200
                response_time = response.elapsed.total_seconds() * 1000 if is_available else None
                
            elif provider == "opencodezen":
                # Check if API key is configured
                api_key = os.getenv(provider_config["env_variable"])
                if not api_key:
                    return {"available": False, "reason": "api_key_missing"}
                
                # Check API availability
                response = requests.get(f"{provider_config['api_endpoint']}/models", 
                                      headers={"Authorization": f"Bearer {api_key}"},
                                      timeout=10)
                is_available = response.status_code == 200
                response_time = response.elapsed.total_seconds() * 1000 if is_available else None
            
            elif provider == "openai":
                # Check if API key is configured
                api_key = os.getenv(provider_config["env_variable"])
                if not api_key:
                    return {"available": False, "reason": "api_key_missing"}
                
                # Check API availability
                response = requests.get(f"{provider_config['api_endpoint']}/models", 
                                      headers={"Authorization": f"Bearer {api_key}"},
                                      timeout=10)
                is_available = response.status_code == 200
                response_time = response.elapsed.total_seconds() * 1000 if is_available else None
            
            else:
                return {"available": False, "reason": "unknown_provider"}
            
            # Update health database
            self.update_provider_health(provider, is_available, response_time)
            
            return {
                "available": is_available,
                "response_time_ms": response_time,
                "reason": "ok" if is_available else "health_check_failed"
            }
            
        except requests.exceptions.RequestException as e:
            self.update_provider_health(provider, False, None)
            return {"available": False, "reason": str(e)}
    
    def update_provider_health(self, provider: str, is_available: bool, response_time: Optional[float]):
        """Update provider health in database"""
        db_path = self.config_dir / "state" / "graph" / "provider_usage.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO provider_health 
            (provider, last_check, is_available, response_time_ms, error_rate)
            VALUES (?, ?, ?, ?, COALESCE((SELECT error_rate FROM provider_health WHERE provider = ?), 0))
        ''', (provider, datetime.now().timestamp(), is_available, response_time, provider))
        
        conn.commit()
        conn.close()
    
    def call_provider(self, 
                    provider: str,
                    model: str,
                    prompt: str,
                    task_type: str = "general") -> Dict:
        """Call the selected AI provider"""
        
        provider_config = self.config["ai_providers"][provider]
        
        if provider == "ollama_local":
            return self.call_ollama(provider_config, model, prompt, task_type)
        elif provider == "opencodezen":
            return self.call_opencodezen(provider_config, model, prompt, task_type)
        elif provider == "openai":
            return self.call_openai(provider_config, model, prompt, task_type)
        else:
            return {"success": False, "error": "unknown_provider"}
    
    def call_ollama(self, provider_config: Dict, model: str, prompt: str, task_type: str) -> Dict:
        """Call Ollama local API"""
        try:
            response = requests.post(
                f"{provider_config['api_endpoint']}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                tokens_used = result.get("eval_count", 0) + result.get("prompt_count", 0)
                
                # Log request
                self.log_provider_request("ollama_local", model, task_type, 
                                        tokens_used, response.elapsed.total_seconds() * 1000, 
                                        True, 0.0)
                
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "model": model,
                    "tokens_used": tokens_used,
                    "provider": "ollama_local"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": "ollama_local"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e), "provider": "ollama_local"}
    
    def call_opencodezen(self, provider_config: Dict, model: str, prompt: str, task_type: str) -> Dict:
        """Call OpenCodezen API"""
        api_key = os.getenv(provider_config["env_variable"])
        
        if not api_key:
            return {"success": False, "error": "API key not configured", "provider": "opencodezen"}
        
        try:
            response = requests.post(
                f"{provider_config['api_endpoint']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                # Calculate cost (simplified estimation)
                cost = self.calculate_opencodezen_cost(model, tokens_used)
                
                # Log request
                self.log_provider_request("opencodezen", model, task_type,
                                        tokens_used, response.elapsed.total_seconds() * 1000,
                                        True, cost)
                
                return {
                    "success": True,
                    "response": result["choices"][0]["message"]["content"],
                    "model": model,
                    "tokens_used": tokens_used,
                    "cost_usd": cost,
                    "provider": "opencodezen"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": "opencodezen"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e), "provider": "opencodezen"}
    
    def calculate_opencodezen_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for OpenCodezen (simplified)"""
        # Simplified cost calculation - actual pricing may vary
        cost_per_1k_tokens = 0.001  # $0.001 per 1K tokens
        return (tokens / 1000) * cost_per_1k_tokens
    
    def call_openai(self, provider_config: Dict, model: str, prompt: str, task_type: str) -> Dict:
        """Call OpenAI API"""
        api_key = os.getenv(provider_config["env_variable"])
        
        if not api_key:
            return {"success": False, "error": "API key not configured", "provider": "openai"}
        
        try:
            response = requests.post(
                f"{provider_config['api_endpoint']}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                # Calculate cost (simplified estimation)
                cost = self.calculate_openai_cost(model, tokens_used)
                
                # Log request
                self.log_provider_request("openai", model, task_type,
                                        tokens_used, response.elapsed.total_seconds() * 1000,
                                        True, cost)
                
                return {
                    "success": True,
                    "response": result["choices"][0]["message"]["content"],
                    "model": model,
                    "tokens_used": tokens_used,
                    "cost_usd": cost,
                    "provider": "openai"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": "openai"}
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e), "provider": "openai"}
    
    def calculate_openai_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for OpenAI (simplified)"""
        # Simplified cost calculation - actual pricing may vary
        cost_per_1k_tokens = 0.002  # $0.002 per 1K tokens (approximate)
        if "gpt-4" in model.lower():
            cost_per_1k_tokens = 0.03  # Higher cost for GPT-4
        elif "o1" in model.lower():
            cost_per_1k_tokens = 0.05  # Higher cost for o1 models
        return (tokens / 1000) * cost_per_1k_tokens
    
    def log_provider_request(self, provider: str, model: str, task_type: str,
                           tokens_used: int, response_time_ms: float, 
                           success: bool, cost_usd: float):
        """Log provider request to database"""
        db_path = self.config_dir / "state" / "graph" / "provider_usage.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO provider_requests 
            (provider, model, task_type, tokens_used, response_time_ms, success, timestamp, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (provider, model, task_type, tokens_used, response_time_ms, 
              success, datetime.now().timestamp(), cost_usd))
        
        conn.commit()
        conn.close()
    
    def intelligent_routing(self, prompt: str, task_type: str = "general") -> Dict:
        """Intelligent routing with fallback"""
        
        # Analyze prompt for privacy sensitivity
        privacy_sensitivity = self.analyze_privacy_sensitivity(prompt)
        task_complexity = self.analyze_task_complexity(prompt)
        
        # Check for task-specific provider selection
        selection_criteria = self.config["provider_selection_strategy"].get("selection_criteria", {})
        task_type_providers = selection_criteria.get("task_type", {})
        
        if task_type in task_type_providers:
            preferred_provider = task_type_providers[task_type]
            if preferred_provider in self.config["ai_providers"]:
                primary_provider = preferred_provider
            else:
                primary_provider = self.select_provider(
                    task_type=task_type,
                    privacy_sensitivity=privacy_sensitivity,
                    task_complexity=task_complexity
                )
        else:
            # Select primary provider
            primary_provider = self.select_provider(
                task_type=task_type,
                privacy_sensitivity=privacy_sensitivity,
                task_complexity=task_complexity
            )
        
        # Check primary provider health
        health = self.check_provider_health(primary_provider)
        
        if not health["available"]:
            # Fallback to secondary provider
            fallback = self.config["provider_selection_strategy"]["fallback_provider"]
            print(f"Primary provider {primary_provider} unavailable, falling back to {fallback}")
            primary_provider = fallback
        
        # Select model based on provider
        model = self.select_model(primary_provider, task_complexity)
        
        # Call provider
        result = self.call_provider(primary_provider, model, prompt, task_type)
        
        if not result["success"]:
            # Try fallback if primary fails
            fallback = self.config["provider_selection_strategy"]["fallback_provider"]
            if fallback != primary_provider:
                print(f"Primary provider failed, trying fallback {fallback}")
                fallback_model = self.select_model(fallback, task_complexity)
                result = self.call_provider(fallback, fallback_model, prompt, task_type)
        
        return result
    
    def select_model(self, provider: str, complexity: str) -> str:
        """Select appropriate model based on provider and task complexity"""
        provider_config = self.config["ai_providers"][provider]
        models = provider_config["model_families"]
        
        if complexity == "simple":
            return models[0]  # Smallest model
        elif complexity == "medium":
            return models[len(models)//2]  # Mid-range model
        else:  # complex
            return models[-1]  # Largest model
    
    def analyze_privacy_sensitivity(self, prompt: str) -> str:
        """Analyze prompt for privacy sensitivity"""
        privacy_keywords = ["personal", "private", "confidential", "secret", "password", "credit card"]
        
        prompt_lower = prompt.lower()
        for keyword in privacy_keywords:
            if keyword in prompt_lower:
                return "high"
        
        return "medium"
    
    def analyze_task_complexity(self, prompt: str) -> str:
        """Analyze task complexity based on prompt length and content"""
        if len(prompt) < 100:
            return "simple"
        elif len(prompt) < 500:
            return "medium"
        else:
            return "complex"
    
    def get_provider_statistics(self) -> Dict:
        """Get provider usage statistics"""
        db_path = self.config_dir / "state" / "graph" / "provider_usage.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Request count by provider
        cursor.execute('''
            SELECT provider, COUNT(*) as count, AVG(response_time_ms) as avg_time, 
                   AVG(cost_usd) as avg_cost, AVG(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_rate
            FROM provider_requests
            GROUP BY provider
        ''')
        
        provider_stats = {}
        for row in cursor.fetchall():
            provider, count, avg_time, avg_cost, success_rate = row
            provider_stats[provider] = {
                "request_count": count,
                "avg_response_time_ms": avg_time,
                "avg_cost_usd": avg_cost,
                "success_rate": success_rate
            }
        
        conn.close()
        return provider_stats

def main():
    """Main entry point for testing"""
    manager = AIProviderManager()
    
    # Test provider health
    print("Checking provider health...")
    for provider in ["ollama_local", "opencodezen", "openai"]:
        health = manager.check_provider_health(provider)
        print(f"{provider}: {health}")
    
    # Test intelligent routing
    print("\nTesting intelligent routing...")
    test_prompt = "What is the capital of France?"
    result = manager.intelligent_routing(test_prompt, "general")
    print(f"Result: {result}")
    
    # Get statistics
    print("\nProvider statistics:")
    stats = manager.get_provider_statistics()
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()