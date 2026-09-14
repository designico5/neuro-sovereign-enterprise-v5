"""
Neuro-Sovereign Enterprise v5.0-SYMBIOSIS
=========================================
Top-level package for the 17-Layer Neuro-Symbolic Sovereign AI
Operations Platform. Built as an Enterprise Governance & Sovereignty
layer on top of the ECC (affaan-m/ECC) Agent Harness.

Layer Map:
  1.  Energy Feedback         (energy)
  2.  Compute Silicon         (compute)
  3.  Infrastructure IaC      (infra)
  4.  Data Knowledge          (data)
  5.  Integration API         (integration)
  6.  Execution Sandbox       (cognitive)
  7.  Code Evolution          (evolution)
  8.  Verification Proof      (verification)
  9.  Cognition Neuro-Symbolic(cognition_plus)
  10. Orchestration Swarm     (swarm)
  11. DAO Governance          (dao)
  12. Vision Goals            (vision)
  13. Strategy Market         (strategy)
  14. Governance Compliance   (governance)
  15. Ethos Identity          (ethos)
  16. GeoPolitical Router     (geo)
  17. Legal Sovereignty       (legal)

Quickstart:
    from neurosovereign import NSEPlatform
    platform = NSEPlatform()
    await platform.start()
"""

from __future__ import annotations

import os
import sys
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .version import __version__

logger = logging.getLogger(__name__)

__all__ = [
    "__version__",
    "NSEPlatform",
    "LayerStatus",
    "PlatformConfig",
]


@dataclass(slots=True)
class LayerStatus:
    """Runtime status of a single NSE layer."""

    layer_id: int
    name: str
    enabled: bool = True
    initialized: bool = False
    healthy: Optional[bool] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass(slots=True)
class PlatformConfig:
    """Typed configuration for the NSE platform.

    Values can be overridden via env variables (uppercase, NSE_ prefixed):
        NSE_ENVIRONMENT=production
        NSE_LOG_LEVEL=INFO
        NSE_DATA_DIR=./state
    """

    environment: str = field(
        default_factory=lambda: os.getenv("NSE_ENVIRONMENT", "development")
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("NSE_LOG_LEVEL", "INFO")
    )
    data_dir: str = field(
        default_factory=lambda: os.getenv("NSE_DATA_DIR", "./state")
    )
    enable_layer_1_energy: bool = True
    enable_layer_2_compute: bool = True
    enable_layer_3_infra: bool = True
    enable_layer_4_data: bool = True
    enable_layer_5_integration: bool = True
    enable_layer_6_cognitive: bool = True
    enable_layer_7_evolution: bool = True
    enable_layer_8_verification: bool = True
    enable_layer_9_cognition_plus: bool = True
    enable_layer_10_swarm: bool = True
    enable_layer_11_dao: bool = True
    enable_layer_12_vision: bool = True
    enable_layer_13_strategy: bool = True
    enable_layer_14_governance: bool = True
    enable_layer_15_ethos: bool = True
    enable_layer_16_geo: bool = True
    enable_layer_17_legal: bool = True
    use_ecc_harness: bool = field(
        default_factory=lambda: os.getenv("NSE_USE_ECC", "true").lower() == "true"
    )
    ecc_path: str = field(
        default_factory=lambda: os.getenv(
            "NSE_ECC_PATH",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ecc-reference")),
        )
    )


