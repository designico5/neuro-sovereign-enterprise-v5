#!/usr/bin/env bash
#===============================================================================
# CERTIFICATE MANAGEMENT SYSTEM
# VERSION: 5.0-SYMBIOSIS
# PURPOSE: Manage code signing certificates with Neuro-Sovereign integration
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

# Setup certificate directories
setup_cert_directories() {
    info "Setting up certificate directories..."
    
    mkdir -p certificates/macos
    mkdir -p certificates/windows
    mkdir -p certificates/linux
    mkdir -p provisioning/profiles
    mkdir -p state/ledger/certificates
    
    success "Certificate directories created"
}

# Generate self-signed certificate for testing
generate_test_certificate() {
    local platform="$1"
    local cert_name="$2"
    
    info "Generating test certificate for $platform..."
    
    case "$platform" in
        "windows")
            openssl req -x509 -newkey rsa:4096 -keyout "certificates/windows/$cert_name.key" \
                -out "certificates/windows/$cert_name.crt" -days 365 -nodes \
                -subj "/CN=NeuroSovereign Test/O=NeuroSovereign/C=US"
            
            # Convert to PFX format
            openssl pkcs12 -export -out "certificates/windows/$cert_name.pfx" \
                -inkey "certificates/windows/$cert_name.key" \
                -in "certificates/windows/$cert_name.crt" \
                -passout pass:test_password
            
            success "Test Windows certificate generated"
            ;;
        "linux")
            openssl req -x509 -newkey rsa:4096 -keyout "certificates/linux/$cert_name.key" \
                -out "certificates/linux/$cert_name.crt" -days 365 -nodes \
                -subj "/CN=NeuroSovereign Test/O=NeuroSovereign/C=US"
            
            success "Test Linux certificate generated"
            ;;
        *)
            warn "Test certificate generation not supported for $platform"
            ;;
    esac
}

# Import certificate to system
import_certificate() {
    local platform="$1"
    local cert_path="$2"
    
    info "Importing certificate for $platform..."
    
    case "$platform" in
        "macos")
            if [[ "$OSTYPE" == "darwin"* ]]; then
                security import "$cert_path" -k ~/Library/Keychains/login.keychain \
                    -T /usr/bin/codesign -T /usr/bin/productsign
                success "macOS certificate imported to keychain"
            else
                warn "Not on macOS, skipping keychain import"
            fi
            ;;
        "windows")
            if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
                certutil -import "$cert_path"
                success "Windows certificate imported to certificate store"
            else
                warn "Not on Windows, skipping certificate store import"
            fi
            ;;
        "linux")
            # Linux GPG key import
            gpg --import "$cert_path"
            success "Linux certificate imported to GPG keyring"
            ;;
    esac
}

# Setup HashiCorp Vault for certificate storage
setup_vault_certificates() {
    info "Setting up HashiCorp Vault for certificate storage..."
    
    if command -v vault &> /dev/null; then
        # Enable secrets engine
        vault secrets enable -path=certificates kv || true
        
        # Store certificate metadata
        vault kv put certificates/macos \
            certificate_path="certificates/macos/developer_id_application.p12" \
            team_id="YOUR_TEAM_ID" \
            expiry_date="2027-08-15"
        
        vault kv put certificates/windows \
            certificate_path="certificates/windows/code_signing.pfx" \
            subject="CN=NeuroSovereign" \
            expiry_date="2027-08-15"
        
        success "Vault certificate storage configured"
    else
        warn "Vault not found. Certificate storage will be file-based"
    fi
}

# Certificate rotation
rotate_certificate() {
    local platform="$1"
    local cert_name="$2"
    
    info "Rotating certificate for $platform..."
    
    # Backup old certificate
    local backup_dir="certificates/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    if [ -f "certificates/$platform/$cert_name" ]; then
        cp "certificates/$platform/$cert_name" "$backup_dir/"
        success "Old certificate backed up to $backup_dir"
    fi
    
    # Generate new certificate (placeholder for actual rotation logic)
    warn "Certificate rotation logic needs to be implemented for production"
    warn "For now, manual certificate renewal required"
}

# Verify certificate validity
verify_certificate() {
    local cert_path="$1"
    
    info "Verifying certificate: $cert_path"
    
    if [ ! -f "$cert_path" ]; then
        error "Certificate file not found: $cert_path"
    fi
    
    # Check certificate expiry
    local expiry_date
    if command -v openssl &> /dev/null; then
        expiry_date=$(openssl x509 -enddate -noout -in "$cert_path" | cut -d= -f2)
        success "Certificate valid until: $expiry_date"
    else
        warn "OpenSSL not found, cannot verify certificate expiry"
    fi
}

# Generate certificate report
generate_certificate_report() {
    info "Generating certificate report..."
    
    local report_file="state/ledger/certificates/certificate_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# CERTIFICATE MANAGEMENT REPORT
**Date**: $(date)
**System**: Neuro-Sovereign Enterprise v5.0-SYMBIOSIS

## Certificate Inventory

### macOS Certificates
- **Developer ID Application**: \$(test -f certificates/macos/developer_id_application.p12 && echo "✅ Present" || echo "❌ Missing")
- **Developer ID Installer**: \$(test -f certificates/macos/developer_id_installer.p12 && echo "✅ Present" || echo "❌ Missing")
- **Team ID**: \${MAC_TEAM_ID:-Not configured}

### Windows Certificates
- **Code Signing Certificate**: \$(test -f certificates/windows/code_signing.pfx && echo "✅ Present" || echo "❌ Missing")
- **Timestamp Server**: Configured (DigiCert, Sectigo, GlobalSign)

### Linux Certificates
- **GPG Signing Key**: \$(test -f certificates/linux/signing_key.asc && echo "✅ Present" || echo "❌ Missing")
- **Key ID**: \${LINUX_SIGNING_KEY_ID:-Not configured}

## Security Status
- **Certificate Storage**: \$(command -v vault &> /dev/null && echo "HashiCorp Vault" || echo "File-based")
- **Rotation Policy**: 90 days
- **Backup Required**: Yes
- **HSM Integration**: Optional

## Recommendations
1. Store production certificates in HashiCorp Vault
2. Implement automated certificate rotation
3. Use Hardware Security Modules for critical certificates
4. Enable certificate revocation checking
5. Monitor certificate expiry dates

---
*Report generated by Neuro-Sovereign Certificate Management*
EOF
    
    success "Certificate report generated: $report_file"
}

main() {
    echo "==============================================================================="
    echo "  NEURO-SOVEREIGN CERTIFICATE MANAGEMENT"
    echo "==============================================================================="
    
    setup_cert_directories
    setup_vault_certificates
    
    # Generate test certificates for development
    generate_test_certificate "windows" "neuro_sovereign_test"
    generate_test_certificate "linux" "neuro_sovereign_test"
    
    generate_certificate_report
    
    echo ""
    success "Certificate management setup completed!"
    echo ""
    echo "NEXT STEPS:"
    echo "1. Obtain production certificates from certificate authorities"
    echo "2. Configure certificate paths in .env file"
    echo "3. Import certificates to respective platforms"
    echo "4. Set up automated certificate rotation"
    echo "5. Configure HashiCorp Vault for production use"
    echo ""
    echo "CERTIFICATE AUTHORITIES:"
    echo "- macOS: Apple Developer Program"
    echo "- Windows: DigiCert, Sectigo, GlobalSign"
    echo "- Linux: Self-managed GPG keys"
    echo "==============================================================================="
}

main "$@"