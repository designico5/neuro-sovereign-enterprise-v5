## Companion · 3D-Visualisierung dieser Architektur

Diese PR wird begleitet von einem **Full-Stack-3D-Atlas** (nicht Teil des Python-Repos,
sondern Companion unter `nse-v5-visual` / distributib als `nse-v5-visual.zip`):

```
React 19.1 · Three.js r169 (R3F 9.7 + Drei 10.7) · Framer Motion 11 · Tailwind v4 · Express
```

Rendert die räumliche Architektur interaktiv: **Nexus-Kern · Organellen-Ringe (K1–K4 + Ω) ·
pulsierende Aorta-Flow-Linie · Work-Order-Beam (Nexus→Molekül) · OSINT-Orbit · Park-PVC** +
Screenshot-PNG-Export. Start:

```
cd nse-v5-visual && npm install --legacy-peer-deps
npm run build && npm run start        # API :3001
node node_modules/vite/bin/vite.js preview --port 4173   # UI :4173
```

> Hinweis: Die 3D-App läuft lokal (kein Public-Hosting des Companion-Projekts) —
> oben sind die Start- und Paket-Wege dokumentiert.

---

## Die 1-Zeilen-Essenz (maximale Verdichtung)

> **Ein einzelner Nexus pulsiert (L10), lässt jeden Arbeitsgang über eine Aorta
> fließen (L5→L6→L8→L7), zeichnet ihn im Park ab (PVC state + OSINT-Connectors)
> und versiegelt ihn an der Außengrenze (L15 signiert · L14 prüft · L16 routet ·
> L17 gegenzeichnet) — der Körper (L1–L3) liefert Substrat, das Gehirn (L9)
> liefert Sinne, die Commons halten alles in einem Zustand.**

---

## Kurz-Checkliste für die Review

- **C1** K8s `emptyDir`→PVC `nse-state` (Park persistiert) — `k8s/nse-deployment.yaml`
- **C2** `layers/`→`assets/` + `neurosovereign/layers/`→`molecules/` (22 Import-Fixes, 0 Reste)
- **C3** Nexus-Isolation: CLI nutzt `L15.get_anchor()` / `L17.admin_addresses()`
- **C4** Aorta-Egress `0.0.0.0/0`→Calico-FQDN-Whitelist + RFC1918-Safety-Net — `k8s/nse-aorta-egress.yaml`
- **C5** Defects: L13 tote `z` · L2 Jetson env · L5 `raise` · L1/L11/L16 env-konfigurierbar
- **C6** 3× leere Docking-Ort→uniforme Stubs + `DOCKING.md`
- **OSINT** `osint/` Registry (6 live-verifizierte Docks) + `connectors.py` (out-of-process)

**Verifikation (statisch):** `py_compile` 37/37 · import-smoke PASS · K8s-YAML OK ·
0× `.layers.` / `emptyDir` / `simulated`(L5) · 0 leere Docking-Dirs.

**Folge-PR (nicht hier):** PVC-StorageClass (Cluster) · Calico-CNI · L16 Geo-DB · L1 pynvml ·
OSINT `dispatch_osint_lookup()` verdrahten.
