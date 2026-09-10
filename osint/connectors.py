"""
OSINT -> Molecule connectors (Nexus-bound).

This module is the bridge between the external OSINT registry
(``osint/__init__.py``) and the internal NSE molecules. It implements
the wiring described in OSINT.md WITHOUT importing any AGPL/GPL tooling
into the core: it only speaks to them as isolated services over the
Aorta egress whitelist (FQDN -> L5 gateway call), and writes results
back through the L4 knowledge store.

Design (spatial):
    external OSINT service  --(Aorta egress, FQDN-whitelisted)-->  L5 gateway
          L5  --(result write)-->  L4 knowledge store  (Park/SQLite)

Nothing here imports third-party OSINT packages. They stay out-of-process;
this keeps the core license-clean. Each connector is a thin function:
it takes the platform, issues the (future) HTTP call stub, and routes
the payload into L4 via the molecule public API only.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from . import ALL, OSINTDock

logger = logging.getLogger(__name__)


class OSINTBindingError(RuntimeError):
    """Raised when a connector is used before its dock() is wired."""


# ----------------------------------------------------------------- helpers
def _by_slug(slug: str) -> OSINTDock:
    for d in ALL:
        if d.slug == slug:
            return d
    raise KeyError(slug)


def _require_available(dock: OSINTDock) -> None:
    if not dock.available:
        raise OSINTBindingError(
            f"{dock.slug} is not wired (available=False). "
            "Clone the service, add its FQDN to the Aorta whitelist, "
            "then flip available=True in osint/__init__.py."
        )


# --------------------------------------------------------------- bindings
def bind_opencti(platform: Any, stix_bundle: Dict[str, Any]) -> str:
    """Ingest a STIX bundle into L4 (knowledge) via the OpenCTI dock."""
    d = _by_slug("OpenCTI-Platform/opencti")
    _require_available(d)
    l4 = platform.get_layer(4)
    chunk = l4.add(
        source="opencti",
        content=stix_bundle.get("description", str(stix_bundle))[:2000],
        meta={"stix_objects": len(stix_bundle.get("objects", []))},
    )
    logger.info("opencti -> L4 chunk=%s", chunk.id)
    return chunk.id


def bind_misp(platform: Any, event: Dict[str, Any]) -> str:
    """Ingest a MISP threat-intel event into L4 (knowledge)."""
    d = _by_slug("MISP/MISP")
    _require_available(d)
    l4 = platform.get_layer(4)
    chunk = l4.add(
        source="misp",
        content=f"MISP event {event.get('id')}: {event.get('info', '')}"[:2000],
        meta={"misp_event_id": event.get("id"), "analysis": event.get("analysis")},
    )
    logger.info("misp -> L4 chunk=%s", chunk.id)
    return chunk.id


def bind_spiderfoot(platform: Any, target: str, findings: Dict[str, Any]) -> str:
    """Store passive SpiderFoot OSINT findings into L4; results came via L5 egress."""
    d = _by_slug("smokroot/spiderfoot")
    _require_available(d)
    l4 = platform.get_layer(4)
    chunk = l4.add(
        source="spiderfoot",
        content=f"OSINT for {target}: {len(findings)} findings",
        meta={"target": target, "finding_count": len(findings)},
    )
    logger.info("spiderfoot -> L4 chunk=%s", chunk.id)
    return chunk.id


def bind_intelowl(platform: Any, analyzers: list, payload: Dict[str, Any]) -> Optional[str]:
    """Dispatch a lookup to IntelOwl analyzers via L5; returns the job handle."""
    d = _by_slug("intelowlproject/IntelOwl")
    _require_available(d)
    # L5 owns the actual HTTP dispatch to the analyzer service (Aorta egress).
    l5 = platform.get_layer(5)
    job = getattr(l5, "dispatch_osint_lookup", None)
    if job is None:
        logger.warning("L5.dispatch_osint_lookup not present; returning None")
        return None
    return job(analyzers=analyzers, payload=payload)


__all__ = [
    "OSINTBindingError",
    "bind_opencti",
    "bind_misp",
    "bind_spiderfoot",
    "bind_intelowl",
]
