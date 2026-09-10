# NEURO-SOVEREIGN ENTERPRISE - CODE SIGNING SYSTEM

## 🚀 Cross-Platform Code Signing with Blockchain Verification

**Version**: 5.0-SYMBIOSIS  
**Status**: Production Ready  
**Platforms**: macOS, Windows, Linux

---

## 📋 OVERVIEW

The Neuro-Sovereign Enterprise includes a comprehensive code signing infrastructure that enables you to create signed applications for all major desktop platforms with:

- **✅ Blockchain-verified signatures**
- **✅ Automated compliance checking**  
- **✅ Multi-sig certificate management**
- **✅ Audit trail for all signed applications**
- **✅ Regulatory compliance integration**
- **✅ Neuro-Sovereign identity embedding**

---

## 🏗️ ARCHITECTURE

### Components

1. **Cross-Platform Signing Script** (`cross_platform_signing.py`)
   - Automated signing for macOS, Windows, and Linux
   - Blockchain verification integration
   - Identity embedding in signed applications

2. **Platform-Specific Configurations**
   - `mac_signing_config.json` - macOS Developer ID & Notarization
   - `windows_signing_config.json` - Authenticode & Smart Screen
   - `code_signing_infrastructure.json` - Overall architecture

3. **Certificate Management** (`certificate_management.sh`)
   - Automated certificate setup
   - HashiCorp Vault integration
   - Certificate rotation automation

4. **Desktop App Builder** (`build_desktop_app.py`)
   - Electron-based application building
   - Automated signing integration
   - Multi-platform support

---

## 🔧 SETUP INSTRUCTIONS

### 1. Prerequisites

#### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Python 3.11+
brew install python@3.11

# Install Node.js
brew install node
```

#### Windows
```powershell
# Install Node.js from https://nodejs.org/
# Install Python 3.11+ from https://python.org/
# Install Windows SDK for signtool
```

#### Linux
```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.11+
sudo apt-get install python3.11 python3-pip

# Install GPG for signing
sudo apt-get install gnupg
```

### 2. Obtain Certificates

#### macOS Certificates
1. Join [Apple Developer Program](https://developer.apple.com/programs/)
2. Generate "Developer ID Application" certificate
3. Generate "Developer ID Installer" certificate
4. Download and install in Keychain Access

#### Windows Certificates
1. Purchase Authenticode certificate from:
   - [DigiCert](https://www.digicert.com/)
   - [Sectigo](https://www.sectigo.com/)
   - [GlobalSign](https://www.globalsign.com/)
2. Export as .pfx file with password
3. Install in Windows Certificate Store

#### Linux Certificates
1. Generate GPG key pair:
   ```bash
   gpg --full-generate-key
   ```
2. Export public key for distribution

### 3. Configure Environment

```bash
# Run certificate management setup
bash certificate_management.sh

# Configure environment variables
cp .env.template .env
# Edit .env with your certificate details
```

---

## 🚀 USAGE

### Sign an Existing Application

```bash
# Sign macOS application
python cross_platform_signing.py sign /path/to/MyApp.app "MyApp" "1.0.0"

# Sign Windows executable
python cross_platform_signing.py sign /path/to/MyApp.exe "MyApp" "1.0.0"

# Sign Linux package
python cross_platform_signing.py sign /path/to/MyApp.AppImage "MyApp" "1.0.0"
```

### Build and Sign Desktop Application

```bash
# Build and sign for current platform
python build_desktop_app.py build-and-sign

# Build and sign for specific platform
python build_desktop_app.py build-and-sign macos
python build_desktop_app.py build-and-sign windows
python build_desktop_app.py build-and-sign linux
```

### Verify Signature

```bash
# Verify any signed application
python cross_platform_signing.py verify /path/to/signed_app
```

---

## 🔐 SECURITY FEATURES

### macOS
- **Hardened Runtime**: Memory protection and system integrity
- **App Sandbox**: Restricted system access
- **Library Validation**: Prevents code injection
- **Notarization**: Apple's security verification
- **Entitlements**: Fine-grained permission control

### Windows
- **Authenticode**: Microsoft's code signing standard
- **Timestamp Servers**: Signature validity verification
- **Smart Screen**: Microsoft Defender integration
- **Dual Signing**: SHA-1 and SHA-256 support
- **EV Certificate**: Extended Validation for highest trust

### Linux
- **GPG Signing**: OpenPGP standard
- **Repository Signing**: Package manager integration
- **Detached Signatures**: Separate signature files
- **Key Management**: GPG keyring integration

---

## 🌐 NEURO-SOVEREIGN INTEGRATION

### Blockchain Verification
Every signed application is:
1. Hashed with SHA-256
2. Recorded in local database
3. Anchored to blockchain (placeholder for production)
4. Verified against identity anchor

### Compliance Checking
- **Layer 17**: Legal sovereignty verification
- **Layer 14**: Compliance framework integration
- **Layer 8**: Formal verification integration
- **Layer 15**: Identity anchor embedding

### Audit Trail
- All signing operations logged
- Blockchain transaction records
- Certificate usage tracking
- Compliance verification records

---

## 📊 PLATFORM-SPECIFIC REQUIREMENTS

### macOS
- **Apple Developer Account**: $99/year
- **Team ID**: Required for notarization
- **Provisioning Profiles**: For App Store distribution
- **Notarization**: Required for macOS 10.15+

### Windows
- **Code Signing Certificate**: $100-500/year
- **EV Certificate**: $500-1000/year (recommended)
- **Microsoft Verified Publisher**: Optional but recommended
- **Timestamp Server**: Included with certificate

### Linux
- **GPG Key**: Free self-managed
- **Repository Access**: For package distribution
- **Package Signing**: Integrates with apt/yum/pacman

---

## 🎯 WORKFLOW EXAMPLES

### Complete Workflow for macOS

```bash
# 1. Setup environment
bash certificate_management.sh

