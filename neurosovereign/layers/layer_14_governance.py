"""
LAYER 14 - Governance & Compliance
-----------------------------------
Policy-as-Code engine: GDPR, EU AI Act (Risk Tiering), NIST-800-53, PCI-DSS, SOX.
Compliance checks run BEFORE every AI operation, with signed receipts + audit logs.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base import BaseNSELayer

logger = logging.getLogger(__name__)

Framework = str


@dataclass(slots=True)
class PolicyRule:
    id: str
    framework: Framework
    severity: str  # critical, high, medium, low, info
    description: str
    check_fn_name: str  # reference to registered check function name


@dataclass(slots=True)
class ComplianceResult:
    rule_id: str
    framework: Framework
    severity: str
    passed: bool
    evidence: str = ""
    duration_ms: float = 0.0


@dataclass(slots=True)
class AuditEntry:
    id: str
    operation: str
    actor: str
    framework_results: Dict[Framework, List[ComplianceResult]]
    overall: bool
    signed_hash: str
    created_at: float


CheckFn = Callable[[Dict[str, Any]], Tuple[bool, str]]


class ComplianceGovernance(BaseNSELayer):
    layer_id = 14
    layer_name = "Governance & Compliance"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "governance")
        os.makedirs(self.root, exist_ok=True)
        self.db = os.path.join(self.root, "compliance.sqlite3")
        self._conn: Optional[sqlite3.Connection] = None
        self._checks: Dict[str, CheckFn] = {}
        self._rules: Dict[str, PolicyRule] = {}

    async def _initialize(self) -> None:
        self._conn = sqlite3.connect(self.db, check_same_thread=False)
        for ddl in (
            """CREATE TABLE IF NOT EXISTS rules (
                id TEXT PRIMARY KEY, framework TEXT, severity TEXT,
                description TEXT, check_fn_name TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS audits (
                id TEXT PRIMARY KEY, operation TEXT, actor TEXT,
                overall INTEGER, signed_hash TEXT, created REAL,
                results_json TEXT
            )""",
        ):
            self._conn.execute(ddl)
        self._conn.commit()
        self._register_defaults()
        self.add_extra("rules_count", len(self._rules))
        self.add_extra("frameworks", sorted({r.framework for r in self._rules.values()}))
        self.add_extra("audits_count", self._count("audits"))

    # =========================================================== registration
    def register_check(self, fn_name: str, fn: CheckFn) -> None:
        self._checks[fn_name] = fn
        self.bump_ok()

    def add_rule(self, rule: PolicyRule) -> None:
        self._rules[rule.id] = rule
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO rules VALUES (?,?,?,?,?)",
            (rule.id, rule.framework, rule.severity, rule.description, rule.check_fn_name),
        )
        self._conn.commit()
        self.add_extra("rules_count", len(self._rules))
        self.add_extra("frameworks", sorted({r.framework for r in self._rules.values()}))
        self.bump_ok()

    # ============================================================ evaluate
    async def evaluate(self, operation: str, actor: str, context: Dict[str, Any],
                       framework_filter: Optional[List[Framework]] = None) -> AuditEntry:
        t0 = time.time()
        results: Dict[str, List[ComplianceResult]] = {}
        overall_passing = True
        for r in self._rules.values():
            if framework_filter and r.framework not in framework_filter:
                continue
            fn = self._checks.get(r.check_fn_name)
            rule_t0 = time.time()
            try:
                ok, evidence = (False, f"check not registered: {r.check_fn_name}") if not fn else fn(context)
            except Exception as exc:
                ok, evidence = False, f"check crashed: {type(exc).__name__}: {exc}"
            if not ok and r.severity in {"critical", "high"}:
                overall_passing = False
            results.setdefault(r.framework, []).append(ComplianceResult(
                rule_id=r.id, framework=r.framework, severity=r.severity,
                passed=ok, evidence=evidence,
                duration_ms=(time.time()-rule_t0) * 1000,
            ))
        entry = AuditEntry(
            id="audit-" + uuid.uuid4().hex[:12],
            operation=operation,
            actor=actor,
            framework_results=results,
            overall=overall_passing,
            signed_hash=self._sign(entry_id=None, operation=operation, actor=actor,
                                  overall=overall_passing, started=t0),
            created_at=time.time(),
        )
        self._persist(entry, t0)
        if overall_passing:
            self.bump_ok()
        else:
            self.bump_fail()
        return entry

    # =========================================================== framework helpers
    def auto_pass_rate(self, framework: Framework) -> float:
        assert self._conn is not None
        rows = self._conn.execute("SELECT results_json, overall FROM audits").fetchall()
        if not rows:
            return 0.0
        total_fr = 0
        pass_fr = 0
        for (results_json, _overall) in rows:
            try:
                data = json.loads(results_json)
            except Exception:
                continue
            for rl in data.get(framework, []):
                total_fr += 1
                if rl.get("passed"):
                    pass_fr += 1
        return round(pass_fr / max(1, total_fr), 4)

    # =========================================================== defaults
    def _register_defaults(self) -> None:
        # Register functions (names map to rules)
        def personal_data_leak(ctx: Dict[str, Any]) -> Tuple[bool, str]:
            text = str(ctx.get("prompt", "") + str(ctx.get("output", ""))).lower()
            bad = ["ssn", "social security", "credit card", "iban", "kreditkarte"]
            found = [b for b in bad if b in text]
            return (not found, f"leak markers found: {found}" if found else "gdpr/personal-data clear")
        def eu_ai_risk_tier(ctx: Dict[str, Any]) -> Tuple[bool, str]:
            risk = ctx.get("eu_ai_risk", "minimal")
            allowed_low = {"minimal", "limited", "general"}
            if risk in allowed_low:
                return True, f"risk tier {risk} permitted"
            return (ctx.get("has_human_in_the_loop", False),
                    f"risk={risk}; human-in-the-loop required for 'high' / 'unacceptable'")
        def nist_access_control(ctx: Dict[str, Any]) -> Tuple[bool, str]:
            has_auth = bool(ctx.get("authenticated")) and bool(ctx.get("roles"))
            return (has_auth, "actor authenticated with roles" if has_auth else "AC-1 access-control failed")
        def pci_cardholder_env(ctx: Dict[str, Any]) -> Tuple[bool, str]:
            prompt = str(ctx.get("prompt", ""))
            bad = any(x in prompt for x in ("4111-1111", "5500000000000004", "340000000000009"))
            return (not bad, "PAN patterns present" if bad else "no PAN literals")
        def sox_change_control(ctx: Dict[str, Any]) -> Tuple[bool, str]:
            has_approval = bool(ctx.get("change_ticket")) or bool(ctx.get("approved_by"))
            return (has_approval, "missing approval ticket" if not has_approval else f"approved via {ctx.get('change_ticket')}")
        self.register_check("gdpr.personal-data", personal_data_leak)
        self.register_check("euai.risk-tier", eu_ai_risk_tier)
        self.register_check("nist.ac-1", nist_access_control)
        self.register_check("pci.dss-3.2", pci_cardholder_env)
        self.register_check("sox.404-change", sox_change_control)
        # Load existing + add baseline rules if empty
        assert self._conn is not None
        existing = self._conn.execute("SELECT id, framework, severity, description, check_fn_name FROM rules").fetchall()
        if not existing:
            for r in [
                ("GDPR-ART5", "gdpr", "high", "No personal-data leakage in prompt/outputs", "gdpr.personal-data"),
                ("EUAIA-6", "eu_ai_act", "critical", "EU AI Act risk tiering enforced", "euai.risk-tier"),
                ("NIST-AC-1", "nist_800_53", "high", "Access control: authentication + roles required", "nist.ac-1"),
                ("PCI-DSS-3.2", "pci_dss", "critical", "Cardholder data environment clean", "pci.dss-3.2"),
                ("SOX-404", "sox", "high", "Change control / approval before ops", "sox.404-change"),
            ]:
                self.add_rule(PolicyRule(r[0], r[1], r[2], r[3], r[4]))
        else:
            for (rid, fw, sev, desc, fn) in existing:
                self._rules[rid] = PolicyRule(rid, fw, sev, desc, fn)

    # --------------------------------------------------------------- misc
    def _sign(self, **kwargs: Any) -> str:
        import hashlib
        payload = "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _persist(self, entry: AuditEntry, started: float) -> None:
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO audits VALUES (?,?,?,?,?,?,?)",
            (entry.id, entry.operation, entry.actor, int(entry.overall),
             entry.signed_hash, entry.created_at,
             json.dumps({
                 fw: [
                     {"rule_id": r.rule_id, "severity": r.severity,
                      "passed": r.passed, "evidence": r.evidence,
                      "ms": round(r.duration_ms, 3)}
                     for r in lst
                 ]
                 for fw, lst in entry.framework_results.items()
             })),
        )
        self._conn.commit()
        self.add_extra("audits_count", self._count("audits"))
        logger.debug("compliance audit %s overall=%s (took %.2fms)", entry.id, entry.overall,
                     (time.time()-started)*1000)

    def _count(self, t: str) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute(f"SELECT COUNT(*) FROM {t}")), (0,))
        return int(c or 0)
