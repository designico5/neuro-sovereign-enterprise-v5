# NEXUS TORUS: NSE-v5 RAUMSTRUKTUR
# Stand: 2026-09-10 · Methodik: 369/Spark² · Invariante: no_delete_or_overwrite
# Status: KOLLAS-FAZIT (Phase 9 NEXUS PRIME abgeschlossen)

> Diese Datei ist das Orchester der 5-Schicht-Raumstruktur.
> Phase 9 (Kollaps) ist ausgeführt: alle Legacy-Root-Pfade sind konsolidiert,
> die no-delete-Invariante bleibt intakt (git-Renames, keine Löschungen).

## KOLLAPS-FAZIT (was passiert ist)

| Schritt | Commit | Ergebnis |
|---|---|---|
| 5-Schicht-Struktur (copy-only) | `bd0d2b2` | 37 Mappings, 12 Root-Originale erhalten, INTEGRITY PASS |
| Root-JSON-Fix (electron-builder) | `34a9083` | kaputte Klammer im `package.json` repariert (Build-Blocker) |
| Kollaps-Konsolidierung | `b0fd901` | 30 Legacy-Root-Pfade → `99_ARCHIVE/pre_migration/` (69 Dateien, **100 % git-Renames**) |
| relative Assets + HOWTO | `59f6836` | `base:"./"` — Dashboard portable, `file://`-Leerscreen-Fix |
| gitignore + Verifikationstool | `8201062` | Scratch ignoriert, `_nexus_verify_collapse.py` beibehalten |

**Nach dem Kollaps ist `01_CORE` die *einzige* build-aktive Quelle:**
`pyproject.toml where=["01_CORE"]` ↔ `Dockerfile COPY 01_CORE/neurosovereign` ↔
`ci.yml '01_CORE/neurosovereign/**/*.py'` — alle Verträge aufeinander abgestimmt.

## SCHICHT-MODUL-MAPPING (finaler Zustand)

```
  ⟁ 01_CORE ────────── neurosovereign/ (17-Layer-Python-Package, invarianter Kernel)
      │                (neuro_stack_final.toml — Konsolidierung: nach pre_migration)
      │
  ⟂ 02_MEMBRANE ────── k8s/  terraform/  Dockerfile  docker-compose.yml
      │  (semi-permeable Grenze: IaC + Container)
      │
  ◬ 03_SYNAPSE ─────── config/ (Layer-Config, ehem. layers/)
      │                ai_providers_* (Präparate)
      │  (autokatalytisches Netzwerk)
      │
  ◉ 04_OBSERVER ────── .github/  security/  signing/  state/
      │  (Meta-Ebene: CI/CD + Security + Signing + Runtime-State)
      │
  ⏣ 05_OUTPUT ──────── deployment/  voice/  desktop/  setup/
      │  (manifestierte Realität: alles was ausgegeben wird)
      │
  🕳️ 99_ARCHIVE ────── science-codeevolve/  self_improving_coding_agent/  verus/
                        pre_migration/  (30 Legacy-Root-Pfade, 69 Dateien)
                        _manifest.json · _consolidation_manifest.json
      (Verdauungstrakt: stasiert, nicht gelöscht)
```

## LAYER-17 → SCHICHT-MAPPING

| NSE-Layer | Name | Schicht | Ziel-Pfad |
|-----------|------|---------|-----------|
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

1. **Aufnahme** (02_MEMBRANE → 03_SYNAPSE): IaC-Changes werden als Layer-Config ingested
2. **Verdauung** (01_CORE): `neurosovereign/`-Package lädt die Config, initialisiert 17 Layer
3. **Aktivierung** (04_OBSERVER): CI/CD + Security-Scans beobachten die Layer
4. **Manifestierung** (05_OUTPUT): Deployment- und Voice-Scripts geben die Plattform aus
5. **Archivierung** (99_ARCHIVE): Inaktive Module + alle 30 Legacy-Root-Pfade stasiert

## INARIANTEN (Kollaps-Status)

- `no_delete_or_overwrite_during_migration`:
  **INTAKT** — Konsolidierung läuft über `_nexus_consolidate.py` als *git-Renames*
  (keine Löschungen), alle 69 Dateien in `99_ARCHIVE/pre_migration/` erhalten.
- `unknown_evidence_is_not_success`:
  **Dokumentiert** — `_nexus_spatial_mapping.json` (37 Mappings) +
  `_consolidation_manifest.json` (32 Einträge) + reproducible Verifikation
  `_nexus_verify_collapse.py` (läuft: INTEGRITY PASS).
- Die 17 Layer sind **invariant** (01_CORE) — nur durch die Engine aktualisiert.

## LIVING DASHBOARD (Begleit-Artefakt)

Zwei Generationen liegen in `dashboard/`:

| Version | Pfad | Stack | Öffnen |
|---------|------|-------|--------|
| **Single-File-Fallback** | `dashboard/index.html` | Three.js + statische Panels (CDN-resilient) | `python -m http.server` |
| **Max-Level** | `dashboard/web/` | Vite6 · React 19 · R3F v9 · Drei 10 · Framer 11 · Tailwind 4 · Three r169 | `npm run serve` / `npm run dev` |

3D-Szene: 5-Schicht-Torus + 17-Layer-Golden-Angle-Kern + 520 Metabolismus-Partikel +
Hexad-Ring + 5 Genie-Module + OrbitControls. HUD: Layer-Fokus, 7 Live-Metriken,
369/Spark²-Phase, Genie-Multiplikatoren. ⚠️ Max-Level immer **via HTTP** öffnen
(ES-Module + `file://`-CORS = leere Seite; `base:"./"` macht die Assets portabel).
