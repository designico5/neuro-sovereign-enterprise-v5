#!/usr/bin/env bash
#===============================================================================
# OLLAMA LOCAL SETUP
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Install and configure Ollama for local AI inference
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

# Install Ollama
install_ollama() {
    info "Installing Ollama..."
    
    if command -v ollama &> /dev/null; then
        warn "Ollama already installed. Checking version..."
        ollama --version
        return
    fi
    
    if [[ "$SYSTEM" == "macos" ]]; then
        info "Installing Ollama for macOS..."
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$SYSTEM" == "linux" ]] || [[ "$SYSTEM" == "wsl2" ]]; then
        info "Installing Ollama for Linux..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    
    success "Ollama installed successfully"
}

# Start Ollama service
start_ollama() {
    info "Starting Ollama service..."
    
    if [[ "$SYSTEM" == "macos" ]]; then
        brew services start ollama || warn "Ollama service may already be running"
    elif [[ "$SYSTEM" == "linux" ]] || [[ "$SYSTEM" == "wsl2" ]]; then
        # Start Ollama in background
        nohup ollama serve > /dev/null 2>&1 &
        sleep 2
    fi
    
    success "Ollama service started"
}

# Download recommended models
download_models() {
    info "Downloading recommended models..."
    
    local models=(
        "llama3.1:8b"
        "mistral:7b"
        "codellama:7b"
        "gemma2:9b"
    )
    
    for model in "${models[@]}"; do
        info "Downloading $model..."
        ollama pull "$model" || warn "Failed to download $model"
    done
    
    success "Models downloaded"
}

# Test Ollama
test_ollama() {
    info "Testing Ollama installation..."
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        error "Ollama is not running. Please start it manually with: ollama serve"
    fi
    
    # Test simple generation
    info "Running test generation..."
    ollama run llama3.1:8b "Hello, this is a test." || warn "Test generation failed"
    
    success "Ollama test completed"
}

# Configure Neuro-Sovereign integration
configure_integration() {
    info "Configuring Neuro-Sovereign integration..."
    
    # Update .env with Ollama configuration
    if [ -f ".env" ]; then
        if ! grep -q "OLLAMA_HOST" .env; then
            echo "OLLAMA_HOST=http://localhost:11434" >> .env
            success "Added OLLAMA_HOST to .env"
        else
            info "OLLAMA_HOST already configured in .env"
        fi
    else
        echo "OLLAMA_HOST=http://localhost:11434" > .env
        success "Created .env with OLLAMA_HOST configuration"
    fi
    
    # Update provider configuration
    if [ -f "ai_providers_config.json" ]; then
        info "AI providers configuration already exists"
    else
        warn "AI providers configuration not found. This should have been created during installation."
    fi
}

# Setup GPU acceleration (optional)
setup_gpu() {
    info "Checking GPU acceleration..."
    
    if command -v nvidia-smi &> /dev/null; then
        info "NVIDIA GPU detected"
        success "GPU acceleration available for supported models"
    elif [[ "$SYSTEM" == "macos" ]]; then
        if [[ $(uname -m) == "arm64" ]]; then
            info "Apple Silicon detected - Metal acceleration available"
            success "GPU acceleration available for supported models"
        else
            warn "Intel Mac detected - CPU only"
        fi
    else
        warn "No GPU detected - CPU only"
    fi
}

# Create Ollama models directory
setup_models_dir() {
    info "Setting up models directory..."
    
    mkdir -p ~/.ollama/models
    success "Models directory ready"
}

main() {
    echo "==============================================================================="
    echo "  OLLAMA LOCAL SETUP FOR NEURO-SOVEREIGN ENTERPRISE"
    echo "==============================================================================="
    
    detect_system
    setup_models_dir
    install_ollama
    start_ollama
    download_models
    test_ollama
    configure_integration
    setup_gpu
    
    echo ""
    success "Ollama setup completed!"
    echo ""
    echo "OLLAMA CONFIGURATION:"
    echo "  Service: http://localhost:11434"
    echo "  Models: llama3.1:8b, mistral:7b, codellama:7b, gemma2:9b"
    echo "  Integration: AI Provider Manager configured"
    echo ""
    echo "USAGE:"
    echo "  Start Ollama: ollama serve"
    echo "  Run model: ollama run llama3.1:8b"
    echo "  List models: ollama list"
    echo "  Python integration: python ai_provider_manager.py"
    echo ""
    echo "NEURO-SOVEREIGN INTEGRATION:"
    echo "  - Default provider: ollama_local"
    echo "  - Fallback provider: opencodezen"
    echo "  - Privacy-aware routing"
    echo "  - Cost optimization"
    echo "==============================================================================="
}

main "$@"