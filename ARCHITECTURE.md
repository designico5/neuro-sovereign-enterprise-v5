# Neuro-Sovereign Enterprise v5 — Molekül-Atlas & Raumarchitektur

> **Verdichtete Essenz (1 Zeile):**
> Ein einziger **Nexus** pulsiert (L10 Swarm), lässt jeden Arbeitsgang über eine
> **Aorta** fließen (L5→L6→L8→L7), zeichnet ihn im **Park** ab (PVC `state/`), und
> versiegelt ihn, bevor er die Außengrenze passiert (L15 signiert · L14 prüft ·
> L16 routet · L17 gegenzeichnet) — der **Körper** (L1–L3) liefert Energie/Silikon/IaC,
> das **Gehirn** (L9) liefert Sinne, die **Commons** (Park) halten alles in einem Zustand.

---

## 1. Raummodell — Nexus / Park / Aorta

Die 17 "Layern" sind flach nummeriert, **funktional** aber nur **5 Organellen + 1 Skelettmolekül**.
Dieses Dokument ist die autoritative räumliche Lesart des Codes.

| Raum-Element | Rolle | Was wohnt da |
|---|---|---|
| **🫀 Nexus** | Einziges Bindungs- & Zustandsknoten. Template-Method (init→metrics→lifecycle), startet alle 17 in Abhängigkeitsreihenfolge, `health_report()` als einziger globaler Puls. | `NSEPlatform` + `BaseNSELayer` + Typer-CLI |
| **🩸 Aorta** | Eine horizontale Flow-Linie: Mündung (L5) → Queue (L10) → Pumpen-Segment (L6) → Beweis (L8) → Reflex-Lernen (L7) → Zoll (L14/L17) → Signatur (L15) → Aus-Kammer. Egress nur via FQDN-Whitelist. | `k8s/nse-aorta-egress.yaml` + Molekül-Flow |
| **🌳 Park** | Ein einziger Zustand-Ort: alle 9 SQLite-DBs (identity, governance, okr, market, compliance, geo, sovereignty, proofs, knowledge) + Merkle + Swarm-Queue. Lesbar von allen, beschrieben nur via Molekül-API. Persistiert als **PVC** (RWX 5Gi). Statische `assets/*.{json,yaml,sol}` werden **einmalig seediert**, danach existiert nur die DB. | `k8s/nse-deployment.yaml` (`nse-state` PVC) + `state/` |

**Regel (Nexus-Isolation):** Keiner spricht direkt mit einer anderen Molekül; alle melden
sich am **Nexus** (Template-Method + Metrik-Slot). Die CLI und externer Code dürfen nie
`._conn` / fremde SQLite-Handles / private Sets rufen — nur die **public Molekül-API**.

---

## 2. Molekül-Inventar (5 Organellen + Skelett)

### Skelett
- **`NSEPlatform` + `BaseNSELayer` + Typer-CLI** — Nexus-Instanz.

### K1 — Körper / Substrat (L1–L3, am "Perikard")
| Molekül | 1-Zeilen-Essenz |
|---|---|
| **L1** `EnergyFeedbackEngine` | Watt/Cost-Sampling-Loop (30s, pynvml→env-Fallback), Carbon-Ceiling. Konfigurierbar via `NSE_ENERGY_BASE_WATTS` / `MIN_WATTS` / `COST_PER_KWH` / `RENEWABLE_PCT`. |
| **L2** `ComputeSiliconManager` | Heterogen-Device-Discovery (NVIDIA/AMD/Apple/CPU) + 4-Tier-Routepolicy. Edge-Target konfigurierbar via `NSE_EDGE_DEVICE_SUBSTR`, mit `logger.warning` bei Fallback. |
| **L3** `InfrastructureManager` | Terraform/K8s/Docker-Plan/Apply/Rollback + Drift (SHA256-Template). Provider-Erkennung via `which`. |

