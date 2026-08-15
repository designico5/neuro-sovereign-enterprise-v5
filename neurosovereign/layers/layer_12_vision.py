"""
LAYER 12 - Vision & Goals
--------------------------
Mission, OKRs and Key Results with tracking, auto-derived subtasks, and
attainment probability scoring.
"""
from __future__ import annotations

import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Objective:
    id: str
    title: str
    owner: str
    deadline_epoch: float
    mission_aligned: bool = True
    confidence: float = 0.5


@dataclass(slots=True)
class KeyResult:
    id: str
    objective_id: str
    title: str
    baseline: float
    target: float
    current: float = 0.0
    unit: str = "items"
    weight: float = 1.0


class VisionAndGoals(BaseNSELayer):
    layer_id = 12
    layer_name = "Vision & Goals"

    MISSION = (
        "Build a sovereign, human-aligned, neuro-symbolic enterprise AI platform "
        "that upholds constitutional, ethical, and legal guardrails in every "
        "operation, while continuously improving through evidence-based evolution."
    )

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "vision")
        os.makedirs(self.root, exist_ok=True)
        self.db = os.path.join(self.root, "okr.sqlite3")
        self._conn: Optional[sqlite3.Connection] = None

    async def _initialize(self) -> None:
        self._conn = sqlite3.connect(self.db, check_same_thread=False)
        for ddl in (
            """CREATE TABLE IF NOT EXISTS objectives (
                id TEXT PRIMARY KEY, title TEXT, owner TEXT, deadline REAL,
                aligned INTEGER, confidence REAL
            )""",
            """CREATE TABLE IF NOT EXISTS key_results (
                id TEXT PRIMARY KEY, objective_id TEXT, title TEXT,
                baseline REAL, target REAL, current REAL, unit TEXT, weight REAL
            )""",
        ):
            self._conn.execute(ddl)
        self._conn.commit()
        self.add_extra("objectives", self._count("objectives"))
        self.add_extra("key_results", self._count("key_results"))
        self.add_extra("mission_words", len(self.MISSION.split()))

    # ------------------------------------------------------------------ API
    def mission_statement(self) -> str:
        return self.MISSION

    def add_objective(self, title: str, owner: str, days: int = 90,
                      confidence: float = 0.5) -> Objective:
        oid = "OBJ-" + uuid.uuid4().hex[:8]
        o = Objective(id=oid, title=title, owner=owner,
                      deadline_epoch=time.time() + days * 86400, confidence=confidence)
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO objectives VALUES (?,?,?,?,?,?)",
            (o.id, o.title, o.owner, o.deadline_epoch, int(o.mission_aligned), o.confidence),
        )
        self._conn.commit()
        self.add_extra("objectives", self._count("objectives"))
        self.bump_ok()
        return o

    def add_kr(self, objective_id: str, title: str, baseline: float, target: float,
              unit: str = "items", weight: float = 1.0) -> KeyResult:
        kid = "KR-" + uuid.uuid4().hex[:8]
        kr = KeyResult(id=kid, objective_id=objective_id, title=title,
                       baseline=baseline, target=target, unit=unit, weight=weight)
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO key_results VALUES (?,?,?,?,?,?,?,?)",
            (kr.id, kr.objective_id, kr.title, kr.baseline, kr.target,
             kr.current, kr.unit, kr.weight),
        )
        self._conn.commit()
        self.add_extra("key_results", self._count("key_results"))
        self.bump_ok()
        return kr

    def progress(self, kr_id: str, current: float) -> None:
        assert self._conn is not None
        self._conn.execute("UPDATE key_results SET current=? WHERE id=?", (current, kr_id))
        self._conn.commit()
        self.bump_ok()

    def score_objective(self, obj_id: str) -> Dict[str, Any]:
        rows = self._conn.execute(  # type: ignore[union-attr]
            "SELECT id,baseline,target,current,weight FROM key_results WHERE objective_id=?", (obj_id,)
        ).fetchall()
        if not rows:
            return {"objective": obj_id, "progress": 0.0, "krs": 0}
        total_w = 0.0
        weighted = 0.0
        for _kid, base, target, cur, w in rows:
            span = max(abs(target - base), 1e-9)
            pct = max(0.0, min(1.0, (cur - base) / span))
            weighted += pct * float(w)
            total_w += float(w)
        score = weighted / total_w if total_w else 0.0
        return {"objective": obj_id, "progress": round(score, 4), "krs": len(rows)}

    def dashboard(self) -> List[Dict[str, Any]]:
        out = []
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT id,title,owner,deadline,confidence FROM objectives"
        ).fetchall()
        for oid, title, owner, deadline, conf in rows:
            s = self.score_objective(oid)
            left_days = max(0, int((deadline - time.time()) / 86400))
            out.append({
                "id": oid, "title": title, "owner": owner,
                "progress_pct": s["progress"], "krs": s["krs"],
                "days_left": left_days,
                "confidence": conf,
                "attainment_probability": round(min(1.0, float(conf) * 0.6 + s["progress"] * 0.4), 4),
            })
        return out

    def _count(self, t: str) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute(f"SELECT COUNT(*) FROM {t}")), (0,))
        return int(c or 0)
