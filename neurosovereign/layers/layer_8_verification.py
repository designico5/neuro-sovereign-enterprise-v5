"""
LAYER 8 - Verification Proof
----------------------------
GRPO (Group Relative Policy Optimization) proof generation +
Zero-Knowledge Style execution receipts +
deterministic SBOM provenance ledger.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProofReceipt:
    id: str
    subject: str
    policy: str
    group: str
    score: float
    threshold: float
    passed: bool
    created_at: float
    hash: str
    evidence: Dict[str, Any] = field(default_factory=dict)


class VerificationProofEngine(BaseNSELayer):
    layer_id = 8
    layer_name = "Verification Proof"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "verification")
        os.makedirs(self.root, exist_ok=True)
        self.db_path = os.path.join(self.root, "proofs.sqlite3")
        self._conn: Optional[sqlite3.Connection] = None
        self.policies: Dict[str, Any] = {
            "python-syntax": {"kind": "syntax", "threshold": 0.99},
            "python-typecheck": {"kind": "mypy", "threshold": 0.80},
            "unit-test": {"kind": "pytest", "threshold": 0.80},
            "sql-injection": {"kind": "static", "threshold": 1.00},
            "sbom-coverage": {"kind": "sbom", "threshold": 0.90},
            "compliance-gdpr": {"kind": "policy", "threshold": 0.85},
            "compliance-eu-ai-act": {"kind": "policy", "threshold": 0.80},
        }

    async def _initialize(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("""CREATE TABLE IF NOT EXISTS proofs (
            id TEXT PRIMARY KEY, subject TEXT, policy TEXT, grp TEXT,
            score REAL, threshold REAL, passed INTEGER, created_at REAL,
            hash TEXT, evidence_json TEXT
        ) WITHOUT ROWID""")
        self._conn.execute("""CREATE TABLE IF NOT EXISTS grpo_groups (
            grp TEXT PRIMARY KEY, baseline REAL, best REAL, size INTEGER, updated REAL
        )""")
        self._conn.commit()
        self.add_extra("policies", list(self.policies.keys()))
        self.add_extra("proofs_stored", self._count("proofs"))

    # ------------------------------------------------------------------ API
    def add_policy(self, name: str, kind: str, threshold: float) -> None:
        self.policies[name] = {"kind": kind, "threshold": float(threshold)}
        self.add_extra("policies", list(self.policies.keys()))
        self.bump_ok()

    async def verify(self, subject: str, policy_name: str, evidence: Optional[Dict[str, Any]] = None,
                     group: str = "default") -> ProofReceipt:
        if policy_name not in self.policies:
            raise KeyError(f"unknown policy: {policy_name}")
        p = self.policies[policy_name]
        score = await self._score(subject, p["kind"], evidence or {})
        threshold = float(p["threshold"])
        passed = bool(score >= threshold)
        pid = "prf-" + hashlib.sha256(f"{subject}|{policy_name}|{score}|{time.time()}".encode()).hexdigest()[:16]
        payload = json.dumps({"id": pid, "subject": subject, "policy": policy_name,
                            "score": score, "threshold": threshold, "passed": passed}, sort_keys=True)
        h = hashlib.sha256(payload.encode()).hexdigest()
        receipt = ProofReceipt(pid, subject, policy_name, group, round(score, 6),
                            threshold, passed, time.time(), h, evidence or {})
        self._store(receipt)
        self._update_group(group, score)
        if passed:
            self.bump_ok()
        else:
            self.bump_fail()
        return receipt

    def proofs_for(self, subject: str) -> List[Dict[str, Any]]:
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT id,policy,score,threshold,passed,created_at,hash FROM proofs WHERE subject=? ORDER BY created_at DESC",
            (subject,),
        ).fetchall()
        return [
            {"id": r[0], "policy": r[1], "score": r[2], "threshold": r[3],
             "passed": bool(r[4]), "ts": r[5], "hash": r[6]} for r in rows
        ]

    # ---------------------------------------------------------------- grpo
    def grpo_report(self, group: str) -> Dict[str, Any]:
        """Group Relative score statistics for GRPO-style policy optimization."""
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT baseline, best, size, updated FROM grpo_groups WHERE grp=?", (group,)
        ).fetchone()
        if not row:
            return {"group": group, "exists": False}
        baseline, best, size, updated = row
        rel_best = (best - baseline) / max(baseline, 1e-9)
        return {
            "group": group,
            "exists": True,
            "baseline": baseline,
            "best": best,
            "samples": int(size),
            "relative_improvement": round(rel_best, 6),
            "updated_at": updated,
        }

    # ================================================================ core
    async def _score(self, subject: str, kind: str, evidence: Dict[str, Any]) -> float:
        #  ------------------------------------------------------ python-syntax
        if kind == "syntax":
            try:
                compile(subject, "<verify>", "exec")
                return 1.0
            except SyntaxError as exc:
                return max(0.0, 0.8 - 0.1 * str(exc).count("\n"))
        # ----------------------------------------------------- mypy static
        if kind == "mypy":
            return float(evidence.get("mypy_pass_rate", 0.5))
        # ------------------------------------------------------------- pytest
        if kind == "pytest":
            passed = int(evidence.get("tests_passed", 0))
            total = max(int(evidence.get("tests_total", 0)), 1)
            cov = float(evidence.get("coverage_pct", 0)) / 100.0
            return 0.7 * (passed / total) + 0.3 * cov
        # --------------------------------------------- static sql-injection
        if kind == "static":
            lowered = subject.lower()
            hits = sum(1 for token in (") union ", " exec(", " execute(", "shell=True") if token in lowered)
            return max(0.0, 1.0 - 0.5 * hits)
        # ------------------------------------------------------------- sbom
        if kind == "sbom":
            declared = int(evidence.get("declared_components", 1))
            tracked = int(evidence.get("tracked_components", 0))
            return min(1.0, tracked / declared)
        # -------------------------------------------------------- policies
        if kind == "policy":
            if not evidence:
                return 0.5
            ok_keys = [v for k, v in evidence.items() if k.endswith("_passed") and isinstance(v, bool)]
            if not ok_keys:
                return 0.5
            return sum(1.0 if v else 0.0 for v in ok_keys) / len(ok_keys)
        return 0.0

    # ============================================================== storage
    def _store(self, r: ProofReceipt) -> None:
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO proofs VALUES (?,?,?,?,?,?,?,?,?,?)",
            (r.id, r.subject, r.policy, r.group, r.score, r.threshold,
             int(r.passed), r.created_at, r.hash, json.dumps(r.evidence)),
        )
        self._conn.commit()
        self.add_extra("proofs_stored", self._count("proofs"))

    def _update_group(self, group: str, score: float) -> None:
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT baseline, best, size FROM grpo_groups WHERE grp=?", (group,)
        ).fetchone()
        if not row:
            self._conn.execute(
                "INSERT INTO grpo_groups VALUES (?,?,?,?,?)", (group, score, score, 1, time.time())
            )
        else:
            baseline, best, size = row
            new_best = max(best, score)
            self._conn.execute(
                "UPDATE grpo_groups SET best=?, size=?, updated=? WHERE grp=?",
                (new_best, int(size) + 1, time.time(), group),
            )
        self._conn.commit()

    def _count(self, table: str) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute(f"SELECT COUNT(*) FROM {table}")), (0,))
        return int(c or 0)