### K2 — Kognition & Ausführung (L4–L9)
| Molekül | 1-Zeilen-Essenz |
|---|---|
| **L4** `KnowledgeDataLayer` | Vektorstore (Chroma→Hash-Cosine-Fallback) + Netzwerk-Graf (networkx→dict) + SQLite-Chunks/Edges. |
| **L5** `IntegrationAPIGateway` | Typete Connectors (REST/SAP/JDBC/SFTP/Kafka/MQTT/Mainframe) + RateLimit + mTLS + Vault. Fehlende Deps → **`RuntimeError`** (kein stilles Simulieren). |
| **L6** `SafeExecutionSandbox` | RestrictedPython (kein builtins/import), Shell **nur** in Docker (`--network none --cap-drop ALL`), param SQL, realpath-Jail. Das echte "Säuberungs"-Molekül. |
| **L7** `CodeEvolutionEngine` | Genetisch: Crossover+Mutation, pygit2-Lineage, Turnier-Selektion, GRPO-ähnlicher Reward. |
| **L8** `VerificationProofEngine` | Policy-Skoring (Syntax/Mypy/Pytest/SQLi/SBOM/Compliance) → signierte, gehashte Proof-Receipts + GRPO-Gruppen. |
| **L9** `NeuroSymbolicEngine` | Die **Seele**: backward-chaining-Resolvent (Klausel/Fakten) + regex-LLM-Routing (Ollama/OpenAI→Fallback) + DSR-Trace-Visualizer (Mermaid). |

### K3 — Koordination (L10)
- **L10** `OrchestrationSwarm` — AgentRuntimes (TTL/Token-Budget/Lane), Prioritäts-Queue, Auto-Skalierung (2↔64, 30s-Cooling). Der **Herzschlag** der Aorta.

### K4 — Souveränität (L11–L17)
| Molekül | 1-Zeilen-Essenz |
|---|---|
| **L11** `DAOGovernanceEngine` | Quadratic Voting (√rep), Delegation, Verfassungs-Lock (≥75%), Not-Shutdown (2/3+3), Human-Veto. Voter-Seed via `NSE_DAO_SEED_VOTERS` (Default `root:100`). |
| **L12** `VisionAndGoals` | OKRs + Mission + Erreichungs-Wahrscheinlichkeit (conf·0.6 + progress·0.4). |
| **L13** `StrategyMarketEngine` | Prognose-Märkte: Crowd(35%)+Backtest(35%)+Sharpe(30%) → ACCUMULATE/HOLD/REDUCE. |
| **L14** `ComplianceGovernance` | Policy-as-Code (GDPR/EU-AI/NIST/PCI/SOX), läuft **vor** jeder Op, signierte Audit-Receipts. |
| **L15** `EthosIdentityLayer` | **ECC-Kern**: Ed25519-Sign + X25519/NaCl-Box + Merkle-Inklusions-Beweis + SQLite-Registry + SCrypt/AES-GCM-Keyvault. Public `get_anchor()` (CLI rüttelt nicht mehr am `_conn`). |
| **L16** `GeoPoliticalRouter` | Jurisdiktionskarte + Datenresidenz (Schrems-II→EU-Reroute, LGPD→BR, genetic→CN/RU-Deny). Demo-IP-Map via `NSE_GEO_DEMO_IP_MAP`; Oktett-Heuristik per Default **OFF** (`NSE_GEO_OCTET_HEURISTIC`). |
| **L17** `LegalSovereigntyEngine` | MultiSig (Replay+Duplikat-Block), Oracles, Charter-Registry, Compliance-Receipts. Public `admin_addresses()`. |

---

## 3. Bindungsmatrix (Datenfluss)

```
Körper L1/L2/L3 ──(Substrat)──▶ L10 Swarm ──(Aufträge)──▶ L6 Sandbox
L4 Knowledge ──▶ L9 Kognition ──(LLM-route)──▶ extern
L6 Output ──▶ L8 Verify ──▶ L7 Evolve ──(Receipts)──▶ L8 GRPO
ALLE Ops:  L14 Compliance(vor) + L15 Signatur + L16 Geo-Routing + L17 Legal
L11/DAO + L12 Vision + L13 Strategy ──(Governance-Signal)──▶ L14/L17
SKELETT: NSEPlatform(Nexus) bindet jede Molekül via BaseNSELayer
```