class NSEPlatform:
    """The unified 17-Layer Neuro-Sovereign Enterprise Platform.

    Usage:
        import asyncio
        from neurosovereign import NSEPlatform

        async def main():
            platform = NSEPlatform()
            await platform.start()
            print(platform.health_report())
            await platform.stop()

        asyncio.run(main())
    """

    LAYER_NAMES: Dict[int, str] = {
        1: "Energy Feedback",
        2: "Compute Silicon",
        3: "Infrastructure IaC",
        4: "Data Knowledge",
        5: "Integration API",
        6: "Execution Sandbox (Cognitive)",
        7: "Code Evolution",
        8: "Verification Proof",
        9: "Cognition Neuro-Symbolic",
        10: "Orchestration Swarm",
        11: "DAO Governance",
        12: "Vision Goals",
        13: "Strategy Market",
        14: "Governance Compliance",
        15: "Ethos Identity",
        16: "GeoPolitical Router",
        17: "Legal Sovereignty",
    }

    def __init__(self, config: Optional[PlatformConfig] = None) -> None:
        self.config = config or PlatformConfig()
        self._layers: Dict[int, LayerStatus] = {
            lid: LayerStatus(layer_id=lid, name=name)
            for lid, name in self.LAYER_NAMES.items()
        }
        self._layer_implementations: Dict[int, Any] = {}
        self._started = False
        self._configure_logging()

    # ------------------------------------------------------------------ utils
    def _configure_logging(self) -> None:
        level = getattr(logging, str(self.config.log_level).upper(), logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            fmt = logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
            )
            handler.setFormatter(fmt)
            logger.addHandler(handler)
        logger.setLevel(level)
        logger.info(
            "Neuro-Sovereign Enterprise v%s | env=%s | ecc=%s",
            __version__,
            self.config.environment,
            "ENABLED" if self.config.use_ecc_harness else "STANDALONE",
        )

    # ---------------------------------------------------------------- lifecycle
    async def start(self) -> "NSEPlatform":
        """Start all 17 layers in dependency order."""

        if self._started:
            logger.warning("Platform already started")
            return self

        self._ensure_dirs()
        await self._start_layer_1_energy()
        await self._start_layer_2_compute()
        await self._start_layer_3_infra()
        await self._start_layer_4_data()
        await self._start_layer_5_integration()
        await self._start_layer_6_cognitive()
        await self._start_layer_7_evolution()
        await self._start_layer_8_verification()
        await self._start_layer_9_cognition_plus()
        await self._start_layer_10_swarm()
        await self._start_layer_11_dao()
        await self._start_layer_12_vision()
        await self._start_layer_13_strategy()
        await self._start_layer_14_governance()
        await self._start_layer_15_ethos()
        await self._start_layer_16_geo()
        await self._start_layer_17_legal()
        self._started = True
        logger.info("All 17 NSE layers started successfully")
        return self

    async def stop(self) -> None:
        """Gracefully shut the platform down."""
        for lid in sorted(self._layers, reverse=True):
            status = self._layers[lid]
            status.initialized = False
            status.healthy = None
        self._started = False
        logger.info("Neuro-Sovereign Platform stopped")

    def _ensure_dirs(self) -> None:
        os.makedirs(self.config.data_dir, exist_ok=True)
        for sub in ("ledger", "sbom", "wallets", "backups"):
            os.makedirs(os.path.join(self.config.data_dir, sub), exist_ok=True)

    # ------------------------------------------------------------- Layer boots
    async def _start_layer_1_energy(self) -> None:
        from .layers.layer_1_energy import EnergyFeedbackEngine

        if not self.config.enable_layer_1_energy:
            self._layers[1].enabled = False
            return
        impl = EnergyFeedbackEngine(self.config)
        await impl.initialize()
        self._layer_implementations[1] = impl
        self._layers[1].initialized = True
        self._layers[1].healthy = True
        self._layers[1].metrics = impl.metrics()

    async def _start_layer_2_compute(self) -> None:
        from .layers.layer_2_compute import ComputeSiliconManager

        if not self.config.enable_layer_2_compute:
            self._layers[2].enabled = False
            return
        impl = ComputeSiliconManager(self.config)
        await impl.initialize()
        self._layer_implementations[2] = impl
        self._layers[2].initialized = True
        self._layers[2].healthy = True
        self._layers[2].metrics = impl.metrics()

    async def _start_layer_3_infra(self) -> None:
        from .layers.layer_3_infra import InfrastructureManager

        if not self.config.enable_layer_3_infra:
            self._layers[3].enabled = False
            return
        impl = InfrastructureManager(self.config)
        await impl.initialize()
        self._layer_implementations[3] = impl
        self._layers[3].initialized = True
        self._layers[3].healthy = True
        self._layers[3].metrics = impl.metrics()

    async def _start_layer_4_data(self) -> None:
        from .layers.layer_4_data import KnowledgeDataLayer

        if not self.config.enable_layer_4_data:
            self._layers[4].enabled = False
            return
        impl = KnowledgeDataLayer(self.config)
        await impl.initialize()
        self._layer_implementations[4] = impl
        self._layers[4].initialized = True
        self._layers[4].healthy = True
        self._layers[4].metrics = impl.metrics()

    async def _start_layer_5_integration(self) -> None:
        from .layers.layer_5_integration import IntegrationAPIGateway

        if not self.config.enable_layer_5_integration:
            self._layers[5].enabled = False
            return
        impl = IntegrationAPIGateway(self.config)
        await impl.initialize()
        self._layer_implementations[5] = impl
        self._layers[5].initialized = True
        self._layers[5].healthy = True
        self._layers[5].metrics = impl.metrics()

    async def _start_layer_6_cognitive(self) -> None:
        from .layers.layer_6_cognitive import SafeExecutionSandbox

        if not self.config.enable_layer_6_cognitive:
            self._layers[6].enabled = False
            return
        impl = SafeExecutionSandbox(self.config)
        await impl.initialize()
        self._layer_implementations[6] = impl
        self._layers[6].initialized = True
        self._layers[6].healthy = True
        self._layers[6].metrics = impl.metrics()

    async def _start_layer_7_evolution(self) -> None:
        from .layers.layer_7_evolution import CodeEvolutionEngine

        if not self.config.enable_layer_7_evolution:
            self._layers[7].enabled = False
            return
        impl = CodeEvolutionEngine(self.config)
        await impl.initialize()
        self._layer_implementations[7] = impl
        self._layers[7].initialized = True
        self._layers[7].healthy = True
        self._layers[7].metrics = impl.metrics()

    async def _start_layer_8_verification(self) -> None:
        from .layers.layer_8_verification import VerificationProofEngine

        if not self.config.enable_layer_8_verification:
            self._layers[8].enabled = False
            return
        impl = VerificationProofEngine(self.config)
        await impl.initialize()
        self._layer_implementations[8] = impl
        self._layers[8].initialized = True
        self._layers[8].healthy = True
        self._layers[8].metrics = impl.metrics()

    async def _start_layer_9_cognition_plus(self) -> None:
        from .layers.layer_9_cognition import NeuroSymbolicEngine

        if not self.config.enable_layer_9_cognition_plus:
            self._layers[9].enabled = False
            return
        impl = NeuroSymbolicEngine(self.config)
        await impl.initialize()
        self._layer_implementations[9] = impl
        self._layers[9].initialized = True
        self._layers[9].healthy = True
        self._layers[9].metrics = impl.metrics()

    async def _start_layer_10_swarm(self) -> None:
        from .layers.layer_10_swarm import OrchestrationSwarm

        if not self.config.enable_layer_10_swarm:
            self._layers[10].enabled = False
            return
        impl = OrchestrationSwarm(self.config)
        await impl.initialize()
        self._layer_implementations[10] = impl
        self._layers[10].initialized = True
        self._layers[10].healthy = True
        self._layers[10].metrics = impl.metrics()

    async def _start_layer_11_dao(self) -> None:
        from .layers.layer_11_dao import DAOGovernanceEngine

        if not self.config.enable_layer_11_dao:
            self._layers[11].enabled = False
            return
        impl = DAOGovernanceEngine(self.config)
        await impl.initialize()
        self._layer_implementations[11] = impl
        self._layers[11].initialized = True
        self._layers[11].healthy = True
        self._layers[11].metrics = impl.metrics()

    async def _start_layer_12_vision(self) -> None:
        from .layers.layer_12_vision import VisionAndGoals

        if not self.config.enable_layer_12_vision:
            self._layers[12].enabled = False
            return
        impl = VisionAndGoals(self.config)
        await impl.initialize()
        self._layer_implementations[12] = impl
        self._layers[12].initialized = True
        self._layers[12].healthy = True
        self._layers[12].metrics = impl.metrics()

    async def _start_layer_13_strategy(self) -> None:
        from .layers.layer_13_strategy import StrategyMarketEngine

        if not self.config.enable_layer_13_strategy:
            self._layers[13].enabled = False
            return
        impl = StrategyMarketEngine(self.config)
        await impl.initialize()
        self._layer_implementations[13] = impl
        self._layers[13].initialized = True
        self._layers[13].healthy = True
        self._layers[13].metrics = impl.metrics()

    async def _start_layer_14_governance(self) -> None:
        from .layers.layer_14_governance import ComplianceGovernance

        if not self.config.enable_layer_14_governance:
            self._layers[14].enabled = False
            return
        impl = ComplianceGovernance(self.config)
        await impl.initialize()
        self._layer_implementations[14] = impl
        self._layers[14].initialized = True
        self._layers[14].healthy = True
        self._layers[14].metrics = impl.metrics()

    async def _start_layer_15_ethos(self) -> None:
        from .layers.layer_15_ethos import EthosIdentityLayer

        if not self.config.enable_layer_15_ethos:
            self._layers[15].enabled = False
            return
        impl = EthosIdentityLayer(self.config)
        await impl.initialize()
        self._layer_implementations[15] = impl
        self._layers[15].initialized = True
        self._layers[15].healthy = True
        self._layers[15].metrics = impl.metrics()

    async def _start_layer_16_geo(self) -> None:
        from .layers.layer_16_geo import GeoPoliticalRouter

        if not self.config.enable_layer_16_geo:
            self._layers[16].enabled = False
            return
        impl = GeoPoliticalRouter(self.config)
        await impl.initialize()
        self._layer_implementations[16] = impl
        self._layers[16].initialized = True
        self._layers[16].healthy = True
        self._layers[16].metrics = impl.metrics()

    async def _start_layer_17_legal(self) -> None:
        from .layers.layer_17_legal import LegalSovereigntyEngine

        if not self.config.enable_layer_17_legal:
            self._layers[17].enabled = False
            return
        impl = LegalSovereigntyEngine(self.config)
        await impl.initialize()
        self._layer_implementations[17] = impl
        self._layers[17].initialized = True
        self._layers[17].healthy = True
        self._layers[17].metrics = impl.metrics()

    # ---------------------------------------------------------------- public
    def get_layer(self, layer_id: int) -> Optional[Any]:
        """Return the concrete implementation of a layer."""
        return self._layer_implementations.get(layer_id)

    def health_report(self) -> Dict[str, Any]:
        """Human + machine readable status of every layer."""
        total = len(self._layers)
        initialized = sum(1 for s in self._layers.values() if s.initialized)
        healthy = sum(1 for s in self._layers.values() if s.healthy is True)
        disabled = sum(1 for s in self._layers.values() if not s.enabled)
        percentage = int((initialized / max(total - disabled, 1)) * 100)
        return {
            "platform": "Neuro-Sovereign Enterprise",
            "version": __version__,
            "environment": self.config.environment,
            "started": self._started,
            "completion_percentage": percentage,
            "totals": {
                "layers_total": total,
                "layers_initialized": initialized,
                "layers_healthy": healthy,
                "layers_disabled": disabled,
            },
            "layers": [
                {
                    "id": s.layer_id,
                    "name": s.name,
                    "enabled": s.enabled,
                    "initialized": s.initialized,
                    "healthy": s.healthy,
                    "error": s.error,
                    "metrics": s.metrics,
                }
                for s in self._layers.values()
            ],
        }


def _entrypoint() -> None:
    """`nse` CLI bootstrap."""
    from .cli import app

    app()


if __name__ == "__main__":
    _entrypoint()
