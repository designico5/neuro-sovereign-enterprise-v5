# NEXUS TORUS: NSE-v5 RAUMSTRUKTUR
# Stand: 2026-09-10 · Methodik: 369/Spark² · Invariante: no_delete_or_overwrite

> Diese Datei ist das Orchester der neuen Raumstruktur.
> Alle Originalpfade bleiben erhalten (copy-only Invariante).

## SCHICHT-MODUL-MAPPING

```
  ⟁ 01_CORE ────────── neurosovereign/ (Python-Package)
      │                neuro_stack_final.toml
      │  (17 Layer = invarianter Kernel, nicht zu editieren außer durch Engine)
      │
  ⟂ 02_MEMBRANE ────── k8s/  terraform/  Dockerfile  docker-compose.yml
      │  (semi-permeable Grenze: IaC + Container)
      │
  ◬ 03_SYNAPSE ─────── config/ (ehemals layers/)
      │                ai_providers_config.json
      │                ai_provider_manager.py
      │  (autokatalytisches Netzwerk: Layer-Config + AI-Anbindungs-Präparate)
      │
  ◉ 04_OBSERVER ─────── .github/
      │                security/  signing/  state/
      │  (Meta-Ebene: CI/CD + Security-Analyse + Code-Signing + Runtime-State)
      │
  ⏣ 05_OUTPUT ───────── deployment/  voice/  desktop/  setup/
      │  (manifestierte Realität: alles was ausgegeben wird)
      │
  🕳️ 99_ARCHIVE ─────── science-codeevolve/  self_improving_coding_agent/  verus/
                        _manifest.json
      (Verdauungstrakt: stasierte Orphans — nicht gelöscht, nur gelagert)
```

## LAYER-17 → SCHICHT-MAPPING

| NSE-Layer | Name | Neue Schicht | Ziel-Pfad |
|-----------|------|--------------|-----------|
| 1 | Energy Feedback | 01_CORE | `01_CORE/neurosovereign/layers/layer_1_energy.py` |
| 2 | Compute Silicon | 01_CORE | `01_CORE/neurosovereign/layers/layer_2_compute.py` |
| 3 | Infrastructure IaC | 02_MEMBRANE | `02_MEMBRANE/terraform/` + `k8s/` |
| 4 | Data Knowledge | 01_CORE | `01_CORE/neurosovereign/layers/layer_4_data.py` |
| 5 | Integration API | 01_CORE | `01_CORE/neurosovereign/layers/layer_5_integration.py` |
| 6 | Execution Sandbox | 01_CORE | `01_CORE/neurosovereign/layers/layer_6_cognitive.py` |
| 7 | Code Evolution | 01_CORE | `01_CORE/neurosovereign/layers/layer_7_evolution.py` |
| 8 | Verification Proof | 01_CORE | `01_CORE/neurosovereign/layers/layer_8_verification.py` |
| 9 | Cognition | 01_CORE | `01_CORE/neurosovereign/layers/layer_9_cognition.py` |
| 10 | Orchestration Swarm | 01_CORE | `01_CORE/neurosovereign/layers/layer_10_swarm.py` |
| 11 | DAO Governance | 01_CORE + 03_SYNAPSE | `layer_11_dao.py` + `03_SYNAPSE/config/11_dao/` |
| 12 | Vision Goals | 01_CORE | `01_CORE/neurosovereign/layers/layer_12_vision.py` |
| 13 | Strategy Market | 01_CORE | `01_CORE/neurosovereign/layers/layer_13_strategy.py` |
| 14 | Governance Compliance | 01_CORE + 03_SYNAPSE | `layer_14_governance.py` + `03_SYNAPSE/config/14_governance/` |
| 15 | Ethos Identity | 01_CORE + 03_SYNAPSE | `layer_15_ethos.py` + `03_SYNAPSE/config/15_ethos/` |
| 16 | GeoPolitical Router | 01_CORE + 03_SYNAPSE | `layer_16_geo.py` + `03_SYNAPSE/config/16_geo/` |
| 17 | Legal Sovereignty | 01_CORE + 03_SYNAPSE | `layer_17_legal.py` + `03_SYNAPSE/config/17_legal/` |

## METABOLISMUS-KREISLÄUFE

1. **Aufnahme** (02_MEMBRANE → 03_SYNAPSE): IaC-Changes werden als Layer-Config in `03_SYNAPSE/config/` ingested
2. **Verdauung** (01_CORE): `neurosovereign/`-Package lädt die Config und initialisiert alle 17 Layer
3. **Aktivierung** (04_OBSERVER): CI/CD-Pipeline und Security-Scans beobachten die Layer
4. **Manifestierung** (05_OUTPUT): Deployment- und Voice-Scripts geben die Plattform als Artefakt aus
5. **Archivierung** (99_ARCHIVE): Inaktive Module (verus, codeevolve, self_improving_coding_agent) werden stasiert

## INARIANTEN

- `no_delete_or_overwrite_during_migration`: Alle Originalpfade bleiben im Root erhalten
- `unknown_evidence_is_not_success`: Jedes Migration-Event ist im `_nexus_spatial_manifest.json` protokolliert
- Die 17 Layer sind **invariant** (01_CORE) — sie werden nicht manuell editiert, sondern nur durch die Engine aktualisiert
