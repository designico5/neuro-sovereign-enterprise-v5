"""
LAYER 16 - GeoPolitical Router
-------------------------------
Data-Residency + Jurisdiction-Compliance aware routing engine.

Features:
  - Per-country data residency map (EU/Schrems-II, US, CN, RU, BR LGPD, ...)
  - IP geo lookup + dynamic REROUTING if current region disallows processing
  - Routing policy JSON loaded; but compiled into executable code
  - Jurisdiction conflicts -> governance veto
  - Audit trail of each routed operation
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

from .base import BaseNSELayer

logger = logging.getLogger(__name__)

Jurisdiction = str
DataCategory = Literal["personal", "sensitive", "genetic", "anonymous", "metadata", "contract"]
RoutingDecision = Literal["ALLOW", "QUARANTINE", "DENY", "REROUTE"]


@dataclass(slots=True)
class GeoRule:
    id: str
    source_jurisdiction: Optional[Jurisdiction]
    target_jurisdiction: Optional[Jurisdiction]
    categories: List[DataCategory]
    decision: RoutingDecision
    reroute_to: Optional[str] = None
    requires_human_veto: bool = False


@dataclass(slots=True)
class RouteAudit:
    id: str
    operation: str
    client_ip: str
    source_jurisdiction: str
    target_jurisdiction: str
    categories: List[str]
    decision: RoutingDecision
    matched_rule: Optional[str]
    notes: str = ""
    created_at: float = field(default_factory=time.time)


class GeoPoliticalRouter(BaseNSELayer):
    layer_id = 16
    layer_name = "GeoPolitical Router"

    # Countries in each jurisdiction block
    DEFAULT_JURISDICTION_MAP: Dict[Jurisdiction, List[str]] = {
        "EU": ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
              "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT",
              "RO", "SK", "SI", "ES", "SE"],
        "EEA_PLUS": ["IS", "LI", "NO", "CH"],
        "US": ["US"],
        "UK": ["GB"],
        "BR": ["BR"],
        "CN": ["CN"],
        "RU": ["RU"],
        "IN": ["IN"],
        "JP": ["JP"],
        "KR": ["KR"],
        "AU": ["AU"],
        "CA": ["CA"],
    }

    # A small deterministic CIDR->country map for demo environments;
    # production deployments should connect to a paid geo DB (MaxMind/IP2Location)
    DEMO_IP_MAP: List[Tuple[str, str]] = [
        ("192.168.0.0/16", "DE"),
        ("10.0.0.0/8", "US"),
        ("172.16.0.0/12", "FR"),
        ("127.0.0.1/32", "DE"),
        ("::1/128", "DE"),
    ]

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "geo")
        os.makedirs(self.root, exist_ok=True)
        self.db_path = os.path.join(self.root, "geo.sqlite3")
        self._conn: Optional[sqlite3.Connection] = None
        self.rules: List[GeoRule] = []
        self.conflicts: List[str] = []
        self.geodb_provider: str = os.getenv("NSE_GEO_PROVIDER", "demo")
        self.preferred_jurisdiction: Jurisdiction = os.getenv("NSE_PREFERRED_JURISDICTION", "EU")

    async def _initialize(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        for ddl in (
            """CREATE TABLE IF NOT EXISTS rules (
                id TEXT PRIMARY KEY, src TEXT, dst TEXT,
                categories_json TEXT, decision TEXT, reroute TEXT, veto INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS audits (
                id TEXT PRIMARY KEY, operation TEXT, client_ip TEXT,
                src TEXT, dst TEXT, cat_json TEXT, decision TEXT,
                matched_rule TEXT, notes TEXT, created REAL
            )""",
        ):
            self._conn.execute(ddl)
        self._conn.commit()
        self._reload_rules()
        if not self.rules:
            self._install_default_rules()
        self.add_extra("jurisdictions", list(self.DEFAULT_JURISDICTION_MAP.keys()))
        self.add_extra("rules_count", len(self.rules))
        self.add_extra("geodb_provider", self.geodb_provider)
        self.add_extra("preferred", self.preferred_jurisdiction)
        self.add_extra("audits_count", self._count("audits"))

    # ----------------------------------------------------------- rule mgmt
    def add_rule(self, rule: GeoRule) -> None:
        self.rules.append(rule)
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO rules VALUES (?,?,?,?,?,?,?)",
            (rule.id, rule.source_jurisdiction, rule.target_jurisdiction,
             json.dumps(rule.categories), rule.decision, rule.reroute_to,
             int(rule.requires_human_veto)),
        )
        self._conn.commit()
        self.add_extra("rules_count", len(self.rules))
        self.bump_ok()

    def _install_default_rules(self) -> None:
        # (1) EU→US transfers: Schrems-II → REROUTE to EU unless categories are "anon"/"metadata"
        self.add_rule(GeoRule(
            id="SCHREMS-II-001", source_jurisdiction="EU", target_jurisdiction="US",
            categories=["personal", "sensitive", "genetic", "contract"],
            decision="REROUTE", reroute_to="EU",
        ))
        # (2) No genetic data to RU/CN
        for bad in ("CN", "RU"):
            self.add_rule(GeoRule(
                id=f"GENETIC-EXPORT-{bad}", source_jurisdiction=None, target_jurisdiction=bad,
                categories=["genetic"], decision="DENY",
            ))
        # (3) LGPD BR personal data must stay in BR
        self.add_rule(GeoRule(
            id="LGPD-BR-RESIDENCY", source_jurisdiction="BR", target_jurisdiction=None,
            categories=["personal", "sensitive"], decision="REROUTE", reroute_to="BR",
        ))
        # (4) Everything else (default) → ALLOW within preferred jurisdiction
        self.add_rule(GeoRule(
            id="DEFAULT-INTERNAL", source_jurisdiction=None, target_jurisdiction=self.preferred_jurisdiction,
            categories=["personal", "metadata", "anonymous"], decision="ALLOW",
        ))
        # (5) Cross-jurisdiction unknown → QUARANTINE (requires human review)
        self.add_rule(GeoRule(
            id="DEFAULT-QUARANTINE", source_jurisdiction=None, target_jurisdiction=None,
            categories=["personal", "sensitive", "genetic", "contract"],
            decision="QUARANTINE", requires_human_veto=True,
        ))

    def _reload_rules(self) -> None:
        self.rules = []
        assert self._conn is not None
        for (rid, src, dst, cats, decision, reroute, veto) in self._conn.execute(
            "SELECT id,src,dst,categories_json,decision,reroute,veto FROM rules"
        ):
            self.rules.append(GeoRule(
                id=rid, source_jurisdiction=src, target_jurisdiction=dst,
                categories=json.loads(cats), decision=decision,
                reroute_to=reroute, requires_human_veto=bool(veto),
            ))

    # --------------------------------------------------------------- geo API
    def route(self, operation: str, client_ip: str, target_jurisdiction: str,
              categories: List[DataCategory]) -> RouteAudit:
        """Execute a routing decision, persisting an audit entry."""
        src_jur = self.jurisdiction_for_ip(client_ip)
        matched: Optional[GeoRule] = None
        for r in self.rules:
            src_ok = r.source_jurisdiction is None or r.source_jurisdiction == src_jur
            dst_ok = r.target_jurisdiction is None or r.target_jurisdiction == target_jurisdiction
            cat_ok = any(c in r.categories for c in categories)
            if src_ok and dst_ok and cat_ok:
                matched = r
                break
        decision: RoutingDecision = "ALLOW"
        rerouted_to = None
        notes = ""
        if matched:
            decision = matched.decision
            rerouted_to = matched.reroute_to
            if matched.requires_human_veto:
                self.conflicts.append(f"op={operation} rule={matched.id} needs human sign-off")
                notes = "human_veto_required"
        audit = RouteAudit(
            id="rt-" + uuid.uuid4().hex[:12],
            operation=operation,
            client_ip=client_ip,
            source_jurisdiction=src_jur,
            target_jurisdiction=target_jurisdiction,
            categories=list(categories),
            decision=decision,
            matched_rule=matched.id if matched else None,
            notes=notes,
        )
        if rerouted_to and decision == "REROUTE":
            audit.notes += f" reroute_to={rerouted_to}"
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO audits VALUES (?,?,?,?,?,?,?,?,?,?)",
            (audit.id, audit.operation, audit.client_ip, audit.source_jurisdiction,
             audit.target_jurisdiction, json.dumps(audit.categories), audit.decision,
             audit.matched_rule, audit.notes, audit.created_at),
        )
        self._conn.commit()
        self.add_extra("audits_count", self._count("audits"))
        if decision in {"ALLOW", "REROUTE"}:
            self.bump_ok()
        else:
            self.bump_fail()
        return audit

    def jurisdiction_for_ip(self, ip: str) -> str:
        """Resolve IP → country → jurisdiction.

        Default behaviour:
          - Use a prefix-list-based demo map.
          - If nothing matched -> "UNKNOWN".
        """
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return "UNKNOWN"
        country = None
        for net_cidr, cc in self.DEMO_IP_MAP:
            net = ipaddress.ip_network(net_cidr, strict=False)
            if addr in net:
                country = cc
                break
        if country is None:  # try a quick heuristic based on leading bytes
            oct_a = int(str(addr).split(".")[0]) if addr.version == 4 else None
            if oct_a is not None:
                if 40 <= oct_a <= 60:
                    country = "US"
                elif 80 <= oct_a <= 90:
                    country = "DE"
                else:
                    country = "US"
        for jur, countries in self.DEFAULT_JURISDICTION_MAP.items():
            if country in countries:
                return jur
        return country or "UNKNOWN"

    def country_list(self, jurisdiction: Jurisdiction) -> List[str]:
        return list(self.DEFAULT_JURISDICTION_MAP.get(jurisdiction, []))

    def recent_audits(self, limit: int = 20) -> List[Dict[str, Any]]:
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT id,operation,client_ip,src,dst,cat_json,decision,matched_rule,notes,created "
            "FROM audits ORDER BY created DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            {
                "id": r[0], "operation": r[1], "ip": r[2],
                "src": r[3], "dst": r[4],
                "categories": json.loads(r[5]),
                "decision": r[6], "matched_rule": r[7],
                "notes": r[8], "created_at": r[9],
            }
            for r in rows
        ]

    def _count(self, t: str) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute(f"SELECT COUNT(*) FROM {t}")), (0,))
        return int(c or 0)
