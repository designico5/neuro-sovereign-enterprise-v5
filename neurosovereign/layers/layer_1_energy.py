"""
LAYER 1 - Energy Feedback
-------------------------
Tracks energy consumption, carbon intensity and cost-optimized workload steering.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EnergyReading:
    timestamp: float
    watts: float
    cost_per_kwh: float
    location: str
    renewable_pct: float


class EnergyFeedbackEngine(BaseNSELayer):
    layer_id = 1
    layer_name = "Energy Feedback"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.readings: List[EnergyReading] = []
        self.carbon_ceiling_kwh: float = 10_000.0
        self.preferred_region: str = "eu-west"
        self._sampler_task: Optional[asyncio.Task] = None

    async def _initialize(self) -> None:
        self.add_extra("carbon_ceiling_kwh", self.carbon_ceiling_kwh)
        self.add_extra("preferred_region", self.preferred_region)
        self._sampler_task = asyncio.create_task(self._sampling_loop())

    async def _sampling_loop(self, interval: float = 30.0) -> None:
        try:
            while True:
                self.readings.append(self.sample_once())
                if len(self.readings) > 2880:  # 24h @ 30s
                    self.readings.pop(0)
                self.add_extra("readings_count", len(self.readings))
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    def sample_once(self) -> EnergyReading:
        watts = 250.0
        try:  # pragma: no cover - hardware specific
            import pynvml  # type: ignore

            pynvml.nvmlInit()
            watts = 0.0
            for i in range(pynvml.nvmlDeviceGetCount()):
                h = pynvml.nvmlDeviceGetHandleByIndex(i)
                watts += pynvml.nvmlDeviceGetPowerUsage(h) / 1000.0
        except Exception:
            watts = max(watts, 120.0)
        self.bump_ok()
        return EnergyReading(time.time(), watts, 0.28, self.preferred_region, 0.62)

    def cost_last_hour(self) -> float:
        cutoff = time.time() - 3600
        recent = [r for r in self.readings if r.timestamp >= cutoff] or self.readings[-1:]
        if not recent:
            return 0.0
        avg_w = sum(r.watts for r in recent) / len(recent)
        hours = min(1.0, len(recent) * 30.0 / 3600.0)
        return round((avg_w * hours / 1000.0) * 0.28, 4)

    def recommendations(self) -> Dict[str, Any]:
        cost_hour = self.cost_last_hour()
        month_proj = round(cost_hour * 24.0 * 30.0, 2)
        last = self.readings[-1] if self.readings else None
        renewable = last.renewable_pct if last else 0.0
        return {
            "cost_hour_eur": cost_hour,
            "monthly_projected_eur": month_proj,
            "action": "scale_batch_jobs" if cost_hour > 1.0 else "ok",
            "renewable_ratio": renewable,
            "green_light": renewable >= 0.7,
        }
