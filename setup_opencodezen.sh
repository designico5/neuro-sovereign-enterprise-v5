#!/usr/bin/env bash
#===============================================================================
# OPENCODEZ SETUP
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Configure OpenCodezen as cloud AI provider
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

# Configure OpenCodezen API key
configure_opencodezen() {
    info "Configuring OpenCodezen integration..."
    
    if [ -f ".env" ]; then
        if ! grep -q "OPENCODEZEN_API_KEY" .env; then
            echo "OPENCODEZEN_API_KEY=your_opencodezen_api_key_here" >> .env
            success "Added OPENCODEZEN_API_KEY to .env"
        else
            info "OPENCODEZEN_API_KEY already configured in .env"
        fi
    else
        echo "OPENCODEZEN_API_KEY=your_opencodezen_api_key_here" > .env
        success "Created .env with OPENCODEZEN_API_KEY configuration"
    fi
}

# Test OpenCodezen connection
test_opencodezen() {
    info "Testing OpenCodezen connection..."
    
    # Check if API key is configured
    if [ -z "${OPENCODEZEN_API_KEY:-}" ]; then
        warn "OPENCODEZEN_API_KEY not set. Please configure it in .env"
        return
    fi
    
    # Test API connection
    if command -v curl &> /dev/null; then
        response=$(curl -s -w "\n%{http_code}" \
            -H "Authorization: Bearer $OPENCODEZEN_API_KEY" \
            "https://api.opencodezen.com/v1/models" 2>/dev/null)
        
        http_code=$(echo "$response" | tail -n1)
        
        if [ "$http_code" = "200" ]; then
            success "OpenCodezen API connection successful"
        else
            warn "OpenCodezen API connection failed (HTTP $http_code)"
        fi
    else
        warn "curl not available, skipping connection test"
    fi
}

# Get OpenCodezen information
get_opencodezen_info() {
    info "OpenCodezen Information:"
    echo ""
    echo "API Endpoint: https://api.opencodezen.com/v1"
    echo "Available Models:"
    echo "  - opencodezen-7b (Fast, efficient)"
    echo "  - opencodezen-13b (Balanced)"
    echo "  - opencodezen-34b (Powerful)"
    echo "  - opencodezen-70b (Maximum performance)"
    echo ""
    echo "Features:"
    echo "  - Streaming responses"
    echo "  - Function calling"
    echo "  - Code generation"
    echo "  - 128K context window"
    echo ""
    echo "Pricing:"
    echo "  - Competitive rates"
    echo "  - Pay-per-token model"
    echo "  - High cost-efficiency"
}

# Setup OpenCodezen account
setup_account() {
    info "OpenCodezen Account Setup:"
    echo ""
    echo "1. Visit: https://opencodezen.com"
    echo "2. Sign up for an account"
    echo "3. Generate API key in dashboard"
    echo "4. Add API key to .env file:"
    echo "   OPENCODEZEN_API_KEY=your_actual_api_key"
    echo ""
    echo "Current configuration in .env:"
    if [ -f ".env" ]; then
        grep "OPENCODEZEN" .env || echo "  OPENCODEZEN_API_KEY=your_opencodezen_api_key_here"
    fi
}

main() {
    echo "==============================================================================="
    echo "  OPENCODEZ SETUP FOR NEURO-SOVEREIGN ENTERPRISE"
    echo "==============================================================================="
    
    configure_opencodezen
    test_opencodezen
    get_opencodezen_info
    setup_account
    
    echo ""
    success "OpenCodezen setup completed!"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Sign up at https://opencodezen.com"
    echo "2. Generate API key"
    echo "3. Update OPENCODEZEN_API_KEY in .env"
    echo "4. Test with: python ai_provider_manager.py"
    echo ""
    echo "NEURO-SOVEREIGN INTEGRATION:"
    echo "  - Fallback provider (when Ollama unavailable)"
    echo "  - High-complexity tasks"
    echo "  - Online-only operations"
    echo "  - Cost tracking and optimization"
    echo "==============================================================================="
}

main "$@"