**Aorta-Röhre (horizontal):**
```
Request → L5 Gateway (Mündung) → L10 Swarm (Queue) → L6 Sandbox (Pumpen-Segment)
        → L8 Verify (Beweis) → L7 Evolve (Reflux-Lernen) → L14/L17 (Zoll+Kammer)
        → L15 Signatur (Blut) → Rückkanal
```
Zuordnung: L5 = **Mündung** (ein), L17 = **Kammer** (aus), dazwischen nur die Aorta.
L14/L16 = **Zollstationen** an der Aorten-fore. L15 = das **Blut** (Signatur/Reput),
das durch jede Kammer fließt.

---

## 4. Räumliche Pruning-Liste (was diese Revision gefixt hat)

| # | Fix | Status |
|---|---|---|
| **C2** | Zwei `layers/`-Bäume aufgelöst: root `assets/` (Voice/UI-Assets) + `neurosovereign/molecules/` (Moleküle); 22 Import-Fixes | ✅ |
| **C1** | K8s `emptyDir` → **PVC** `nse-state` (5Gi RWX) — der Park persistiert über Neustarts | ✅ |
| **C4** | Aorta-Egress `0.0.0.0/0:443` → **FQDN-Whitelist** (`nse-aorta-egress.yaml`, Calico) + RFC1918-Safety-Net; Config-Manifest in `nse-aorta-domains` | ✅ |
| **C3** | Nexus-Isolation: CLI `identity_verify` → `L15.get_anchor()`; L17-Smoke → `L17.admin_addresses()` (kein privater Handle mehr) | ✅ |
| **C5** | Defects: L13 tote `z`-Zeile entfernt · L2 Jetson-Edge konfigurierbar+warn · L5 `simulated`→`raise` · L1 Watt/Cost/Renewable env-getrieben · L11 Demo-Voter→`NSE_DAO_SEED_VOTERS` · L16 Demo-IP-Map+Oktett env-getrieben, Oktett per Default aus | ✅ |
| **C6** | 3× leere Docking-Ort → uniforme Stubs (`AVAILABLE=False` + `dock()→NotImplementedError`) + `DOCKING.md` (Vertrag) | ✅ |

**Zuordnung der Moleküle zum Raum:**
- *Rund um den Nexus:* L1–L3 (Körper, am Perikard), L10 (Herzmuskel), L9 (Gehirn).
- *Im Park:* alle Persistenz (L4/L8/L11–L17-DBs) + ge-seedete `assets/*`.
- *Auf der Aorta:* L5 (Mündung), L6 (Pumpen-Segment), L8/L7 (Reflux-Lernen), L17 (Aus-Kammer), L15 (Blut).
- *Außenmembran:* L14/L16 = Zollstationen (Compliance-Check & Geo-Grenze) an der Aorten-fore.

---

## 5. Offene Punkte (Cluster-/Upstream-Op, nicht Code)

| Thema | Aufwand |
|---|---|
| PVC-StorageClass (RWX: NFS/CephFS/CSI) im Cluster konfigurieren — YAML steht | Cluster-Op |
| Calico CNI aktivieren, um die FQDN-`host`-Einträge in `nse-aorta-egress.yaml` wirksam zu machen (aktuell RFC1918-Exclusion-Safety-Net) | CNI-Upgrade |
| L16: `NSE_GEO_PROVIDER` an eine echte Geo-DB (MaxMind/IP2Location) koppeln | Medium |
| L1: `sample_once` → echte pynvml-Telemetrie (env-Basis ist jetzt konfigurierbar, ohne HW bleibt Fallback) | HW-abhängig |
| `assets/6_cognitive/` (Voice ASR/TTS/Agenten) vs. `molecules/layer_9_cognition.py` (neuro-symbolisch) als **zwei Moleküle desselben Organells** in der Doku verankern | Doku |
| Upstream-PR als atomares `git commit` gegen `designico5/neuro-sovereign-enterprise-v5` | Upstream |

---

## 6. Verifikationsstatus (Stand dieser Revision)

- `py_compile` über alle 22 `.py` in `neurosovereign/` → **ALL OK**
- Import-Smoke: `NSEPlatform` construct + 17 `enable_layer_*` Flags + C3-Accessoren + C6-Vertrag → **PASS**
- `yaml.safe_load_all` über alle `k8s/*.yaml` → **OK**
- 0× `simulated`, 0× `emptyDir`, 0× `.layers.`-Import, 0 leere Docking-Ort → **0 verblieben**
- `__pycache__` + temporäre Hilfs-Skripte → **aufgeräumt**
