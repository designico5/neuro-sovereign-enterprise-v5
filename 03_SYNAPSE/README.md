# ◬ NEXUS TORUS: 03_SYNAPSE — NSE-v5

Autokatalytisches Netzwerk: Layer-Konfigurationen + AI-Anbindungs-Präparate.

## Prinzip
Die Synapse verbindet den invarianten Kernel (01_CORE) mit der Außenwelt.
Hier liegen die thematischen Layer-Config-Dateien und die AI-Provider-Präparate.

## Enthaltene Komponenten
- `config/` — thematische Layer-Config-Dateien (ehem. `layers/`)
  - `11_dao/governance_tokenomics.json`
  - `14_governance/compliance_framework.yaml`
  - `15_ethos/identity_anchor.md` + `identity_anchor_dynamic.py`
  - `16_geo/routing_policy.json`
  - `17_legal/charter_smart_contract.sol`
  - `6_cognitive/` — Voice-Interface (ASR/TTS/Orchestrator/Audio/Tools)
- `ai_providers_config.json` — AI-Provider-Routing
- `ai_provider_manager.py` — Provider-Manager (Ollama/OpenAI/OpenCodeZen)
- `AI_PROVIDERS_README.md` — Dokumentation

## Warum "Synapse" statt "layers"
Der alte Name `layers/` kollidierte mit `neurosovereign/layers/` (Python-Package).
`03_SYNAPSE/config/` macht die Trennung klar:
- `01_CORE/neurosovereign/layers/` = **Code** (invariant)
- `03_SYNAPSE/config/` = **Konfiguration** (editierbar)
