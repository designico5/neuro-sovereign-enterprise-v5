"""
Base class for every NSE layer. All 17 layers inherit from BaseNSELayer.
Ensures consistent initialization, metrics and lifecycle hooks.
"""
from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LayerMetrics:
    ops_total: int = 0
    ops_failed: int = 0
    uptime_seconds: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)


class BaseNSELayer(ABC):
    """Common interface for all 17 NSE layers."""

    layer_id: int
    layer_name: str

    def __init__(self, config: Any) -> None:
        self.config = config
        self._metrics = LayerMetrics()
        self._initialized = False
        self._startup_event = asyncio.Event()

    # ------------------------------------------------------------------ API
    @abstractmethod
    async def _initialize(self) -> None:
        """Concrete layer setup."""

    async def initialize(self) -> None:
        """Template-method: handles logging + metrics around _initialize."""
        logger.info("[L%02d] Initializing %s", self.layer_id, self.layer_name)
        try:
            await self._initialize()
            self._initialized = True
            self._startup_event.set()
            logger.info("[L%02d] ✅ Initialized", self.layer_id)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("[L%02d] ❌ Failed: %s", self.layer_id, exc)
            raise

    def is_initialized(self) -> bool:
        return self._initialized

    def metrics(self) -> Dict[str, Any]:
        return {
            "ops_total": self._metrics.ops_total,
            "ops_failed": self._metrics.ops_failed,
            **self._metrics.extra,
        }

    def bump_ok(self) -> None:
        self._metrics.ops_total += 1

    def bump_fail(self) -> None:
        self._metrics.ops_total += 1
        self._metrics.ops_failed += 1

    def add_extra(self, key: str, value: Any) -> None:
        self._metrics.extra[key] = value
