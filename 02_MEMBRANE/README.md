# ⟂ NEXUS TORUS: 02_MEMBRANE — NSE-v5

Semi-permeable Grenze: Infrastruktur-Abstraktion (IaC + Container).

## Prinzip
Die Membrane trennt den invarianten Kernel (01_CORE) von der äußeren Welt.
Sie ist der einzige Ort, an dem externe Infrastrukturregelungen eingreifen dürfen.

## Enthaltene Komponenten
- `k8s/` — Kubernetes-Manifeste (Deployment, HPA, NetworkPolicy, PDB)
- `terraform/` — Terraform-IaC (multi-cloud: AWS/GCP/Azure)
- `Dockerfile` — Container-Build für die NSE-Plattform
- `docker-compose.yml` — lokale Multi-Container-Orchestrierung

## Layer-Bezug
- Layer 3 (Infrastructure IaC) → `terraform/` + `k8s/`
- Layer 6 (Execution Sandbox) → `Dockerfile` (Docker-Isolation)
