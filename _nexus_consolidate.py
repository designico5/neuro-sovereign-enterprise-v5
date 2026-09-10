#!/usr/bin/env python3
"""
NexusTorus KOLLAPS (Phase 9, 2. Stufe) — Konsolidierung
=========================================================
Verschiebt die legacy Root-Duplikate nach 99_ARCHIVE/pre_migration/
(sie sind nun durch die 5-Schicht-Struktur ersetzt).

Invariante: no_delete_or_overwrite_during_migration
  - Alles wird VERSCHOBEN (move), nie geloescht.
  - Ziel existiert bereits -> skip (kein ueberschreiben).
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
DRY = "--apply" not in sys.argv
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
PRE = ROOT / "99_ARCHIVE" / "pre_migration"
lines: list[str] = []

def log(m: str):
    lines.append(m)

# WICHTIG: Tooling-Vertraege + Git-managed Items BLEIBEN IM ROOT.
#   - .github         -> GitHub Actions laest .github NUR aus dem Repo-Root
#   - Dockerfile / docker-compose.yml -> docker build erwartet diese im Root
#   - pyproject.toml / package.json / requirements.txt / README.md -> Build-Meta
#   - .gitmodules + die 3 Submodule-Dirs -> Git-Verwaltung (gitlink), nicht verschiebbar
#
# Reine Inhalts-Duplikate -> stauen in 99_ARCHIVE/pre_migration/
MOVE = [
    # 01_CORE ersetzt
    "neurosovereign",
    "neuro_stack_final.toml",
    # 02_MEMBRANE ersetzt (IaC-Quellen, nicht die Tooling-Docker-Dateien)
    "k8s", "terraform",
    # 03_SYNAPSE ersetzt
    "layers", "ai_providers_config.json", "ai_provider_manager.py", "AI_PROVIDERS_README.md",
    # 04_OBSERVER ersetzt
    "SECURITY_ANALYSIS.md", "SECURITY_ANALYSIS_V5_OPTIMIZED.md",
    "supply_chain_security.json", "supply_chain_security.sh",
    "cross_platform_signing.py", "code_signing_infrastructure.json",
    "windows_signing_config.json", "mac_signing_config.json",
    "CODE_SIGNING_README.md", "certificate_management.sh",
    "state",
    # 05_OUTPUT ersetzt
    "deploy_optimized_system.sh", "DEPLOYMENT_SUMMARY.md",
    "VOICE_INTERFACE_README.md", "setup_voice_interface.sh",
    "build_desktop_app.py", "electron_builder_config.yml",
    "setup_ollama.sh", "setup_openai.sh", "setup_opencodezen.sh",
    "setup_secure_credentials.sh",
]

# Git-Submodule -> BLEIBEN IM ROOT (gitlink + .gitmodules). Hier nur dokumentiert,
# NICHT verschoben. Die leeren (nicht initialisierten) gitlink-Dirs sind Git-Bookmarks.
SUBMODULES = ["verus", "self_improving_coding_agent", "science-codeevolve"]

def move_item(src_name: str, dest_dir: Path, reason: str) -> str:
    src = ROOT / src_name
    dst = dest_dir / src_name
    if not src.exists():
        return f"  [skip-missing] {src_name}"
    if dst.exists():
        return f"  [skip-exists] {src_name} (no-overwrite invariant)"
    dest_dir.mkdir(parents=True, exist_ok=True)
    if DRY:
        return f"  [dry-run] move {src_name} -> {dest_dir.name}/{src_name}  ({reason})"
    # Verzeichnisse sicher verschieben (git submodule gitlinks inbegriffen)
    shutil.move(str(src), str(dst))
    return f"  [moved] {src_name} -> {dest_dir.name}/{src_name}  ({reason})"

def run():
    log(f"=== NEXUS-TORUS KOLLAPS / KONSOLIDIERUNG ===  (DRY_RUN={DRY})")
    PRE.mkdir(parents=True, exist_ok=True)
    manifest_moves = []

    for name in MOVE:
        msg = move_item(name, PRE, "legacy root replaced by 5-layer spatial structure")
        log(msg); manifest_moves.append({"item": name, "to": f"99_ARCHIVE/pre_migration/{name}", "result": msg.strip()})

    for sm in SUBMODULES:
        # Git-Submodule: im Root behalten (gitlink + .gitmodules). Nur dokumentiert.
        msg = f"  [git-submodule-kept] {sm} (remains root-anchored, not moved)"
        log(msg); manifest_moves.append({"item": sm, "to": "(root, git-submodule)", "result": "kept", "submodule": True})

    man = {
        "phase": "KOLLAPS/consolidation",
        "stamp": STAMP,
        "method": "NexusTorus 369/Spark2",
        "invariants": ["no_delete_or_overwrite_during_migration"],
        "active_source": {
            "python_package": "01_CORE/neurosovereign (pyproject where=['01_CORE'])",
            "stack_config": "01_CORE/neuro_stack_final.toml",
        },
        "kept_in_root": [
            "README.md", "requirements.txt", "pyproject.toml", "package.json",
            ".env.template", ".gitignore", ".gitmodules", "NEXUS_TORUS_STRUCTURE.md",
        ],
        "moves": manifest_moves,
    }
    man_path = ROOT / "99_ARCHIVE" / "pre_migration" / "_consolidation_manifest.json"
    man_path.parent.mkdir(parents=True, exist_ok=True)
    if DRY:
        log(f"  [dry-run] write {man_path.relative_to(ROOT)}")
    else:
        man_path.write_text(json.dumps(man, indent=2, ensure_ascii=False))
        log(f"  [wrote] 99_ARCHIVE/pre_migration/_consolidation_manifest.json")

    out = ROOT / "_consolidate_out.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if DRY:
        print("\nRun with --apply to execute the moves.")

if __name__ == "__main__":
    run()
