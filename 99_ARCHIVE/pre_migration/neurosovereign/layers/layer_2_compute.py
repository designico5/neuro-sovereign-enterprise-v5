"""
LAYER 2 - Compute Silicon
-------------------------
Heterogeneous compute manager: NVIDIA H100/A100, AMD MI300, Apple M-series,
Jetson Orin, CPU fallbacks and vendor-aware model selection/routing.
"""
from __future__ import annotations

import logging
import platform
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .base import BaseNSELayer

logger = logging.getLogger(__name__)

ComputeTier = Literal["inference", "training", "lowpower", "edge"]


@dataclass(slots=True)
class ComputeDevice:
    id: str
    vendor: str
    model: str
    tier: ComputeTier
    vram_gb: float
    available_gb: float
    utilization_pct: float
    enabled: bool = True


class ComputeSiliconManager(BaseNSELayer):
    layer_id = 2
    layer_name = "Compute Silicon"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.devices: List[ComputeDevice] = []
        self.routing_policy: Dict[ComputeTier, str] = {
            "inference": "low-latency",
            "training": "highest-memory",
            "lowpower": "minimum-watts",
            "edge": "jetson-orin-only",
        }

    async def _initialize(self) -> None:
        self._discover_nvidia()
        self._discover_amd()
        self._discover_cpu()
        self._discover_apple_silicon()
        if not self.devices:
            self.devices.append(
                ComputeDevice("cpu-local", "Generic", platform.processor() or "CPU",
                              "lowpower", 8.0, 4.0, 0.1)
            )
        self.add_extra("device_count", len(self.devices))
        self.add_extra("total_vram_gb", round(sum(d.vram_gb for d in self.devices), 1))

    # ------------------------------------------------------------ detection
    def _discover_nvidia(self) -> None:
        try:  # pragma: no cover - hardware specific
            import pynvml  # type: ignore

            pynvml.nvmlInit()
            for i in range(pynvml.nvmlDeviceGetCount()):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(h)
                mem = pynvml.nvmlDeviceGetMemoryInfo(h)
                util = pynvml.nvmlDeviceGetUtilizationRates(h)
                tier: ComputeTier = "inference" if mem.total / 1024**3 < 80 else "training"
                self.devices.append(ComputeDevice(
                    id=f"nvidia-{i}", vendor="NVIDIA", model=name, tier=tier,
                    vram_gb=round(mem.total / 1024**3, 2),
                    available_gb=round(mem.free / 1024**3, 2),
                    utilization_pct=util.gpu / 100.0,
                ))
        except Exception:
            pass

    def _discover_amd(self) -> None:
        try:  # pragma: no cover - hardware specific
            import subprocess

            out = subprocess.check_output(["rocm-smi", "--showproductname", "--csv"], text=True, timeout=10)
            for idx, line in enumerate(out.splitlines()[1:]):
                if not line.strip():
                    continue
                model = line.split(",")[-1]
                self.devices.append(ComputeDevice(
                    id=f"amd-{idx}", vendor="AMD", model=model, tier="inference",
                    vram_gb=24.0, available_gb=20.0, utilization_pct=0.05,
                ))
        except Exception:
            pass

    def _discover_apple_silicon(self) -> None:
        if platform.system() != "Darwin":
            return
        machine = platform.machine().lower()
        if machine.startswith("arm") or machine in ("arm64", "aarch64"):
            import psutil  # type: ignore
            self.devices.append(ComputeDevice(
                id="apple-ane", vendor="Apple",
                model=platform.processor() or "Apple Silicon ANE",
                tier="edge", vram_gb=psutil.virtual_memory().total / 1024**3,
                available_gb=psutil.virtual_memory().available / 1024**3,
                utilization_pct=0.1,
            ))

    def _discover_cpu(self) -> None:
        try:
            import psutil  # type: ignore

            mem = psutil.virtual_memory()
            self.devices.append(ComputeDevice(
                id="cpu-local", vendor="CPU", model=platform.processor() or "Generic",
                tier="lowpower",
                vram_gb=round(mem.total / 1024**3, 2),
                available_gb=round(mem.available / 1024**3, 2),
                utilization_pct=psutil.cpu_percent(0.1) / 100.0,
            ))
        except Exception:
            pass

    # ----------------------------------------------------------------- API
    def pick_device(self, tier: ComputeTier, min_vram_gb: float = 2.0) -> Optional[ComputeDevice]:
        eligible = [
            d for d in self.devices
            if d.enabled and d.tier == tier and d.available_gb >= min_vram_gb
        ]
        if not eligible:
            eligible = [d for d in self.devices if d.enabled and d.available_gb >= min_vram_gb]
        if not eligible:
            return None
        policy = self.routing_policy[tier]
        if policy == "low-latency":
            return min(eligible, key=lambda d: d.utilization_pct)
        if policy == "highest-memory":
            return max(eligible, key=lambda d: d.available_gb)
        if policy == "minimum-watts":
            return min(eligible, key=lambda d: d.vram_gb)
        if policy == "jetson-orin-only":
            j = [d for d in eligible if "orin" in d.model.lower() or "jetson" in d.model.lower()]
            return j[0] if j else eligible[0]
        return eligible[0]

    def inventory(self) -> Dict[str, Any]:
        return {
            "devices": [
                {
                    "id": d.id, "vendor": d.vendor, "model": d.model,
                    "tier": d.tier, "vram_gb": d.vram_gb,
                    "available_gb": d.available_gb, "util_pct": d.utilization_pct,
                }
                for d in self.devices
            ],
            "routing_policy": self.routing_policy,
        }
