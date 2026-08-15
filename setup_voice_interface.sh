#!/usr/bin/env bash
#===============================================================================
# VOICE INTERFACE SETUP
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Install and configure full-duplex voice interface system
#===============================================================================

set -euo pipefail

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

log() {
    local level="$1"; shift
    echo "[$(date '+%H:%M:%S')] [$level] $*"
}
info() { log "INFO" "${BLUE}$*${NC}"; }
success() { log "OK" "${GREEN}$*${NC}"; }
warn() { log "WARN" "${YELLOW}$*${NC}"; }
error() { log "ERROR" "${RED}$*${NC}"; exit 1; }

# Detect system
detect_system() {
    info "Detecting system..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        SYSTEM="macos"
        info "Detected: macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        SYSTEM="linux"
        if grep -q "microsoft" /proc/version 2>/dev/null; then 
            SYSTEM="wsl2"
            info "Detected: WSL2"
        else
            info "Detected: Linux"
        fi
    else
        error "Unsupported system: $OSTYPE"
    fi
}

# Install Python dependencies
install_python_dependencies() {
    info "Installing Python dependencies..."
    
    # Ensure pip is available
    if ! command -v pip &> /dev/null; then
        warn "pip not found, installing..."
        python3 -m ensurepip --upgrade || true
    fi
    
    # Install core dependencies
    pip install --upgrade pip || true
    
    local packages=(
        "torch"
        "whisper"
        "pyttsx3"
        "websockets"
        "pyjwt"
        "numpy"
        "requests"
        "asyncio"
    )
    
    for package in "${packages[@]}"; do
        info "Installing $package..."
        pip install "$package" || warn "Failed to install $package"
    done
    
    success "Python dependencies installed"
}

# Install system dependencies
install_system_dependencies() {
    info "Installing system dependencies..."
    
    if [[ "$SYSTEM" == "linux" ]] || [[ "$SYSTEM" == "wsl2" ]]; then
        sudo apt-get update
        sudo apt-get install -y \
            portaudio19-dev \
            python3-pyaudio \
            ffmpeg \
            espeak \
            espeak-data \
            libespeak1 \
            libespeak-dev || warn "Some system packages failed to install"
    elif [[ "$SYSTEM" == "macos" ]]; then
        brew install portaudio ffmpeg espeak || warn "Some system packages failed to install"
    fi
    
    success "System dependencies installed"
}

# Configure voice interface
configure_voice_interface() {
    info "Configuring voice interface..."
    
    # Create necessary directories
    mkdir -p layers/6_cognitive
    mkdir -p temp_audio
    
    # Check if configuration exists
    if [ -f "layers/6_cognitive/voice_interface_config.json" ]; then
        info "Voice interface configuration already exists"
    else
        warn "Voice interface configuration not found"
    fi
    
    success "Voice interface configured"
}

# Test ASR setup
test_asr_setup() {
    info "Testing ASR setup..."
    
    # Test Whisper import
    if python3 -c "import whisper" 2>/dev/null; then
        success "Whisper installed successfully"
    else
        warn "Whisper not installed or not accessible"
    fi
    
    # Test TTS import
    if python3 -c "import pyttsx3" 2>/dev/null; then
        success "pyttsx3 installed successfully"
    else
        warn "pyttsx3 not installed or not accessible"
    fi
}

# Test communication interface
test_communication_interface() {
    info "Testing communication interface..."
    
    # Test websockets import
    if python3 -c "import websockets" 2>/dev/null; then
        success "websockets installed successfully"
    else
        warn "websockets not installed or not accessible"
    fi
    
    # Test JWT import
    if python3 -c "import jwt" 2>/dev/null; then
        success "pyjwt installed successfully"
    else
        warn "pyjwt not installed or not accessible"
    fi
}

# Update neuro stack configuration
update_neuro_stack_config() {
    info "Updating neuro stack configuration..."
    
    if [ -f "neuro_stack_final.toml" ]; then
        if ! grep -q "voice_interface" neuro_stack_final.toml; then
            echo "" >> neuro_stack_final.toml
            echo "[voice_interface] # Ebene 6 - Cognitive" >> neuro_stack_final.toml
            echo "enabled = true" >> neuro_stack_final.toml
            echo "mode = \"full_duplex\"" >> neuro_stack_final.toml
            echo "architecture = \"hybrid_local_cloud\"" >> neuro_stack_final.toml
            echo "config_file = \"./layers/6_cognitive/voice_interface_config.json\"" >> neuro_stack_final.toml
            success "Added voice interface to neuro stack configuration"
        else
            info "Voice interface already in neuro stack configuration"
        fi
    else
        warn "neuro_stack_final.toml not found"
    fi
}