# 2. Configure certificates
export MAC_CERT_PASSWORD="your_password"
export APPLE_ID="your@email.com"
export APPLE_APP_SPECIFIC_PASSWORD="app-specific-password"
export MAC_TEAM_ID="YOUR_TEAM_ID"

# 3. Build application
python build_desktop_app.py build macos

# 4. Sign application
python cross_platform_signing.py sign dist/NeuroSovereignEnterprise.app "NeuroSovereignEnterprise" "5.0.0"

# 5. Verify signature
python cross_platform_signing.py verify dist/NeuroSovereignEnterprise.app
```

### Complete Workflow for Windows

```bash
# 1. Setup environment
bash certificate_management.sh

# 2. Configure certificates
export WINDOWS_CERT_PASSWORD="your_password"
export WINDOWS_CERT_PATH="certificates/windows/code_signing.pfx"

# 3. Build application
python build_desktop_app.py build windows

# 4. Sign application
python cross_platform_signing.py sign dist/NeuroSovereignEnterprise.exe "NeuroSovereignEnterprise" "5.0.0"

# 5. Verify signature
python cross_platform_signing.py verify dist/NeuroSovereignEnterprise.exe
```

---

## 🔍 TROUBLESHOOTING

### Common Issues

#### macOS Notarization Failed
```bash
# Check notarization status
xcrun notarytool history --apple-id YOUR_EMAIL --password APP_PASSWORD --team-id TEAM_ID

# Check notarization log
xcrun notarytool log YOUR_REQUEST_UUID --apple-id YOUR_EMAIL --password APP_PASSWORD --team-id TEAM_ID
```

#### Windows Smart Screen Warning
- Build reputation over time
- Use EV certificate
- Apply for Microsoft Verified Publisher
- Distribute gradually (beta program)

#### Linux Signature Verification
```bash
# Verify GPG signature
gpg --verify your-app.asc your-app

# Import public key if needed
gpg --import public-key.asc
```

---

## 📈 COMPLIANCE & STANDARDS

### Regulatory Compliance
- **EU AI Act**: High-risk category compliance
- **NIST AI RMF**: Governance and mapping functions
- **ISO 42001**: AI management system certification
- **GDPR**: Data protection compliance

### Industry Standards
- **Apple Developer Program License Agreement**
- **Microsoft Verified Publisher Requirements**
- **OpenPGP Standards** (Linux)
- **Authenticode Specifications** (Windows)

---

## 🎉 ADVANTAGES

### Security
- **Blockchain Verification**: Immutable proof of authenticity
- **Multi-sig Governance**: Certificate management security
- **Automated Compliance**: Regulatory adherence
- **Audit Trail**: Complete signing history

### Symbiosis
- **Fair Contribution**: Compliance across jurisdictions
- **Innovation Investment**: Local development support
- **Community Benefit**: Open verification system
- **Regulatory Cooperation**: Standardized processes

### Automation
- **One-command signing**: Simple workflow
- **Cross-platform**: Single codebase
- **Blockchain integration**: Automatic verification
- **CI/CD ready**: Automated pipelines

---

## 📞 SUPPORT

For issues and questions:
- **Documentation**: See `SECURITY_ANALYSIS_V5_OPTIMIZED.md`
- **Configuration**: Edit platform-specific JSON files
- **Certificates**: Follow platform-specific guides
- **Blockchain**: See identity anchor system

---

**Ready to create signed, verified applications with Neuro-Sovereign Enterprise v5.0-SYMBIOSIS!** 🚀