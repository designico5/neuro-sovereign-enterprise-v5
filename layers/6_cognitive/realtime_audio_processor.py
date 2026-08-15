#!/usr/bin/env python3
#===============================================================================
# REAL-TIME AUDIO PROCESSING SYSTEM
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Process audio in real-time for full-duplex communication
#===============================================================================

import os
import json
import numpy as np
import wave
import asyncio
from typing import Dict, Optional, Callable
from pathlib import Path
from datetime import datetime
import queue
import threading

class AudioProcessor:
    """Real-time audio processor"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.audio_config = self.config.get("real_time_processing", {}).get("audio_processing", {})
        self.streaming_config = self.config.get("real_time_processing", {}).get("streaming", {})
        
        # Audio parameters
        self.sample_rate = self.audio_config.get("sample_rate", 16000)
        self.channels = self.audio_config.get("channels", 1)
        self.bit_depth = self.audio_config.get("bit_depth", 16)
        self.buffer_size = self.audio_config.get("buffer_size", 1024)
        self.latency_target_ms = self.audio_config.get("latency_target_ms", 500)
        
        # Processing queues
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Processing state
        self.is_processing = False
        self.processing_thread = None
        
        # Callbacks
        self.on_audio_processed: Optional[Callable] = None
        self.on_vad_detected: Optional[Callable] = None
        
    def load_config(self, config_path: str) -> Dict:
        """Load audio processing configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "real_time_processing": {
                "audio_processing": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "bit_depth": 16,
                    "buffer_size": 1024,
                    "latency_target_ms": 500
                },
                "streaming": {
                    "enabled": True,
                    "protocol": "websocket",
                    "compression": "opus",
                    "vad": True,
                    "noise_suppression": True
                }
            }
        }
    
    def start_processing(self):
        """Start real-time audio processing"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        print("Real-time audio processing started")
    
    def stop_processing(self):
        """Stop real-time audio processing"""
        self.is_processing = False
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        print("Real-time audio processing stopped")
    
    def _processing_loop(self):
        """Main processing loop"""
        while self.is_processing:
            try:
                # Get audio data from input queue
                audio_data = self.input_queue.get(timeout=0.1)
                
                # Process audio
                processed_audio = self._process_audio(audio_data)
                
                # Put processed audio in output queue
                self.output_queue.put(processed_audio)
                
                # Trigger callback if registered
                if self.on_audio_processed:
                    self.on_audio_processed(processed_audio)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Audio processing error: {e}")
    
    def _process_audio(self, audio_data: bytes) -> bytes:
        """Process audio data"""
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Apply noise reduction if enabled
        if self.streaming_config.get("noise_suppression", True):
            audio_array = self._noise_reduction(audio_array)
        
        # Apply VAD if enabled
        if self.streaming_config.get("vad", True):
            speech_detected = self._voice_activity_detection(audio_array)
            
            if speech_detected and self.on_vad_detected:
                self.on_vad_detected(audio_array)
        
        # Convert back to bytes
        return audio_array.astype(np.int16).tobytes()
    
    def _noise_reduction(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply noise reduction"""
        # Simple spectral subtraction for noise reduction
        # In production, use more sophisticated algorithms
        
        # FFT
        fft = np.fft.fft(audio_array)
        magnitude = np.abs(fft)
        phase = np.angle(fft)
        
        # Estimate noise floor (simple approach)
        noise_floor = np.percentile(magnitude, 10)
        
        # Subtract noise floor
        magnitude = np.maximum(magnitude - noise_floor, 0)
        
        # Reconstruct signal
        fft_clean = magnitude * np.exp(1j * phase)
        audio_clean = np.fft.ifft(fft_clean).real
        
        return audio_clean.astype(np.int16)
    
    def _voice_activity_detection(self, audio_array: np.ndarray) -> bool:
        """Detect voice activity"""
        # Simple energy-based VAD
        energy = np.sum(audio_array ** 2) / len(audio_array)
        
        # Dynamic threshold based on recent audio
        threshold = np.percentile(np.abs(audio_array), 75)
        
        return energy > threshold * 1.5
    
    def add_audio_input(self, audio_data: bytes):
        """Add audio data to input queue"""
        self.input_queue.put(audio_data)
    
    def get_audio_output(self) -> Optional[bytes]:
        """Get processed audio from output queue"""
        try:
            return self.output_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_processing_statistics(self) -> Dict:
        """Get processing statistics"""
        return {
            "is_processing": self.is_processing,
            "input_queue_size": self.input_queue.qsize(),
            "output_queue_size": self.output_queue.qsize(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "buffer_size": self.buffer_size,
            "latency_target_ms": self.latency_target_ms,
            "noise_suppression": self.streaming_config.get("noise_suppression", True),
            "vad": self.streaming_config.get("vad", True)
        }

class AudioStreamer:
    """Audio streaming handler"""
    
    def __init__(self, config_path: str = "layers/6_cognitive/voice_interface_config.json"):
        self.config = self.load_config(config_path)
        self.streaming_config = self.config.get("real_time_processing", {}).get("streaming", {})
        
        self.protocol = self.streaming_config.get("protocol", "websocket")
        self.compression = self.streaming_config.get("compression", "opus")
        self.vad_enabled = self.streaming_config.get("vad", True)
        
        self.audio_processor = AudioProcessor(config_path)
        self.is_streaming = False
        
    def load_config(self, config_path: str) -> Dict:
        """Load streaming configuration"""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "real_time_processing": {
                "streaming": {
                    "enabled": True,
                    "protocol": "websocket",
                    "compression": "opus",
                    "vad": True,
                    "noise_suppression": True
                }
            }
        }
    
    def start_streaming(self):
        """Start audio streaming"""
        self.audio_processor.start_processing()
        self.is_streaming = True
        print(f"Audio streaming started ({self.protocol} with {self.compression})")
    
    def stop_streaming(self):
        """Stop audio streaming"""
        self.audio_processor.stop_processing()
        self.is_streaming = False
        print("Audio streaming stopped")
    
    def stream_audio(self, audio_data: bytes):
        """Stream audio data"""
        if self.is_streaming:
            self.audio_processor.add_audio_input(audio_data)
    
    def get_streamed_audio(self) -> Optional[bytes]:
        """Get streamed audio data"""
        if self.is_streaming:
            return self.audio_processor.get_audio_output()
        return None
    
    def get_streaming_statistics(self) -> Dict:
        """Get streaming statistics"""
        return {
            "is_streaming": self.is_streaming,
            "protocol": self.protocol,
            "compression": self.compression,
            "vad_enabled": self.vad_enabled,
            "audio_processor": self.audio_processor.get_processing_statistics()
        }

