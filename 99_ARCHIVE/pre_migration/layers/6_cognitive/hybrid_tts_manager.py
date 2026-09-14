#!/usr/bin/env python3
#===============================================================================
# HYBRID TEXT-TO-SPEECH MANAGER
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Local and Cloud TTS with intelligent routing
#===============================================================================

import os
import json
import requests
import pyttsx3
from typing import Dict, Optional
from pathlib import Path
import io
from datetime import datetime

class HybridTTSManager:
    """Hybrid TTS Manager with local engines and cloud providers"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.local_engine = None
        self.load_local_engine()
        
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
            "speech_synthesis": {
                "local_provider": {
                    "voice": "de",
                    "speed": 1.0,
                    "pitch": 1.0
                },
                "cloud_provider": {
                    "model": "tts-1",
                    "voice": "alloy"
                }
            }
        }
    
    def load_local_engine(self):
        """Load local TTS engine"""
        try:
            local_config = self.config["speech_synthesis"]["local_provider"]
            
            print("Loading local TTS engine...")
            self.local_engine = pyttsx3.init()
            
            # Configure voice
            voice = local_config.get("voice", "de")
            speed = local_config.get("speed", 1.0)
            pitch = local_config.get("pitch", 1.0)
            
            # Set properties
            self.local_engine.setProperty('rate', speed * 150)  # Base rate is 150
            self.local_engine.setProperty('volume', 1.0)
            
            # Try to set voice
            voices = self.local_engine.getProperty('voices')
            if voices:
                for v in voices:
                    if voice.lower() in v.name.lower():
                        self.local_engine.setProperty('voice', v.id)
                        break
            
            print("Local TTS engine loaded successfully")
            
        except Exception as e:
            print(f"Failed to load local TTS engine: {e}")
            self.local_engine = None
    
    def synthesize_local(self, text: str, voice: str = None, speed: float = None) -> Dict:
        """Synthesize speech using local engine"""
        if not self.local_engine:
            return {"success": False, "error": "Local engine not loaded", "provider": "local"}
        
        try:
            # Configure parameters
            if voice:
                voices = self.local_engine.getProperty('voices')
                if voices:
                    for v in voices:
                        if voice.lower() in v.name.lower():
                            self.local_engine.setProperty('voice', v.id)
                            break
            
            if speed:
                self.local_engine.setProperty('rate', speed * 150)
            
            # Generate speech (save to file for return)
            output_file = f"temp_speech_{datetime.now().timestamp()}.wav"
            self.local_engine.save_to_file(text, output_file)
            self.local_engine.runAndWait()
            
            # Read the file
            if os.path.exists(output_file):
                with open(output_file, 'rb') as f:
                    audio_data = f.read()
                os.remove(output_file)
                
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "format": "wav",
                    "duration": len(text) * 0.1,  # Rough estimate
                    "provider": "local"
                }
            else:
                return {"success": False, "error": "Failed to generate audio file", "provider": "local"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "local"}
    
    def synthesize_cloud(self, text: str, voice: str = None, speed: float = None) -> Dict:
        """Synthesize speech using cloud provider (OpenAI TTS)"""
        try:
            cloud_config = self.config["speech_synthesis"]["cloud_provider"]
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return {"success": False, "error": "OpenAI API key not configured", "provider": "cloud"}
            
            api_endpoint = cloud_config.get("api_endpoint", "https://api.openai.com/v1/audio/speech")
            model = cloud_config.get("model", "tts-1")
            default_voice = cloud_config.get("voice", "alloy")
            
            # Prepare request
            data = {
                "model": model,
                "input": text,
                "voice": voice or default_voice
            }
            
            if speed:
                data["speed"] = speed
            
            # Make request
            response = requests.post(
                api_endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                audio_data = response.content
                
                return {
                    "success": True,
                    "audio_data": audio_data,
                    "format": "mp3",
                    "duration": len(audio_data) / 32000,  # Rough estimate
                    "provider": "cloud"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": "cloud"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "cloud"}
    
    def synthesize_hybrid(self, text: str, voice: str = None, speed: float = None) -> Dict:
        """Hybrid synthesis with intelligent routing"""
        strategy = self.config["speech_synthesis"]["selection_strategy"]
        priority = strategy.get("priority", "local_first")
        
        if priority == "local_first":
            # Try local first
            result = self.synthesize_local(text, voice, speed)
            
            if result["success"]:
                return result
            
            # Fallback to cloud
            if strategy.get("fallback_on_error", True):
                print("Local synthesis failed, falling back to cloud")
                return self.synthesize_cloud(text, voice, speed)
        
        elif priority == "cloud_first":
            # Try cloud first
            result = self.synthesize_cloud(text, voice, speed)
            
            if result["success"]:
                return result
            
            # Fallback to local
            if strategy.get("fallback_on_error", True):
                print("Cloud synthesis failed, falling back to local")
                return self.synthesize_local(text, voice, speed)
        
        return {"success": False, "error": "No provider available"}
    
    def synthesize_with_quality_check(self, text: str, voice: str = None, speed: float = None) -> Dict:
        """Synthesize with quality threshold check"""
        result = self.synthesize_hybrid(text, voice, speed)
        
        if not result["success"]:
            return result
        
        # Quality checks
        strategy = self.config["speech_synthesis"]["selection_strategy"]
        quality_threshold = strategy.get("quality_threshold", 0.7)
        
        # Check audio data size
        if len(result["audio_data"]) < 100:
            return {"success": False, "error": "Audio data too small", "provider": result["provider"]}
        
        return result
    
    def get_available_voices(self) -> Dict:
        """Get available voices for both providers"""
        voices = {
            "local": [],
            "cloud": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        }
        
        if self.local_engine:
            try:
                local_voices = self.local_engine.getProperty('voices')
                if local_voices:
                    voices["local"] = [v.name for v in local_voices]
            except:
                pass
        
        return voices
    
    def get_synthesis_statistics(self) -> Dict:
        """Get synthesis statistics"""
        return {
            "local_engine_loaded": self.local_engine is not None,
            "cloud_available": bool(os.getenv("OPENAI_API_KEY")),
            "available_voices": self.get_available_voices(),
            "strategy": self.config["speech_synthesis"]["selection_strategy"].get("priority", "local_first")
        }

def main():
    """Main entry point for testing"""
    manager = HybridTTSManager()
    
    print("Hybrid TTS Manager Statistics:")
    stats = manager.get_synthesis_statistics()
    print(json.dumps(stats, indent=2))
    
    # Test synthesis
    print("\nTesting synthesis...")
    test_text = "Hallo, dies ist ein Test der Sprachsynthese."
    result = manager.synthesize_hybrid(test_text)
    
    if result["success"]:
        print(f"✅ Synthesis successful: {result['provider']}")
        print(f"   Duration: {result['duration']:.2f}s")
        print(f"   Format: {result['format']}")
    else:
        print(f"❌ Synthesis failed: {result['error']}")

if __name__ == "__main__":
    main()