#!/usr/bin/env bash
#===============================================================================
# OPENAI SETUP
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Configure OpenAI as enterprise AI provider
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

# Configure OpenAI API key
configure_openai() {
    info "Configuring OpenAI integration..."
    
    if [ -f ".env" ]; then
        if ! grep -q "OPENAI_API_KEY" .env; then
            echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
            success "Added OPENAI_API_KEY to .env"
        else
            info "OPENAI_API_KEY already configured in .env"
        fi
    else
        echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
        success "Created .env with OPENAI_API_KEY configuration"
    fi
}

# Test OpenAI connection
test_openai() {
    info "Testing OpenAI connection..."
    
    # Check if API key is configured
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        warn "OPENAI_API_KEY not set. Please configure it in .env"
        return
    fi
    
    # Test API connection
    if command -v curl &> /dev/null; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $OPENAI_API_KEY" \
            "https://api.openai.com/v1/models" 2>/dev/null)
        
        http_code=$(echo "$response" | tail -n1)
        
        if [ "$http_code" = "200" ]; then
            success "OpenAI API connection successful"
        else
            warn "OpenAI API connection failed (HTTP $http_code)"
        fi
    else
        warn "curl not available, skipping connection test"
    fi
}

# Get OpenAI information
get_openai_info() {
    info "OpenAI Information:"
    echo ""
    echo "API Endpoint: https://api.openai.com/v1"
    echo "Available Models:"
    echo "  - gpt-4o (Latest, multimodal, 128K context)"
    echo "  - gpt-4o-mini (Fast, cost-effective)"
    echo "  - gpt-4-turbo (High performance)"
    echo "  - gpt-3.5-turbo (Fast, efficient)"
    echo "  - o1-preview (Advanced reasoning)"
    echo "  - o1-mini (Compact reasoning)"
    echo ""
    echo "Features:"
    echo "  - Streaming responses"
    echo "  - Function calling"
    echo "  - Vision capabilities"
    echo "  - Code generation"
    echo "  - Multimodal (text + images)"
    echo "  - JSON mode"
    echo "  - 128K context window"
    echo ""
    echo "Pricing:"
    echo "  - Pay-per-token model"
    echo "  - Enterprise tier available"
    echo "  - Usage-based billing"
}

# Setup OpenAI account
setup_account() {
    info "OpenAI Account Setup:"
    echo ""
    echo "1. Visit: https://platform.openai.com"
    echo "2. Sign up for an account"
    echo "3. Create API key in dashboard"
    echo "4. Add API key to .env file:"
    echo "   OPENAI_API_KEY=your_actual_api_key"
    echo ""
    echo "Current configuration in .env:"
    if [ -f ".env" ]; then
        grep "OPENAI" .env || echo "  OPENAI_API_KEY=your_openai_api_key_here"
    fi
}

# Install OpenAI Python SDK
install_sdk() {
    info "Installing OpenAI Python SDK..."
    
    if command -v pip &> /dev/null; then
        pip install openai || warn "Failed to install OpenAI SDK"
        success "OpenAI SDK installed"
    elif command -v pip3 &> /dev/null; then
        pip3 install openai || warn "Failed to install OpenAI SDK"
        success "OpenAI SDK installed"
    else
        warn "pip not available, SDK installation skipped"
    fi
}

# Test OpenAI with Python
test_python_integration() {
    info "Testing OpenAI Python integration..."
    
    if python3 -c "import openai" 2>/dev/null; then
        success "OpenAI Python SDK available"
    else
        warn "OpenAI Python SDK not installed or not accessible"
    fi
}

main() {
    echo "==============================================================================="
    echo "  OPENAI SETUP FOR NEURO-SOVEREIGN ENTERPRISE"
    echo "==============================================================================="
    
    configure_openai
    test_openai
    get_openai_info
    setup_account
    install_sdk
    test_python_integration
    
    echo ""
    success "OpenAI setup completed!"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Sign up at https://platform.openai.com"
    echo "2. Create API key in dashboard"
    echo "3. Update OPENAI_API_KEY in .env"
    echo "4. Test with: python ai_provider_manager.py"
    echo ""
    echo "NEURO-SOVEREIGN INTEGRATION:"
    echo "  - Enterprise provider for production"
    echo "  - High-complexity tasks"
    echo "  - Vision and multimodal capabilities"
    echo "  - Advanced reasoning (o1 models)"
    echo "  - Cost tracking and optimization"
    echo "  - Compliance layer integration"
    echo "==============================================================================="
}

main "$@"