class AudioBuffer:
    """Audio buffer management"""
    
    def __init__(self, buffer_size: int = 1024):
        self.buffer_size = buffer_size
        self.buffer = np.zeros(buffer_size, dtype=np.int16)
        self.write_position = 0
        self.read_position = 0
        self.lock = threading.Lock()
    
    def write(self, audio_data: np.ndarray):
        """Write audio data to buffer"""
        with self.lock:
            data_length = len(audio_data)
            available_space = self.buffer_size - (self.write_position - self.read_position)
            
            if data_length > available_space:
                # Overflow - skip oldest data
                skip_amount = data_length - available_space
                self.read_position += skip_amount
            
            # Write data
            end_position = self.write_position + data_length
            if end_position <= self.buffer_size:
                self.buffer[self.write_position:end_position] = audio_data
            else:
                # Wrap around
                first_part = self.buffer_size - self.write_position
                self.buffer[self.write_position:] = audio_data[:first_part]
                self.buffer[:data_length - first_part] = audio_data[first_part:]
            
            self.write_position = end_position % self.buffer_size
    
    def read(self, frame_count: int) -> np.ndarray:
        """Read audio data from buffer"""
        with self.lock:
            available_data = self.write_position - self.read_position
            
            if available_data < frame_count:
                # Not enough data - return zeros
                return np.zeros(frame_count, dtype=np.int16)
            
            # Read data
            end_position = self.read_position + frame_count
            if end_position <= self.buffer_size:
                audio_data = self.buffer[self.read_position:end_position].copy()
            else:
                # Wrap around
                first_part = self.buffer_size - self.read_position
                audio_data = np.zeros(frame_count, dtype=np.int16)
                audio_data[:first_part] = self.buffer[self.read_position:]
                audio_data[first_part:] = self.buffer[:frame_count - first_part]
            
            self.read_position = end_position % self.buffer_size
            return audio_data
    
    def get_available_data(self) -> int:
        """Get amount of available data in buffer"""
        with self.lock:
            return self.write_position - self.read_position
    
    def clear(self):
        """Clear buffer"""
        with self.lock:
            self.buffer = np.zeros(self.buffer_size, dtype=np.int16)
            self.write_position = 0
            self.read_position = 0

def main():
    """Main entry point for testing"""
    audio_processor = AudioProcessor()
    
    print("Real-time Audio Processor Statistics:")
    stats = audio_processor.get_processing_statistics()
    print(json.dumps(stats, indent=2))
    
    # Test audio processing
    print("\nTesting audio processing...")
    audio_processor.start_processing()
    
    # Add dummy audio data
    dummy_audio = np.random.randint(-1000, 1000, 1024, dtype=np.int16).tobytes()
    audio_processor.add_audio_input(dummy_audio)
    
    # Get processed audio
    import time
    time.sleep(0.1)
    processed_audio = audio_processor.get_audio_output()
    
    if processed_audio:
        print(f"✅ Audio processed: {len(processed_audio)} bytes")
    else:
        print("❌ No processed audio available")
    
    audio_processor.stop_processing()
    
    # Test audio streaming
    print("\nTesting audio streaming...")
    streamer = AudioStreamer()
    streamer.start_streaming()
    
    print(f"Streaming statistics: {json.dumps(streamer.get_streaming_statistics(), indent=2)}")
    
    streamer.stop_streaming()

if __name__ == "__main__":
    main()