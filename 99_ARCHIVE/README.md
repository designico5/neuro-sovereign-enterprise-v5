# 🕳️ NEXUS TORUS: 99_ARCHIVE — NSE-v5

Verdauungstrakt: Stasierte, inaktive Module.

## Prinzip
Nichts wird gelöscht (Invariante: `no_delete_or_overwrite_during_migration`).
Inaktive oder noch nicht implementierte Module werden hier gestaut,
mit einem Manifest, das den Grund und die Herkunft dokumentiert.

## Enthaltene Komponenten
- `science-codeevolve/` — geplantes Code-Evolution-Modul (leer, 0 Dateien)
- `self_improving_coding_agent/` — geplantes Self-Improving-Agent-Modul (leer, 0 Dateien)
- `verus/` — geplante formale Verifikation (Verus-Proof-Assistent) (leer, 0 Dateien)
- `_manifest.json` — Archiv-Manifest (Grund + Zeitstempel)

## Wiederaufnahme-Protokoll
Wenn eines der Module implementiert wird:
1. Dateien aus `99_ARCHIVE/<modul>/` zurück in die passende Schicht kopieren
2. In `_manifest.json` Status auf "reactivated" setzen
3. Die Schicht-README entsprechend aktualisieren