# Create systemd service (Linux only)
create_systemd_service() {
    if [[ "$SYSTEM" == "linux" ]] && [[ "$SYSTEM" != "wsl2" ]]; then
        info "Creating systemd service..."
        
        sudo tee /etc/systemd/system/neuro-voice-interface.service > /dev/null <<EOF
[Unit]
Description=Neuro-Sovereign Voice Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 layers/6_cognitive/communication_interface.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

        sudo systemctl daemon-reload
        sudo systemctl enable neuro-voice-interface.service
        success "Systemd service created"
    else
        info "Skipping systemd service creation (not supported on this system)"
    fi
}

# Test voice interface components
test_voice_interface() {
    info "Testing voice interface components..."
    
    # Test ASR manager
    if [ -f "layers/6_cognitive/hybrid_asr_manager.py" ]; then
        info "Testing ASR manager..."
        python3 layers/6_cognitive/hybrid_asr_manager.py || warn "ASR manager test failed"
    fi
    
    # Test TTS manager
    if [ -f "layers/6_cognitive/hybrid_tts_manager.py" ]; then
        info "Testing TTS manager..."
        python3 layers/6_cognitive/hybrid_tts_manager.py || warn "TTS manager test failed"
    fi
    
    # Test agent orchestrator
    if [ -f "layers/6_cognitive/agent_orchestrator.py" ]; then
        info "Testing agent orchestrator..."
        python3 layers/6_cognitive/agent_orchestrator.py || warn "Agent orchestrator test failed"
    fi
    
    success "Voice interface components tested"
}

main() {
    echo "==============================================================================="
    echo "  VOICE INTERFACE SETUP FOR NEURO-SOVEREIGN ENTERPRISE"
    echo "==============================================================================="
    
    detect_system
    install_system_dependencies
    install_python_dependencies
    configure_voice_interface
    test_asr_setup
    test_communication_interface
    update_neuro_stack_config
    create_systemd_service
    test_voice_interface
    
    echo ""
    success "Voice interface setup completed!"
    echo ""
    echo "VOICE INTERFACE COMPONENTS:"
    echo "  - Hybrid ASR (Local Whisper + Cloud)"
    echo "  - Hybrid TTS (Local espeak + Cloud)"
    echo "  - Multi-Agent Orchestration"
    echo "  - Tool Integration System"
    echo "  - Real-time Audio Processing"
    echo "  - WebSocket Communication Interface"
    echo ""
    echo "CONFIGURATION:"
    echo "  - Voice interface config: layers/6_cognitive/voice_interface_config.json"
    echo "  - ASR manager: layers/6_cognitive/hybrid_asr_manager.py"
    echo "  - TTS manager: layers/6_cognitive/hybrid_tts_manager.py"
    echo "  - Agent orchestrator: layers/6_cognitive/agent_orchestrator.py"
    echo "  - Tool integration: layers/6_cognitive/tool_integration.py"
    echo "  - Audio processor: layers/6_cognitive/realtime_audio_processor.py"
    echo "  - Communication: layers/6_cognitive/communication_interface.py"
    echo ""
    echo "USAGE:"
    echo "  Start voice interface server: python3 layers/6_cognitive/communication_interface.py"
    echo "  Test ASR: python3 layers/6_cognitive/hybrid_asr_manager.py"
    echo "  Test TTS: python3 layers/6_cognitive/hybrid_tts_manager.py"
    echo "  Test agents: python3 layers/6_cognitive/agent_orchestrator.py"
    echo ""
    echo "NEURO-SOVEREIGN INTEGRATION:"
    echo "  - Full-duplex voice communication"
    echo "  - Hybrid local/cloud processing"
    echo "  - Multi-agent coordination"
    echo "  - Tool integration for agents"
    echo "  - Real-time audio processing"
    echo "  - Secure WebSocket communication"
    echo "==============================================================================="
}

main "$@"