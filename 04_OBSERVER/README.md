# ◉ NEXUS TORUS: 04_OBSERVER — NSE-v5

Meta-Ebene: CI/CD + Security-Analyse + Code-Signing + Runtime-State.

## Prinzip
Der Observer macht Emergenz messbar. Er beobachtet die anderen Schichten,
misst Compliance und sichert Integrität — ohne sie zu beeinflussen.

## Enthaltene Komponenten
- `.github/` — CI/CD-Pipeline (GitHub Actions)
- `security/` — Security-Analysen + Supply-Chain-Scans
  - `SECURITY_ANALYSIS.md`
  - `SECURITY_ANALYSIS_V5_OPTIMIZED.md`
  - `supply_chain_security.json` + `.sh`
- `signing/` — Code-Signing (Windows/macOS/Linux)
  - `cross_platform_signing.py`
  - `code_signing_infrastructure.json`
  - `windows_signing_config.json`
  - `mac_signing_config.json`
  - `CODE_SIGNING_README.md`
  - `certificate_management.sh`
- `state/` — Runtime-State (ledger, sbom, wallets, backups)

## Beobachtete Metriken
- Compliance-Score-Ziel: 0.95 (EU_AI_ACT, NIST_AI_RMF, ISO_42001)
- Supply-Chain-Integrität (SBOM-Generation)
- Code-Signing-Ketten (Ed25519)
