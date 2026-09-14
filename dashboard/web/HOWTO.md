# NEXUS TORUS · Living 3D Dashboard — wie es öffnen (korrekt)

## ⚠️ WICHTIG: Nicht per Doppelklick (file://) öffnen

Das gebaute `dist/index.html` lädt die 1.19 MB React/R3F-Engine als **ES-Module**
(`<script type="module">`). Browser blockieren ES-Module aus `file://`
wegen CORS → die Seite bleibt **leer**. Deshalb immer über einen **HTTP-Server**
öffnen. Das ist auch der Grund, warum `vite.config.ts` auf `base: "./"` steht
(relative `./assets/`-Pfade = portabel, funktioniert aber nur über HTTP).

## Drei Wege (empfohlen → schnell)

### 1) Vite-Preview (Produktions-Build, `dist/`)
```
cd dashboard/web
npm run serve          # oder: npm run preview
# → http://127.0.0.1:8765
```

### 2) Dev-Server (Hot-Reload, live Quellcode)
```
cd dashboard/web
npm run dev
# → http://127.0.0.1:8765
```

### 3) No-Build-Fallback (kein npm/node nötig)
```
cd dashboard            # das parent-Verzeichnis mit index.html
python -m http.server 8766
# → http://127.0.0.1:8766/index.html
```

## Stack
Vite 6 · React 19.2 · TypeScript 5.6 · @react-three/fiber 9 · drei 10 ·
Framer Motion 11 · Tailwind CSS 4 · Three.js r169

3D-Szene: 5-Schicht-Torus + 17-Layer-Golden-Angle-Kern + 520 Metabolismus-Partikel
+ Hexad-Ring + 5 Genie-Module + OrbitControls (Drag/Zoom) + Stars.
HUD: Layer-Fokus, 7 Live-Metriken, 369/Spark²-Phase, Genie-Multiplikatoren.
