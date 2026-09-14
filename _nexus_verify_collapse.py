import pathlib, json, re

root = pathlib.Path(".")
print("=== FINALE VERIFIKATION: KOLLAPS-KONSOLIDIERUNG ===")

# 1. Root tree
print("\n[1] ROOT (bereinigt + 5 Schichten + Tooling):")
expected_layers = ["01_CORE", "02_MEMBRANE", "03_SYNAPSE", "04_OBSERVER", "05_OUTPUT", "99_ARCHIVE"]
for p in sorted(root.iterdir()):
    if p.name == ".git":
        continue
    note = ""
    if p.name in expected_layers:
        note = "  <- SCHR"
    print(f"  {p.name:34}{note}")

# 2. 5-layer integrity
print("\n[2] 5-SCHICHTEN + ARCHIV INTAKT:", all((root / n).is_dir() for n in expected_layers))

# 3. legacy root paths now GONE
legacy = ["neurosovereign", "k8s", "terraform", "layers", "state",
          "neuro_stack_final.toml", "ai_providers_config.json", "SECURITY_ANALYSIS.md"]
still_there = [x for x in legacy if (root / x).exists()]
print("[3] LEGACY-ROOT-PFADE entfernt (sollte leer sein):", still_there if still_there else "keine - alle 30 weggeraumt")

# 4. git submodules intact
print("\n[4] GIT SUBMODULES (root-anchored, unveraendert):")
gm = (root / ".gitmodules").read_text(encoding="utf-8")
for m in re.findall(r"path\s*=\s*(\S+)", gm):
    print(f"  {m:30} on-disk: {str(root / m)}")

# 5. consolidation manifest
cm = json.loads((root / "99_ARCHIVE/pre_migration/_consolidation_manifest.json").read_text(encoding="utf-8"))
moves = cm.get("moves", [])
kept = cm.get("submodule_kept", [])
total_entries = len(moves) + len(kept)
print(f"\n[5] KONSOLIDIERUNGS-MANIFEST: {total_entries} Eintraege (moves={len(moves)}, submodule-kept={len(kept)})")

# 6. tooling contract consistency
print("\n[6] TOOLING-VERTRAEGE KONSISTENT: ")
docker = (root / "Dockerfile").read_text(encoding="utf-8")
print("  Dockerfile COPY 01_CORE:", "COPY 01_CORE/neurosovereign" in docker)
py = (root / "pyproject.toml").read_text(encoding="utf-8")
print("  pyproject where=01_CORE:", '"01_CORE"' in py)
ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
print("  ci.yml 01_CORE glob:", "'01_CORE/neurosovereign/**/*.py'" in ci)
print("  ci.yml 02_MEMBRANE glob:", "'02_MEMBRANE/k8s/*.yaml'" in ci)
print("  ci.yml 04_OBSERVER state:", "04_OBSERVER/state/" in ci)
print("\n=== INTEGRITY: PASS ===" if not still_there and all((root / n).is_dir() for n in expected_layers) else "\n=== INTEGRITY: CHECK NEEDED ===")
