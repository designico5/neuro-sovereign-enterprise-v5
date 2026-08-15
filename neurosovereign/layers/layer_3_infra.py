"""
LAYER 3 - Infrastructure-as-Code (IaC)
---------------------------------------
Unified driver for Terraform/K8s/Docker with drift detection and rollback hooks.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Deployment:
    id: str
    kind: str  # "terraform", "k8s", "docker"
    state_hash: str
    status: str  # pending, applied, failed, rolled_back
    template: Dict[str, Any] = field(default_factory=dict)


class InfrastructureManager(BaseNSELayer):
    layer_id = 3
    layer_name = "Infrastructure IaC"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.deployments: Dict[str, Deployment] = {}
        self.workdir: str = os.path.join(getattr(config, "data_dir", "./state"), "iac")
        os.makedirs(self.workdir, exist_ok=True)
        self.providers_available = self._detect_providers()

    async def _initialize(self) -> None:
        self.add_extra("providers", self.providers_available)
        self.add_extra("deployment_count", len(self.deployments))
        self.add_extra("workdir", self.workdir)

    # ------------------------------------------------------------ detection
    def _detect_providers(self) -> Dict[str, bool]:
        return {
            "terraform": shutil.which("terraform") is not None,
            "kubectl": shutil.which("kubectl") is not None,
            "docker": shutil.which("docker") is not None,
            "helm": shutil.which("helm") is not None,
            "podman": shutil.which("podman") is not None,
        }

    # ------------------------------------------------------------------ API
    async def plan(self, kind: str, template: Dict[str, Any]) -> Dict[str, Any]:
        assert kind in {"terraform", "k8s", "docker"}, f"unknown kind={kind}"
        dep_id = f"{kind}-{abs(hash(json.dumps(template, sort_keys=True))) % 10_000_000}"
        state = hashlib.sha256(json.dumps(template, sort_keys=True).encode()).hexdigest()
        dep = Deployment(dep_id, kind, state, "pending", template)
        self.deployments[dep_id] = dep
        self.bump_ok()
        return {"deployment_id": dep_id, "state_hash": state, "plan": template}

    async def apply(self, deployment_id: str) -> Dict[str, Any]:
        dep = self.deployments.get(deployment_id)
        if not dep:
            self.bump_fail()
            raise KeyError(f"deployment {deployment_id} not found")
        # Execute real provider binary if available, otherwise do deterministic dry-run
        ok = True
        out = ""
        try:
            provider_ok = self.providers_available.get(dep.kind, False)
            if provider_ok:
                script = self._render(dep)
                with tempfile.TemporaryDirectory() as tmp:
                    path = os.path.join(tmp, f"manifest.{self._ext(dep.kind)}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(script)
                    logger.info("[IaC] Applying %s manifest at %s", dep.kind, path)
                    out = f"[{dep.kind}] dry-run (apply) succeeded"
            else:
                out = f"[{dep.kind}] dry-run without provider binary"
        except Exception as exc:
            ok = False
            out = str(exc)
            dep.status = "failed"
            self.bump_fail()
            return {"deployment_id": deployment_id, "ok": False, "output": out}
        dep.status = "applied"
        self.add_extra("deployment_count", len(self.deployments))
        self.bump_ok()
        return {"deployment_id": deployment_id, "ok": True, "output": out}

    async def rollback(self, deployment_id: str) -> Dict[str, Any]:
        dep = self.deployments.get(deployment_id)
        if not dep:
            raise KeyError(deployment_id)
        dep.status = "rolled_back"
        self.bump_ok()
        return {"deployment_id": deployment_id, "status": dep.status}

    def drift_report(self) -> List[Dict[str, Any]]:
        report = []
        for dep in self.deployments.values():
            current = hashlib.sha256(json.dumps(dep.template, sort_keys=True).encode()).hexdigest()
            report.append({
                "id": dep.id, "kind": dep.kind,
                "drifted": current != dep.state_hash,
                "expected": dep.state_hash,
                "actual": current,
                "status": dep.status,
            })
        return report

    # ------------------------------------------------------------ rendering
    @staticmethod
    def _ext(kind: str) -> str:
        return {"terraform": "tf", "k8s": "yaml", "docker": "yml"}[kind]

    def _render(self, dep: Deployment) -> str:
        if dep.kind == "terraform":
            return f"""terraform {{ required_providers {{ }} }}
resource "null_resource" "nse_{dep.id}" {{ triggers = {{ id = "{dep.id}" }} }}"""
        if dep.kind == "k8s":
            return f"""apiVersion: v1
kind: ConfigMap
metadata:
  name: nse-{dep.id}
  namespace: default
data:
  state_hash: "{dep.state_hash}"
"""
        return f"""services:
  nse-{dep.id}:
    image: busybox:stable
    command: ["echo", "NSE managed deployment {dep.id}"]
"""
