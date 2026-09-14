"""Fix tooling contracts (Dockerfile + CI) to point at the new 5-layer paths
after the consolidation moved the legacy root items to 99_ARCHIVE/pre_migration/."""
import pathlib

root = pathlib.Path(__file__).parent

# ---- Dockerfile: two COPY lines + runtime comment ----
p = root / "Dockerfile"
s = p.read_text(encoding="utf-8")
before = s.count("COPY neurosovereign ./neurosovereign")
s = s.replace(
    "COPY neurosovereign ./neurosovereign",
    "COPY 01_CORE/neurosovereign ./01_CORE/neurosovereign",
)
s = s.replace(
    "# Application source at the same /app path so the editable install resolves",
    "# Application source at 01_CORE so the editable install (pyproject where=01_CORE) resolves",
)
p.write_text(s, encoding="utf-8")
print(f"Dockerfile: {before} COPY refs -> 01_CORE")

# ---- ci.yml: three path refs ----
p2 = root / ".github" / "workflows" / "ci.yml"
s2 = p2.read_text(encoding="utf-8")
n_neuro = s2.count("'neurosovereign/**/*.py'")
n_k8s = s2.count("'k8s/*.yaml'")
n_state = s2.count("state/")
s2 = s2.replace("'neurosovereign/**/*.py'", "'01_CORE/neurosovereign/**/*.py'")
s2 = s2.replace("'k8s/*.yaml'", "'02_MEMBRANE/k8s/*.yaml'")
s2 = s2.replace("state/", "04_OBSERVER/state/")
p2.write_text(s2, encoding="utf-8")
print(f"ci.yml: neuro={n_neuro} k8s={n_k8s} state={n_state} -> 5-layer paths")

# ---- verify no leftover old-path refs in tooling ----
leftover = []
for f in [root / "Dockerfile", root / ".github" / "workflows" / "ci.yml"]:
    txt = f.read_text(encoding="utf-8")
    for pat in [
        "COPY neurosovereign ./neurosovereign",
        "'neurosovereign/**/*.py'",
        "'k8s/*.yaml'",
        "\n          state/",
    ]:
        if pat in txt:
            leftover.append((f.name, pat))
print("LEFTOVER:", leftover if leftover else "none - all tooling now points to 5-layer paths")
