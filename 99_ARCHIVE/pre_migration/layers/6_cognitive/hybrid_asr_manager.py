#!/usr/bin/env python3
#===============================================================================
# HYBRID AUTOMATIC SPEECH RECOGNITION MANAGER
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Local and Cloud ASR with intelligent routing
#===============================================================================

import os
import json
import torch
import whisper
import requests
import numpy as np
from typing import Dict, Optional, Tuple
from pathlib import Path
import wave
import io
from datetime import datetime

class HybridASRManager:
    """Hybrid ASR Manager with local Whisper and cloud providers"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.local_model = None
        self.load_local_model()
        
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
            "speech_recognition": {
                "local_provider": {
                    "model": "base",
                    "device": "cpu"
                },
                "cloud_provider": {
                    "model": "whisper-1"
                }
            }
        }
    
    def load_local_model(self):
        """Load local Whisper model"""
        try:
            local_config = self.config["speech_recognition"]["local_provider"]
            model_name = local_config.get("model", "base")
            device = local_config.get("device", "cpu")
            
            print(f"Loading local Whisper model: {model_name}")
            self.local_model = whisper.load_model(model_name, device=device)
            print("Local Whisper model loaded successfully")
            
        except Exception as e:
            print(f"Failed to load local Whisper model: {e}")
            self.local_model = None
    
    def transcribe_local(self, audio_data: bytes, language: str = "auto") -> Dict:
        """Transcribe audio using local Whisper"""
        if not self.local_model:
            return {"success": False, "error": "Local model not loaded", "provider": "local"}
        
        try:
            # Convert bytes to audio file
            audio_file = io.BytesIO(audio_data)
            audio = whisper.load_audio(audio_file)
            
            # Transcribe
            result = self.local_model.transcribe(
                audio,
                language=language if language != "auto" else None,
                fp16=False  # Use FP32 for CPU compatibility
            )
            
            return {
                "success": True,
                "text": result["text"],
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "provider": "local",
                "duration": result.get("duration", 0)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "local"}
    
    def transcribe_cloud(self, audio_data: bytes, language: str = "auto") -> Dict:
        """Transcribe audio using cloud provider (OpenAI Whisper)"""
        try:
            cloud_config = self.config["speech_recognition"]["cloud_provider"]
            api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return {"success": False, "error": "OpenAI API key not configured", "provider": "cloud"}
            
            api_endpoint = cloud_config.get("api_endpoint", "https://api.openai.com/v1/audio/transcriptions")
            model = cloud_config.get("model", "whisper-1")
            
            # Prepare files
            files = {
                "file": ("audio.wav", audio_data, "audio/wav"),
                "model": (None, model)
            }
            
            if language != "auto":
                files["language"] = (None, language)
            
            # Make request
            response = requests.post(
                api_endpoint,
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result.get("text", ""),
                    "language": result.get("language", "unknown"),
                    "duration": result.get("duration", 0),
                    "provider": "cloud"
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}", "provider": "cloud"}
                
        except Exception as e:
            return {"success": False, "error": str(e), "provider": "cloud"}
    
    def transcribe_hybrid(self, audio_data: bytes, language: str = "auto") -> Dict:
        """Hybrid transcription with intelligent routing"""
        strategy = self.config["speech_recognition"]["selection_strategy"]
        priority = strategy.get("priority", "local_first")
        
        if priority == "local_first":
            # Try local first
            result = self.transcribe_local(audio_data, language)
            
            if result["success"]:
                return result
            
            # Fallback to cloud
            if strategy.get("fallback_on_error", True):
                print("Local transcription failed, falling back to cloud")
                return self.transcribe_cloud(audio_data, language)
        
        elif priority == "cloud_first":
            # Try cloud first
            result = self.transcribe_cloud(audio_data, language)
            
            if result["success"]:
                return result
            
            # Fallback to local
            if strategy.get("fallback_on_error", True):
                print("Cloud transcription failed, falling back to local")
                return self.transcribe_local(audio_data, language)
        
        return {"success": False, "error": "No provider available"}
    
    def transcribe_with_quality_check(self, audio_data: bytes, language: str = "auto") -> Dict:
        """Transcribe with quality threshold check"""
        result = self.transcribe_hybrid(audio_data, language)
        
        if not result["success"]:
            return result
        
        # Quality checks
        strategy = self.config["speech_recognition"]["selection_strategy"]
        quality_threshold = strategy.get("quality_threshold", 0.8)
        
        # Check text length (minimum confidence indicator)
        if len(result["text"]) < 5:
            return {"success": False, "error": "Transcription too short", "provider": result["provider"]}
        
        # Check for special characters (noise indicator)
        special_chars = sum(1 for c in result["text"] if not c.isalnum() and not c.isspace())
        if special_chars > len(result["text"]) * 0.3:
            return {"success": False, "error": "Too much noise detected", "provider": result["provider"]}
        
        return result
    
    def supported_languages(self) -> list:
        """Get supported languages"""
        return [
            "auto", "en", "de", "fr", "es", "it", "pt", "nl", "pl", "ru", 
            "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th", "id", "ms"
        ]
    
    def get_transcription_statistics(self) -> Dict:
        """Get transcription statistics"""
        return {
            "local_model_loaded": self.local_model is not None,
            "local_model_size": "base" if self.local_model else "none",
            "cloud_available": bool(os.getenv("OPENAI_API_KEY")),
            "supported_languages": self.supported_languages(),
            "strategy": self.config["speech_recognition"]["selection_strategy"].get("priority", "local_first")
        }

def main():
    """Main entry point for testing"""
    manager = HybridASRManager()
    
    print("Hybrid ASR Manager Statistics:")
    stats = manager.get_transcription_statistics()
    print(json.dumps(stats, indent=2))
    
    # Test with dummy audio (would normally use real audio)
    print("\nNote: To test transcription, provide actual audio data")
    print("Usage: manager.transcribe_hybrid(audio_bytes, language='de')")

if __name__ == "__main__":
    main()