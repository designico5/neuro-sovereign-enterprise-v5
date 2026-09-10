# OSINT Docking — externe Open-Source-Werkzeuge

Die Ordner `osint/` (registrierbar) und die drei C6-Docking-Ort binden **externe**
OSINT / Threat-Intel / Verifikations-Repos an die NSE-Moleküle. Sie sind bewusst
**nicht** interne Moleküle: sie docken an der **Aorta** (L5 Egress + L4 Store) und
an den C6-Stellplätzen.

## Bindematrix (Repo → Molekül)

| GitHub-Repo | Lizenz | Molekül | Rolle | Aorta-FQDN | ★ (live, 2026-09-10) |
|---|---|---|---|---|---|
| `OpenCTI-Platform/opencti` | NOASSERTION | L4 + L5 | STIX/TAXII-Intellgraph → Vektor/Graf-Store | `opencti.internal:8080` | 9 919 |
| `MISP/MISP` | AGPL-3.0 | L4 + L5 | Open Threat-Intel-Sharing (Events) | `misp.internal` | 6 516 |
| `intelowlproject/IntelOwl` | AGPL-3.0 | L5 | Multi-Analyser-Orchestrierung | `intelowl.internal` | 4 705 |
| `smokroot/spiderfoot` | GPL-3.0 | L5 | Passive OSINT-Spidering (DNS/whois/Leaks) | `spiderfoot.internal:5001` | (nicht live-geprüft) |
| `verus-lang/verus` | MIT | `verus/` (C6) → L8 | formale Verifikations-Backends für Proof-Receipts | — | 3 005 |
| `All-Hands-AI/OpenHands` | MIT | `self_improving_coding_agent/` (C6) → L7 | Coding-Agent-Harness (ECC-Stub) | — | 87 159 |

> **Lizenzen:** OpenCTI ist kein Einzel-Lizenzprojekt (NOASSERTION) → vor dem
> Wires je-Komponente prüfen. MISP/IntelOwl = AGPL-3.0, spiderfoot = GPL-3.0 →
> **Kopplungs-Risiko** für die Aorta: als isolierte Prozess/Service betreiben
> (nicht in `neurosovereign` importieren), Egress via FQDN-Whitelist.
> verus/OpenHands = MIT → sauberes In-Repo-Docken möglich.

## Egress-Kopplung

Die Aorta-FQDNs sind in `k8s/nse-aorta-egress.yaml` im Config-Manifest
`nse-aorta-domains` vermerkt. Sobald ein Repo als isolierter Service läuft,
wird seine interne FQDN in die Calico-Whitelist eingetragen (siehe
`OPERATIONAL NOTE` in dieser Datei).

## Status

`osint/AVAILABLE = False` — kein OSINT-Repo ist noch gekoppelt.

**Binde-Layer:** `osint/connectors.py` liefert die fertigen Noun-Dock-Functions
(`bind_opencti`, `bind_misp`, `bind_spiderfoot`, `bind_intelowl`). Sie koppeln die
externe Registry über die **Nexus-Grenze** an L4/L5 (nur Molekül-API, kein direkter
fremder Handle) und halten AGPL/GPL-Tooling bewusst **out-of-process** (Aorta-Egress),
damit der Core lizenzsaub bleibt.

Zum Ankoppeln:
1. Repo klonen/bauen (Service), 2. FQDN in die Aorta-Whitelist, 3. im
   `osint/__init__.py` `available=True` + `dock()` implementieren, 4. am Nexus
   registrieren. Bis dahin ist jeder `dock()`-Aufruf ein lautes
   `NotImplementedError` (laut C6-Vertrag).
