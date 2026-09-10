"""
LAYER 13 - Strategy Market
---------------------------
Prediction markets + strategy candidates. Each strategy proposal is scored by
historical backtest + crowd forecasts + trend analysis.
"""
from __future__ import annotations

import logging
import math
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Strategy:
    id: str
    name: str
    horizon_days: int
    description: str
    backtest_roi_pct: float
    sharpe: float = 0.0
    max_drawdown_pct: float = 0.0
    active: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass(slots=True)
class Forecast:
    strategy_id: str
    trader: str
    direction: int  # +1 long, -1 short / underweight
    confidence_pct: float
    horizon_days: int
    stake: float = 0.0
    cast_at: float = field(default_factory=time.time)


class StrategyMarketEngine(BaseNSELayer):
    layer_id = 13
    layer_name = "Strategy Market"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "strategy")
        os.makedirs(self.root, exist_ok=True)
        self.db = os.path.join(self.root, "market.sqlite3")
        self._conn: Optional[sqlite3.Connection] = None
        self.trading_fee_pct: float = 0.01
        self.open_interest: float = 0.0

    async def _initialize(self) -> None:
        self._conn = sqlite3.connect(self.db, check_same_thread=False)
        for ddl in (
            """CREATE TABLE IF NOT EXISTS strategies (
                id TEXT PRIMARY KEY, name TEXT, horizon INTEGER, description TEXT,
                roi REAL, sharpe REAL, drawdown REAL, active INTEGER, created REAL
            )""",
            """CREATE TABLE IF NOT EXISTS forecasts (
                strategy_id TEXT, trader TEXT, direction INTEGER, confidence REAL,
                horizon INTEGER, stake REAL, cast REAL,
                PRIMARY KEY(strategy_id, trader)
            )""",
        ):
            self._conn.execute(ddl)
        self._conn.commit()
        self.add_extra("strategies", self._count("strategies"))
        self.add_extra("forecasts", self._count("forecasts"))
        self.add_extra("fee_pct", self.trading_fee_pct)

    # ------------------------------------------------------------------ API
    def list_strategy(self, name: str, horizon_days: int, description: str,
                      backtest_roi_pct: float, sharpe: float = 1.0,
                      max_drawdown_pct: float = 10.0) -> Strategy:
        sid = "S-" + uuid.uuid4().hex[:8]
        s = Strategy(id=sid, name=name, horizon_days=max(1, int(horizon_days)),
                     description=description, backtest_roi_pct=backtest_roi_pct,
                     sharpe=sharpe, max_drawdown_pct=max_drawdown_pct)
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO strategies VALUES (?,?,?,?,?,?,?,?,?)",
            (s.id, s.name, s.horizon_days, s.description, s.backtest_roi_pct,
             s.sharpe, s.max_drawdown_pct, int(s.active), s.created_at),
        )
        self._conn.commit()
        self.add_extra("strategies", self._count("strategies"))
        self.bump_ok()
        return s

    def toggle(self, strategy_id: str) -> None:
        assert self._conn is not None
        self._conn.execute(
            "UPDATE strategies SET active=1-active WHERE id=?", (strategy_id,)
        )
        self._conn.commit()
        self.bump_ok()

    def submit_forecast(self, strategy_id: str, trader: str, direction: int,
                        confidence_pct: float, horizon_days: int, stake: float = 0.0) -> Forecast:
        if direction not in {-1, 0, 1}:
            raise ValueError("direction ∈ {-1,0,1}")
        if not (0.0 <= confidence_pct <= 1.0):
            raise ValueError("confidence ∈ [0,1]")
        f = Forecast(strategy_id=strategy_id, trader=trader, direction=direction,
                     confidence_pct=confidence_pct, horizon_days=horizon_days, stake=max(0.0, float(stake)))
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO forecasts VALUES (?,?,?,?,?,?,?)",
            (f.strategy_id, f.trader, f.direction, f.confidence_pct,
             f.horizon_days, f.stake, f.cast_at),
        )
        self._conn.commit()
        self.open_interest += f.stake
        self.add_extra("forecasts", self._count("forecasts"))
        self.add_extra("open_interest", round(self.open_interest, 2))
        self.bump_ok()
        return f

    def aggregate(self, strategy_id: str) -> Dict[str, Any]:
        assert self._conn is not None
        rows = self._conn.execute(
            "SELECT direction, confidence, stake FROM forecasts WHERE strategy_id=?",
            (strategy_id,),
        ).fetchall()
        if not rows:
            return {"strategy": strategy_id, "forecasts": 0, "consensus_score": 0.0, "aggregate_score": 0.0}
        weighted_long = 0.0
        weighted_short = 0.0
        volume = 0.0
        for d, c, s in rows:
            vol = max(1e-9, float(s)) * max(float(c), 0.01)
            if float(d) > 0:
                weighted_long += vol
            elif float(d) < 0:
                weighted_short += vol
            volume += float(s)
        net = (weighted_long - weighted_short) / max(1e-9, weighted_long + weighted_short)
        strat = self._conn.execute(
            "SELECT name, roi, sharpe, drawdown, active FROM strategies WHERE id=?",
            (strategy_id,),
        ).fetchone()
        backtest, sharpe, dd = (strat[1], strat[2], strat[3]) if strat else (0.0, 1.0, 0.0)
        z = sharpe / math.sqrt(max(1.0, float(strat and strat[3] is not None and 0 or 1)))
        crowd_component = 0.35 * net  # crowd is 35%
        backtest_component = 0.35 * math.tanh(float(backtest) / 100.0)
        sharpe_component = 0.30 * min(1.0, max(0.0, float(sharpe) / 3.0))
        market_score = crowd_component + backtest_component + sharpe_component
        return {
            "strategy": strategy_id,
            "name": strat[0] if strat else "?",
            "forecasts": len(rows),
            "long_weight": round(weighted_long, 4),
            "short_weight": round(weighted_short, 4),
            "consensus_net": round(net, 4),
            "aggregate_score": round(market_score, 4),
            "recommendation": (
                "ACCUMULATE" if market_score > 0.25
                else "REDUCE" if market_score < -0.25 else "HOLD"
            ),
            "volume_staked": round(volume, 2),
        }

    def trending(self, top_k: int = 5) -> List[Dict[str, Any]]:
        rows = self._conn.execute(  # type: ignore[union-attr]
            "SELECT id FROM strategies WHERE active=1"
        ).fetchall()
        scored = [self.aggregate(r[0]) for r in rows]
        scored.sort(key=lambda x: abs(x["aggregate_score"]), reverse=True)
        return scored[:top_k]

    def _count(self, t: str) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute(f"SELECT COUNT(*) FROM {t}")), (0,))
        return int(c or 0)
