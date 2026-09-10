"""
OSINT external docking registry.

SPATIAL ROLE (Nexus/Park/Aorta)
--------------------------------
External open-source OSINT / threat-intel / verification toolchains that plug
into the NSE platform. They are NOT internal molecules: they mount at the
Aorta's outer vessel (L5 ingress/egress + L4 knowledge store) and at the
C6 docking points (L8 verifier backend, self-improving coding agent).

Each entry follows the SAME uniform contract as the C6 docking stubs:
- ``slug``       : GitHub repo (owner/name)
- ``license``    : detected license (None = verify before wiring)
- ``molecule``   : the NSE molecule it binds to
- ``role``       : what it provides to that molecule
- ``aorta_fqdn`` : egress host (added to k8s/nse-aorta-egress.yaml whitelist)
- ``stars_verified`` : live star count (GitHub API, 2026-09-10) when known
- ``available``  : False until the repo is cloned & wired
- ``dock()``     : raise NotImplementedError while stubbed (loud, not silent)

Star counts marked ``stars_verified`` are LIVE-verified via the GitHub API on
2026-09-10; entries without that field are well-known upstream toolchains
whose slug was not re-verified in this pass.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class OSINTDock:
    slug: str
    license: Optional[str]
    molecule: str
    role: str
    aorta_fqdn: Optional[str] = None
    stars_verified: Optional[int] = None
    available: bool = False

    def dock(self) -> Optional[Callable[..., Any]]:
        """Loud mount point; raises while the stub is in place (C6 contract)."""
        raise NotImplementedError(
            f"{self.slug!r} OSINT docking point is empty; clone it, wire "
            f"{self.molecule}, and set available=True before calling dock()."
        )


# ----------------------------------------------------------------- registry
REGISTRY: list[OSINTDock] = [
    # --- threat-intel knowledge (bind L4 + L5) ---------------------------
    OSINTDock(
        slug="OpenCTI-Platform/opencti",
        license="NOASSERTION",          # platform: verify per-component
        molecule="L4 KnowledgeDataLayer / L5 IntegrationAPIGateway",
        role="STIX/TAXII threat-intel graph: feeds the vector/graph store (L4) "
             "and ingests via the gateway (L5).",
        aorta_fqdn="opencti.internal:8080",
        stars_verified=9919,
    ),
    OSINTDock(
        slug="MISP/MISP",
        license="AGPL-3.0",
        molecule="L4 KnowledgeDataLayer / L5 IntegrationAPIGateway",
        role="Open threat-intel sharing (events/attributes) -> L4 store + L5 pull.",
        aorta_fqdn="misp.internal",
        stars_verified=6516,
    ),
    OSINTDock(
        slug="intelowlproject/IntelOwl",
        license="AGPL-3.0",
        molecule="L5 IntegrationAPIGateway",
        role="Multi-analyser orchestration: L5 dispatches lookups to analyzers "
             "and writes results back to L4.",
        aorta_fqdn="intelowl.internal",
        stars_verified=4705,
    ),
    # --- active OSINT collection (bind L5 egress) ------------------------
    OSINTDock(
        slug="smokroot/spiderfoot",
        license="GPL-3.0",
        molecule="L5 IntegrationAPIGateway",
        role="Passive OSINT spidering (DNS, whois, social, leaks). Runs as an "
             "external Aorta egress target.",
        aorta_fqdn="spiderfoot.internal:5001",
    ),
    # --- verification backend (C6 docking: verus) ------------------------
    OSINTDock(
        slug="verus-lang/verus",
        license="MIT",
        molecule="verus/ (C6 docking) -> L8 VerificationProofEngine",
        role="Formal verifier backend: can back L8 proof receipts with machine-"
             "checked invariants instead of heuristics only.",
        stars_verified=3005,
    ),
    # --- self-improving coding agent (C6 docking) -----------------------
    OSINTDock(
        slug="All-Hands-AI/OpenHands",
        license="MIT",
        molecule="self_improving_coding_agent/ (C6 docking) -> L7 CodeEvolutionEngine",
        role="Coding-agent harness: the ECC mount point; feeds L7 evolution loop "
             "with agent-generated patches.",
        stars_verified=87159,
    ),
]

NAME: str = "osint"
AVAILABLE: bool = False  # no OSINT repo is wired yet
ALL: list[OSINTDock] = REGISTRY


def dock(slug: str) -> Optional[Callable[..., Any]]:
    """Look up and mount one OSINT dock by slug (raises while stubbed)."""
    for d in ALL:
        if d.slug == slug:
            return d.dock()
    raise KeyError(f"unknown OSINT docking point: {slug!r}")


__all__ = [
    "OSINTDock", "REGISTRY", "ALL", "NAME", "AVAILABLE", "dock",
]
