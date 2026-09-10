# refactor: Molekulare Großüberholung — Nexus / Park / Aorta + OSINT-Docking

Branch: `molecule-overhaul` → `main` · Commit `672d009`
Basis: `designico5/neuro-sovereign-enterprise-v5`
Scope: 42 Dateien, +743 / −60 · 22 Import-Fixes · 3 neue Doku-Dateien

## TL;DR

Die „17 flachen Ebenen" sind funktional nur **5 Organellen + 1 Skelett**.
Diese PR führt die räumliche Architektur grundlegend auf ein einheitliches
**Nexus / Park / Aorta** Modell zurück und verdichtet sie auf eine konsistente
Essenz, ohne das Verhalten der Moleküle zu ändern (nur Defects + Konsistenz).

> Ein einziger Nexus pulsiert (L10), lässt jeden Arbeitsgang über eine Aorta
> fließen (L5→L6→L8→L7), zeichnet ihn im Park ab (PVC state + OSINT-Connectors)
> und versiegelt ihn an der Außengrenze (L15 signiert · L14 prüft · L16 routet ·
> L17 gegenzeichnet) — der Körper (L1–L3) liefert Substrat, das Gehirn (L9)
> liefert Sinne, die Commons halten alles in einem Zustand.

## Räumliche Neuausschnitt (Raummodell)

- **🫀 Nexus** = `NSEPlatform` + `BaseNSELayer` + CLI: einziger Bindungs- &
  Zustandsknoten. Kein Molekül spricht mehr direkt mit einem anderen (C3).
- **🌳 Park** = `/app/state` (9× SQLite): ein Zustand-Ort, jetzt **PVC** (C1).
  Statische `assets/` werden als einmalige Seed-Migration verstanden.
- **🩸 Aorta** = horizontale Flow-Linie `L5→L10→L6→L8→L7→L17→L15`, jetzt mit
  **FQDN-Egress-Whitelist** statt `0.0.0.0/0` (C4).

## Die 6 Pruning-Änderungen

| ID | Fix | Dateien |
|---|---|---|
| **C1** | K8s `emptyDir` → **PVC `nse-state`** (5Gi RWX) — Park persistiert über Neustarts | `k8s/nse-deployment.yaml` |
| **C2** | Zwei `layers/`-Bäume auflösen: root → `assets/` (Voice/UI), `neurosovereign/layers/` → `molecules/` (17 Moleküle) + 22 Import-Fixes | Renames + `__init__`/`cli` |
| **C3** | **Nexus-Isolation**: CLI nutzt `L15.get_anchor()` / `L17.admin_addresses()` statt privaten `_conn`/`admins` | `cli.py`, `layer_15`, `layer_17` |
| **C4** | **Aorta-Egress** `0.0.0.0/0:443` → Calico-FQDN-Whitelist + RFC1918-Safety-Net | `k8s/nse-aorta-egress.yaml` (neu), `nse-networkpolicy.yaml` |
| **C5** | Defects beseitigen: L13 tote `z` · L2 Jetson env + Warnung · L5 `raise RuntimeError` statt `simulated`-Masking · L1 `NSE_ENERGY_*` env · L11 `NSE_DAO_SEED_VOTERS` · L16 `NSE_GEO_*` env | `molecules/layer_1,2,5,11,13,16` |
| **C6** | 3× leere Docking-Verzeichnisse → **uniforme Stubs** (`AVAILABLE=False` + `dock()→NotImplementedError`) + `DOCKING.md` | `verus/`, `science-codeevolve/`, `self_improving_coding_agent/` |

## OSINT-Verbindung (out-of-process, lizenzsauber)

- `osint/__init__.py` — Registry mit **6 Docks**, deren Stars am 2026-09-10
  über die GitHub API live verifiziert wurden: OpenCTI (9.9k★), MISP (6.5k★),
  IntelOwl (4.7k★), SpiderFoot, verus (3k★), OpenHands (87k★).
- `osint/connectors.py` — **L4/L5-Bridge** (`bind_opencti/misp/spiderfoot/
  intelowl`): hält AGPL/GPL-Tooling **out-of-process** (Aorta-Egress), der
  Core bleibt lizenzsauber.
- OSINT-FQDNs in die `nse-aorta-egress.yaml`-Whitelist eingetragen.

## Doku

- **`ARCHITECTURE.md`** — verdichteter Molekül-Atlas (5 Organellen + Skelett,
  Nexus/Park/Aorta-Raummodell, Pruning-Liste, offene Punkte).
- **`DOCKING.md`** — C6-Vertrag (uniforme Docking-Stubs + Hyphen-Ausnahme).
- **`OSINT.md`** — Bindematrix + Lizenz-Kopplungsrisiko.

## Verifikation (statisch, ohne CI)

- `py_compile` alle Python-Dateien → 37/37 OK
- `import neurosovereign; NSEPlatform(cfg)` → PASS (17 `enable_layer_*` Flags)
- `yaml.safe_load_all` alle `k8s/*.yaml` → OK
- 0× `.layers.`-Importe · 0× `emptyDir` · 0× `simulated` in L5 · 0 leere Docking-Dirs

## Offene Punkte (Folge-PR / Cluster-Op)

1. PVC-StorageClass (RWX) im K8s-Cluster konfigurieren
2. Calico CNI aktivieren → FQDN-`host`-Einträge wirksam
3. L16: `NSE_GEO_PROVIDER` an echte Geo-DB (MaxMind/IP2Location) koppeln
4. L1: `sample_once` → echte pynvml-Telemetrie (HW-abhängig)
5. OSINT-Connector: L5 `dispatch_osint_lookup()` verdrahten

## Companion-Artefakt

Full-Stack-3D-Visualisierung dieser Architektur: `nse-v5-visual` (React 19 +
Three.js R3F + Tailwind v4 + Express), live unter `http://localhost:4173`.
Verdichtet als `nse-v5-visual.zip`.
