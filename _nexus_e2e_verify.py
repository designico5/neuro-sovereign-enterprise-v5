"""End-to-End: prove the post-collapse 5-layer structure is coherent.
Exercises exactly the paths the CI contracts now reference."""
import pathlib, sys, subprocess, json

root = pathlib.Path(".")
ok, fail = 0, 0

def check(name, cond, detail=""):
    global ok, fail
    mark = "PASS" if cond else "FAIL"
    if cond: ok += 1
    else: fail += 1
    print(f"  [{mark}] {name}" + (f"  -- {detail}" if detail and not cond else ""))

print("=== NSE-v5 POST-KOLLAPS END-TO-END VERIFIKATION ===\n")

# 1. 5 layers + archive present
print("[1] SCHICHTEN + ARCHIV")
for n in ["01_CORE", "02_MEMBRANE", "03_SYNAPSE", "04_OBSERVER", "05_OUTPUT", "99_ARCHIVE"]:
    check(f"{n}/", (root / n).is_dir())

# 2. Python package compiles from 01_CORE (CI glob path)
print("\n[2] 01_CORE PYTHON (CI: '01_CORE/neurosovereign/**/*.py' compile)")
pyfiles = list((root / "01_CORE").rglob("*.py"))
check(f"python files under 01_CORE", len(pyfiles) > 0, f"{len(pyfiles)} found")
# compile each
bad = []
for f in pyfiles:
    try:
        compile(f.read_text(encoding="utf-8"), str(f), "exec")
    except SyntaxError as e:
        bad.append(f"{f.name}:{e.lineno}")
check("all 01_CORE py compile clean", not bad, "; ".join(bad[:5]))

# 3. k8s YAML valid in 02_MEMBRANE
print("\n[3] 02_MEMBRANE k8s (CI: '02_MEMBRANE/k8s/*.yaml')")
k8s = list((root / "02_MEMBRANE/k8s").glob("*.yaml")) if (root / "02_MEMBRANE/k8s").exists() else []
check("k8s yaml present", len(k8s) > 0, f"{len(k8s)} found")
yaml_ok = True
if k8s:
    try:
        import yaml
        for y in k8s:
            list(yaml.safe_load_all(y.read_text(encoding="utf-8")))
    except Exception as e:
        yaml_ok = False
        print("    yaml err:", e)
check("k8s yaml parse", yaml_ok)
# terraform in 02_MEMBRANE
tf = list((root / "02_MEMBRANE/terraform").glob("*.tf")) if (root / "02_MEMBRANE/terraform").exists() else []
check("terraform .tf present", len(tf) > 0, f"{len(tf)} found")

# 4. 03_SYNAPSE config tree
print("\n[4] 03_SYNAPSE config (Layer-Config)")
syn = root / "03_SYNAPSE"
syn_files = list(syn.rglob("*")) if syn.exists() else []
check("03_SYNAPSE has content", len([f for f in syn_files if f.is_file()]) > 0, "empty")

# 5. 04_OBSERVER state
print("\n[5] 04_OBSERVER state")
obs = root / "04_OBSERVER"
obs_files = [f for f in obs.rglob("*") if f.is_file()] if obs.exists() else []
check("04_OBSERVER has content", len(obs_files) > 0, "empty")

# 6. 05_OUTPUT
print("\n[6] 05_OUTPUT")
out = root / "05_OUTPUT"
out_files = [f for f in out.rglob("*") if f.is_file()] if out.exists() else []
check("05_OUTPUT has content", len(out_files) > 0, "empty")

# 7. archive intact (no-delete invariant)
print("\n[7] 99_ARCHIVE (no-delete invariant)")
arch = root / "99_ARCHIVE/pre_migration"
arch_files = [f for f in arch.rglob("*") if f.is_file()] if arch.exists() else []
check("archive has consolidated files", len(arch_files) > 0, "empty")
mani = arch / "_consolidation_manifest.json"
check("consolidation manifest present", mani.exists())

# 8. legacy root paths gone
print("\n[8] LEGACY-ROOT PFADE (müssen weg sein)")
legacy = ["neurosovereign", "k8s", "terraform", "layers", "state",
          "neuro_stack_final.toml", "SECURITY_ANALYSIS.md"]
still = [x for x in legacy if (root / x).exists()]
check("legacy root removed", not still, f"still: {still}")

# 9. dashboard
print("\n[9] DASHBOARD")
check("single-file fallback", (root / "dashboard/index.html").exists())
check("max-level dist build", (root / "dashboard/web/dist/index.html").exists())

# 10. tooling contract consistency
print("\n[10] TOOLING-VERTRÄGE KONSISTENT")
docker = (root / "Dockerfile").read_text(encoding="utf-8")
check("Dockerfile COPY 01_CORE", "COPY 01_CORE/neurosovereign" in docker)
py = (root / "pyproject.toml").read_text(encoding="utf-8")
check("pyproject where=01_CORE", '"01_CORE"' in py)
ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
check("ci 01_CORE glob", "'01_CORE/neurosovereign/**/*.py'" in ci)
check("ci 02_MEMBRANE k8s glob", "'02_MEMBRANE/k8s/*.yaml'" in ci)
check("ci 04_OBSERVER state", "04_OBSERVER/state/" in ci)

print(f"\n=== E2E RESULT: {ok} PASS / {fail} FAIL ===")
sys.exit(0 if fail == 0 else 1)
