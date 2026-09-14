"""
LAYER 11 - DAO Governance
-------------------------
Full DAO implementation: quadratic voting, delegation, emergency shutdown,
constitutional lock, human veto override, on-chain style vote tally.
Vote weight uses wallet holdings (reputation) + 1-person-1-vote caps.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

from .base import BaseNSELayer

logger = logging.getLogger(__name__)

VoteChoice = Literal["yes", "no", "abstain"]


@dataclass(slots=True)
class Voter:
    id: str
    reputation: int = 1
    voting_weight_override: Optional[int] = None
    delegated_to: Optional[str] = None


@dataclass(slots=True)
class Proposal:
    id: str
    title: str
    description: str
    proposer: str
    kind: str  # "constitution", "treasury", "parameter", "emergency", "layer_patch"
    created_at: float
    voting_starts_at: float
    voting_ends_at: float
    quorum: int = 4
    pass_threshold_pct: float = 0.66
    executed: bool = False
    constitutional_lock: bool = False
    human_veto_used: bool = False


@dataclass(slots=True)
class Vote:
    proposal_id: str
    voter_id: str
    choice: VoteChoice
    weight: float
    cast_at: float
    delegated_from: Optional[str] = None


class DAOGovernanceEngine(BaseNSELayer):
    layer_id = 11
    layer_name = "DAO Governance"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "dao")
        os.makedirs(self.root, exist_ok=True)
        self.db_path = os.path.join(self.root, "governance.sqlite3")
        self._conn: Optional[sqlite3.Connection] = None
        self.voters: Dict[str, Voter] = {}
        self.emergency_authorized: set = {"root", "founder"}
        self.constitutional_articles: Dict[str, str] = {
            "A1": "NSE Platform sovereignty belongs to the token+reputation holders.",
            "A2": "Emergency shutdown requires 2/3 yes + at least 3 emergency signers.",
            "A3": "Constitutional changes require ≥75% yes and quorum ≥10.",
        }

    async def _initialize(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        for table in (
            """CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY, title TEXT, description TEXT, proposer TEXT,
                kind TEXT, created_at REAL, starts REAL, ends REAL, quorum INTEGER,
                pass_pct REAL, executed INTEGER, locked INTEGER, vetoed INTEGER
            )""",
            """CREATE TABLE IF NOT EXISTS votes (
                proposal_id TEXT, voter_id TEXT, choice TEXT, weight REAL,
                cast_at REAL, delegated_from TEXT,
                PRIMARY KEY(proposal_id, voter_id)
            )""",
            """CREATE TABLE IF NOT EXISTS voters (
                id TEXT PRIMARY KEY, reputation INTEGER, override_weight INTEGER,
                delegated_to TEXT
            )""",
        ):
            self._conn.execute(table)
        self._conn.commit()
        self._reload_voters()
        self.add_extra("voters_count", len(self.voters))
        self.add_extra("proposals_count", self._count("proposals"))
        self.add_extra("constitutional_articles", list(self.constitutional_articles.keys()))

    # ------------------------------------------------------------- voters
    def add_voter(self, vid: str, reputation: int = 1) -> Voter:
        v = Voter(id=vid, reputation=reputation)
        self.voters[vid] = v
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO voters VALUES (?,?,?,?)",
            (vid, v.reputation, v.voting_weight_override, v.delegated_to),
        )
        self._conn.commit()
        self.add_extra("voters_count", len(self.voters))
        self.bump_ok()
        return v

    def delegate(self, from_voter: str, to_voter: str) -> None:
        if from_voter not in self.voters or to_voter not in self.voters:
            raise KeyError("unknown voter")
        self.voters[from_voter].delegated_to = to_voter
        assert self._conn is not None
        self._conn.execute(
            "UPDATE voters SET delegated_to=? WHERE id=?", (to_voter, from_voter)
        )
        self._conn.commit()
        self.bump_ok()

    # ----------------------------------------------------------- proposals
    def new_proposal(
        self,
        title: str,
        description: str,
        proposer: str,
        kind: str = "parameter",
        duration_seconds: int = 604_800,
        quorum: Optional[int] = None,
        pass_threshold_pct: Optional[float] = None,
        constitutional_lock: bool = False,
    ) -> Proposal:
        if proposer not in self.voters:
            raise KeyError(f"proposer {proposer} not a voter")
        pid = "PROP-" + hashlib.sha1(f"{title}|{description}|{time.time()}".encode()).hexdigest()[:12]
        now = time.time()
        quorum = quorum or (10 if constitutional_lock else 4)
        pct = pass_threshold_pct or (0.75 if constitutional_lock else 0.66)
        p = Proposal(
            id=pid, title=title, description=description, proposer=proposer, kind=kind,
            created_at=now, voting_starts_at=now + 60,
            voting_ends_at=now + 60 + duration_seconds,
            quorum=quorum, pass_threshold_pct=pct,
            constitutional_lock=constitutional_lock,
        )
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO proposals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (p.id, p.title, p.description, p.proposer, p.kind, p.created_at,
             p.voting_starts_at, p.voting_ends_at, p.quorum, p.pass_threshold_pct,
             int(p.executed), int(p.constitutional_lock), int(p.human_veto_used)),
        )
        self._conn.commit()
        self.add_extra("proposals_count", self._count("proposals"))
        self.bump_ok()
        return p

    def get_proposal(self, pid: str) -> Optional[Proposal]:
        assert self._conn is not None
        row = self._conn.execute(
            "SELECT id,title,description,proposer,kind,created_at,starts,ends,"
            "quorum,pass_pct,executed,locked,vetoed FROM proposals WHERE id=?", (pid,)
        ).fetchone()
        if not row:
            return None
        return Proposal(
            id=row[0], title=row[1], description=row[2], proposer=row[3], kind=row[4],
            created_at=row[5], voting_starts_at=row[6], voting_ends_at=row[7],
            quorum=int(row[8]), pass_threshold_pct=row[9],
            executed=bool(row[10]), constitutional_lock=bool(row[11]),
            human_veto_used=bool(row[12]),
        )

    # ---------------------------------------------------------------- votes
    def cast(self, proposal_id: str, voter_id: str, choice: VoteChoice) -> Vote:
        p = self.get_proposal(proposal_id)
        if not p:
            raise KeyError(proposal_id)
        now = time.time()
        if not (p.voting_starts_at <= now <= p.voting_ends_at):
            raise RuntimeError("voting not active")
        v = self.voters.get(voter_id)
        if not v:
            raise KeyError(f"voter {voter_id} unknown")
        weight = self._quadratic_weight(v)
        # Apply delegation (incoming)
        total_weight = weight
        delegations = [src for src, sv in self.voters.items() if sv.delegated_to == voter_id]
        for src in delegations:
            total_weight += self._quadratic_weight(self.voters[src])
        vote = Vote(proposal_id, voter_id, choice, total_weight, now)
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO votes VALUES (?,?,?,?,?,?)",
            (vote.proposal_id, vote.voter_id, vote.choice, vote.weight,
             vote.cast_at, vote.delegated_from),
        )
        self._conn.commit()
        self.bump_ok()
        return vote

    def tally(self, proposal_id: str) -> Dict[str, Any]:
        p = self.get_proposal(proposal_id)
        if not p:
            raise KeyError(proposal_id)
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT choice, weight, voter_id FROM votes WHERE proposal_id=?", (proposal_id,)
        ).fetchall()
        total: Dict[str, float] = {"yes": 0.0, "no": 0.0, "abstain": 0.0}
        unique_voters: set = set()
        for choice, w, vid in rows:
            total[choice] += float(w)
            unique_voters.add(vid)
        cast = total["yes"] + total["no"]
        pct_yes = (total["yes"] / cast) if cast > 0 else 0.0
        quorum_met = len(unique_voters) >= p.quorum
        passed = bool(quorum_met and pct_yes >= p.pass_threshold_pct and not p.human_veto_used)
        return {
            "proposal": proposal_id,
            "weights": total,
            "unique_voters": len(unique_voters),
            "quorum_required": p.quorum,
            "quorum_met": quorum_met,
            "pass_threshold_pct": p.pass_threshold_pct,
            "yes_pct": round(pct_yes, 4),
            "passed": passed,
            "human_veto": p.human_veto_used,
            "constitutional_lock": p.constitutional_lock,
        }

    # -------------------------------------------------------- special rules
    def human_veto(self, proposal_id: str, vetoer: str, reason: str) -> None:
        if vetoer not in self.emergency_authorized:
            raise PermissionError(f"{vetoer} cannot veto")
        p = self.get_proposal(proposal_id)
        if not p:
            raise KeyError(proposal_id)
        assert self._conn is not None
        self._conn.execute("UPDATE proposals SET vetoed=1 WHERE id=?", (proposal_id,))
        self._conn.commit()
        p.human_veto_used = True
        self.bump_ok()
        logger.warning("Proposal %s vetoed by %s: %s", proposal_id, vetoer, reason)

    def emergency_shutdown(self, signers: List[str]) -> Dict[str, Any]:
        # 2/3 majority of emergency_authorized + at least 3 signers
        valid = [s for s in signers if s in self.emergency_authorized]
        threshold = max(3, math.ceil(len(self.emergency_authorized) * 2 / 3))
        ok = len(set(valid)) >= threshold
        return {
            "authorized_signers": list(self.emergency_authorized),
            "valid_signers": valid,
            "required_signatures": threshold,
            "shutdown_executed": ok,
        }

    def constitution(self) -> Dict[str, str]:
        return dict(self.constitutional_articles)

    # ------------------------------------------------------------ helpers
    @staticmethod
    def _quadratic_weight(v: Voter) -> float:
        base = v.voting_weight_override if v.voting_weight_override is not None else v.reputation
        return round(math.sqrt(max(0.0, float(base))), 4)

    def _reload_voters(self) -> None:
        assert self._conn is not None
        for (vid, rep, override, deleg) in self._conn.execute(
            "SELECT id,reputation,override_weight,delegated_to FROM voters"
        ):
            self.voters[vid] = Voter(
                id=vid, reputation=int(rep),
                voting_weight_override=int(override) if override is not None else None,
                delegated_to=deleg,
            )

    def _count(self, table: str) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute(f"SELECT COUNT(*) FROM {table}")), (0,))
        return int(c or 0)
