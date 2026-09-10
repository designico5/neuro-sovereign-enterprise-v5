#!/usr/bin/env python3
"""
NexusTorus Spatial Restructuring — NSE-v5 Generalüberholung
============================================================
Copy-only Migration (invariante: no_delete_or_overwrite_during_migration)
Phasen: 369/Spark² (TRIAD → HEXAD → NEXUS PRIME)
"""
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DRY_RUN = "--apply" not in sys.argv
LOG: list[str] = []

def log(msg: str):
    LOG.append(msg)
    print(msg)

# ── TARGET TREE ──────────────────────────────────────────────────────────────
# Schicht 01_CORE
#   neurosovereign/  (Python-Code)
#   neuro_stack_final.toml
# Schicht 02_MEMBRANE
#   k8s/  terraform/  Dockerfile  docker-compose.yml
# Schicht 03_SYNAPSE
#   config/           (ehemals layers/)
#   ai_providers_config.json  ai_provider_manager.py  AI_PROVIDERS_README.md
# Schicht 04_OBSERVER
#   .github/  security/  signing/  state/
# Schicht 05_OUTPUT
#   deployment/  voice/  desktop/  setup/
# Schicht 99_ARCHIVE
#   science-codeevolve/  self_improving_coding_agent/  verus/

MOVE_MAP: dict[str, str] = {
    # 01_CORE
    "neurosovereign":             "01_CORE/neurosovereign",
    "neuro_stack_final.toml":    "01_CORE/neuro_stack_final.toml",
    # 02_MEMBRANE
    "k8s":                       "02_MEMBRANE/k8s",
    "terraform":                 "02_MEMBRANE/terraform",
    "Dockerfile":                "02_MEMBRANE/Dockerfile",
    "docker-compose.yml":        "02_MEMBRANE/docker-compose.yml",
    # 03_SYNAPSE
    "layers":                    "03_SYNAPSE/config",
    "ai_providers_config.json":  "03_SYNAPSE/ai_providers_config.json",
    "ai_provider_manager.py":    "03_SYNAPSE/ai_provider_manager.py",
    "AI_PROVIDERS_README.md":    "03_SYNAPSE/AI_PROVIDERS_README.md",
    # 04_OBSERVER
    ".github":                   "04_OBSERVER/.github",
    "SECURITY_ANALYSIS.md":      "04_OBSERVER/security/SECURITY_ANALYSIS.md",
    "SECURITY_ANALYSIS_V5_OPTIMIZED.md": "04_OBSERVER/security/SECURITY_ANALYSIS_V5_OPTIMIZED.md",
    "supply_chain_security.json": "04_OBSERVER/security/supply_chain_security.json",
    "supply_chain_security.sh":   "04_OBSERVER/security/supply_chain_security.sh",
    "cross_platform_signing.py":  "04_OBSERVER/signing/cross_platform_signing.py",
    "code_signing_infrastructure.json": "04_OBSERVER/signing/code_signing_infrastructure.json",
    "windows_signing_config.json": "04_OBSERVER/signing/windows_signing_config.json",
    "mac_signing_config.json":      "04_OBSERVER/signing/mac_signing_config.json",
    "CODE_SIGNING_README.md":       "04_OBSERVER/signing/CODE_SIGNING_README.md",
    "certificate_management.sh":    "04_OBSERVER/signing/certificate_management.sh",
    "state":                       "04_OBSERVER/state",
    # 05_OUTPUT
    "deploy_optimized_system.sh":   "05_OUTPUT/deployment/deploy_optimized_system.sh",
    "DEPLOYMENT_SUMMARY.md":        "05_OUTPUT/deployment/DEPLOYMENT_SUMMARY.md",
    "VOICE_INTERFACE_README.md":    "05_OUTPUT/voice/VOICE_INTERFACE_README.md",
    "setup_voice_interface.sh":     "05_OUTPUT/voice/setup_voice_interface.sh",
    "build_desktop_app.py":         "05_OUTPUT/desktop/build_desktop_app.py",
    "electron_builder_config.yml":  "05_OUTPUT/desktop/electron_builder_config.yml",
    "setup_ollama.sh":              "05_OUTPUT/setup/setup_ollama.sh",
    "setup_openai.sh":              "05_OUTPUT/setup/setup_openai.sh",
    "setup_opencodezen.sh":         "05_OUTPUT/setup/setup_opencodezen.sh",
    "setup_secure_credentials.sh":  "05_OUTPUT/setup/setup_secure_credentials.sh",
    # 99_ARCHIVE (leere Orphans)
    "science-codeevolve":           "99_ARCHIVE/science-codeevolve",
    "self_improving_coding_agent": "99_ARCHIVE/self_improving_coding_agent",
    "verus":                       "99_ARCHIVE/verus",
}

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def migrate():
    log(f"=== NEXUS-TORUS SPATIAL MIGRATION ===")
    log(f"ROOT: {ROOT}")
    log(f"DRY_RUN: {DRY_RUN}")
    log("")

    for src, dst in MOVE_MAP.items():
        src_path = ROOT / src
        dst_path = ROOT / dst
        if not src_path.exists():
            log(f"  ⚠ skip: {src} (not found)")
            continue
        if dst_path.exists():
            log(f"  ⚠ skip: {dst} already exists (no-overwrite invariant)")
            continue
        ensure_dir(dst_path.parent)
        if DRY_RUN:
            log(f"  [dry-run] {src}  →  {dst}")
        else:
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True) if src_path.is_dir() \
                else shutil.copy2(src_path, dst_path)
            log(f"  ✅ copy  {src}  →  {dst}")

    # ── Write 99_ARCHIVE manifest ─────────────────────────────────────────────
    arch_manifest = {
        "archived_at": STAMP,
        "invariant": "no_delete_or_overwrite_during_migration",
        "items": [
            {"path": "99_ARCHIVE/science-codeevolve",
             "reason": "empty directory (0 files) — planned module, not implemented"},
            {"path": "99_ARCHIVE/self_improving_coding_agent",
             "reason": "empty directory (0 files) — planned module, not implemented"},
            {"path": "99_ARCHIVE/verus",
             "reason": "empty directory (0 files) — formal verification, not implemented"},
        ],
    }
    arch_path = ROOT / "99_ARCHIVE" / "_manifest.json"
    if DRY_RUN:
        log(f"  [dry-run] 99_ARCHIVE/_manifest.json")
    else:
        ensure_dir(arch_path.parent)
        arch_path.write_text(json.dumps(arch_manifest, indent=2))
        log(f"  ✅ wrote 99_ARCHIVE/_manifest.json")

    # ── Write spatial manifest ────────────────────────────────────────────────
    spatial_manifest = {
        "method": "NexusTorus 369/Spark²",
        "stamp": STAMP,
        "invariants": [
            "no_delete_or_overwrite_during_migration",
            "unknown_evidence_is_not_success",
        ],
        "layers": {
            "01_CORE": {
                "role": "invarianter Kernel",
                "contains": ["neurosovereign/", "neuro_stack_final.toml"],
                "note": "The 17-layer Python package + invariant stack config"
            },
            "02_MEMBRANE": {
                "role": "semi-permeable Grenze",
                "contains": ["k8s/", "terraform/", "Dockerfile", "docker-compose.yml"],
                "note": "IaC + container boundary — infrastructure as membrane"
            },
            "03_SYNAPSE": {
                "role": "autokatalytisches Netzwerk",
                "contains": ["config/ (ehem. layers/)", "ai_providers_config.json",
                               "ai_provider_manager.py", "AI_PROVIDERS_README.md"],
                "note": "Layer config + AI provider connectivity"
            },
            "04_OBSERVER": {
                "role": "Meta-Ebene",
                "contains": [".github/", "security/", "signing/", "state/"],
                "note": "CI/CD + security analysis + code signing + runtime state"
            },
            "05_OUTPUT": {
                "role": "manifestierte Realität",
                "contains": ["deployment/", "voice/", "desktop/", "setup/"],
                "note": "Deployment scripts + voice + desktop + setup scripts"
            },
            "99_ARCHIVE": {
                "role": "Verdauungstrakt",
                "contains": ["science-codeevolve/", "self_improving_coding_agent/",
                               "verus/", "_manifest.json"],
                "note": "Empty orphan directories — stashed, not deleted"
            },
        },
        "root_kept": [
            "README.md", "requirements.txt", "package.json",
            "pyproject.toml", ".env.template", ".gitignore", ".gitmodules",
        ],
    }
    sp_path = ROOT / "_nexus_spatial_manifest.json"
    if DRY_RUN:
        log(f"  [dry-run] _nexus_spatial_manifest.json")
    else:
        sp_path.write_text(json.dumps(spatial_manifest, indent=2, ensure_ascii=False))
        log(f"  ✅ wrote _nexus_spatial_manifest.json")

    log("")
    log("MIGRATION DONE")
    if DRY_RUN:
        log("Run with --apply to execute the copy.")
    else:
        log(f"All copied. Old paths still in place (no-overwrite invariant).")

if __name__ == "__main__":
    migrate()
