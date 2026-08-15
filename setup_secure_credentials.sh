#!/usr/bin/env bash
#===============================================================================
# SECURE CREDENTIAL MANAGEMENT SETUP
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Securely manage credentials for the Neuro-Sovereign Enterprise
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

# Generate secure random key
generate_key() {
    local length=${1:-32}
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Setup environment file
setup_env_file() {
    info "Setting up secure environment file..."
    
    if [ -f ".env" ]; then
        warn ".env file already exists. Creating backup..."
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    fi
    
    cp .env.template .env
    
    # Generate secure keys
    info "Generating secure cryptographic keys..."
    
    local jwt_secret=$(generate_key 32)
    local encryption_key=$(generate_key 32)
    local api_gateway_secret=$(generate_key 24)
    local db_encryption_key=$(generate_key 32)
    
    # Update .env with generated keys
    sed -i "s/your-jwt-secret-min-32-characters/$jwt_secret/" .env
    sed -i "s/your-256-bit-master-key/$encryption_key/" .env
    sed -i "s/your-api-gateway-secret/$api_gateway_secret/" .env
    sed -i "s/your-256-bit-encryption-key/$db_encryption_key/" .env
    
    success "Secure keys generated and .env file created"
    warn "Please fill in the remaining values in .env file manually"
}

# Setup HashiCorp Vault integration (optional)
setup_vault() {
    info "Setting up HashiCorp Vault integration..."
    
    if command -v vault &> /dev/null; then
        info "Vault already installed"
    else
        warn "Vault not found. Install with: sudo apt-get install vault"
        return
    fi
    
    # Enable kv secrets engine
    vault secrets enable -path=neuro-sovereign kv || true
    
    # Store initial secrets
    vault kv put neuro-sovereign/ai-core api_key="placeholder" secret="placeholder"
    vault kv put neuro-sovereign/database connection_string="placeholder"
    
    success "Vault integration setup complete"
}

# Setup Google Cloud credentials securely
setup_gcp_credentials() {
    info "Setting up Google Cloud credentials..."
    
    local credentials_dir="${1:-$HOME/.config/gcloud/credentials}"
    mkdir -p "$credentials_dir"
    
    info "Please download your Google Service Account JSON key"
    info "Save it to: $credentials_dir/neuro-sovereign-service-account.json"
    info "Then update GOOGLE_APPLICATION_CREDENTIALS in .env"
    
    success "GCP credentials setup instructions provided"
}

# Verify setup
verify_setup() {
    info "Verifying secure credential setup..."
    
    if [ ! -f ".env" ]; then
        error ".env file not found. Run setup first."
    fi
    
    # Check for placeholder values
    local placeholders=$(grep -c "your-" .env || true)
    if [ "$placeholders" -gt 0 ]; then
        warn "Found $placeholders placeholder values in .env file"
        warn "Please replace them with actual values"
    else
        success "No placeholder values found in .env file"
    fi
    
    # Check file permissions
    chmod 600 .env
    success "Set .env file permissions to 600"
}

main() {
    echo "==============================================================================="
    echo "  NEURO-SOVEREIGN SECURE CREDENTIAL MANAGEMENT"
    echo "==============================================================================="
    
    setup_env_file
    setup_vault
    setup_gcp_credentials
    verify_setup
    
    echo ""
    success "Secure credential setup complete!"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Edit .env file and fill in remaining values"
    echo "2. Never commit .env file to version control"
    echo "3. Use hardware security modules for production"
    echo "4. Rotate credentials regularly"
    echo "==============================================================================="
}

main "$@"