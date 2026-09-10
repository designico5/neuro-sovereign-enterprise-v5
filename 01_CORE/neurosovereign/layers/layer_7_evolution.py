"""
LAYER 7 - Code Evolution
-------------------------
Genetic mutation + crossover based code patches with lineage tracking.
Agents operate on a local git-backed patches with pygit2, evolving towards higher
multi-parent recombination + benchmark scores via GRPO-style reward model.
"""
from __future__ import annotations

import difflib
import hashlib
import logging
import os
import random
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CodeCandidate:
    id: str
    parent_ids: Tuple[str, ...]
    code: str
    generation: int
    score: float = 0.0
    eval_result: Dict[str, Any] = field(default_factory=dict)
    lineage: List[str] = field(default_factory=list)


RewardFn = Callable[[str], float]


class CodeEvolutionEngine(BaseNSELayer):
    layer_id = 7
    layer_name = "Code Evolution"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "evolution")
        os.makedirs(self.root, exist_ok=True)
        self.population: Dict[str, CodeCandidate] = {}
        self.generations: List[List[str]] = []
        self.reward_history: List[float] = []
        self.mutation_rate: float = 0.15

    async def _initialize(self) -> None:
        self.add_extra("population_size", len(self.population))
        self.add_extra("generations", len(self.generations))
        self.add_extra("mutation_rate", self.mutation_rate)
        self._ensure_git()

    def _ensure_git(self) -> None:
        try:
            import pygit2  # type: ignore

            repo_path = os.path.join(self.root, "evolution.git")
            if not os.path.exists(os.path.join(repo_path, ".git")):
                pygit2.init_repository(repo_path, bare=False)
            self.add_extra("git_path", repo_path)
        except Exception:
            self.add_extra("git_path", None)

    # ------------------------------------------------------------------ API
    def seed(self, code_population: List[str]) -> List[str]:
        ids = []
        gen = []
        for c in code_population:
            cid = self._new_id(c)
            cand = CodeCandidate(id=cid, parent_ids=(), code=c, generation=0)
            self.population[cid] = cand
            ids.append(cid)
            gen.append(cid)
        self.generations.append(gen)
        self.add_extra("population_size", len(self.population))
        return ids

    async def evolve(self, generations: int = 5, pop_size: int = 12, reward_fn: Optional[RewardFn] = None) -> Dict[str, Any]:
        reward: RewardFn = reward_fn or (lambda c: self._default_reward(c))
        for _ in range(generations):
            await self._step(reward, pop_size)
        best = max(self.population.values(), key=lambda c: c.score)
        self.add_extra("population_size", len(self.population))
        self.add_extra("generations", len(self.generations))
        self.add_extra("best_score", best.score)
        return {
            "best_id": best.id,
            "best_score": best.score,
            "best_code": best.code,
            "generations_run": generations,
            "reward_history": self.reward_history[-10:],
        }

    # ---------------------------------------------------------------- core
    async def _step(self, reward_fn: RewardFn, pop_size: int) -> None:
        # Evaluate current generation if unscored
        current_ids = self.generations[-1] if self.generations else []
        scored: List[CodeCandidate] = []
        for cid in current_ids:
            cand = self.population[cid]
            if cand.score <= 0:
                try:
                    cand.score = float(reward_fn(cand.code))
                except Exception:
                    cand.score = 0.0
            scored.append(cand)
        scored.sort(key=lambda c: c.score, reverse=True)
        if scored:
            self.reward_history.append(scored[0].score)
        # Selection (tournament_size = max(2, pop_size // 3)
        elite = scored[: max(2, pop_size // 3)] or [CodeCandidate(id="seed", parent_ids=(), code="", generation=0)]
        next_gen_ids: List[str] = []
        while len(next_gen_ids) < pop_size:
            p1, p2 = random.sample(elite, k=2)
            child_code = self._crossover(p1.code, p2.code)
            if random.random() < self.mutation_rate:
                child_code = self._mutate(child_code)
            cid = self._new_id(child_code)
            if cid not in self.population:
                gen_n = len(self.generations) + 1
                self.population[cid] = CodeCandidate(
                    id=cid,
                    parent_ids=(p1.id, p2.id),
                    code=child_code,
                    generation=gen_n,
                    lineage=p1.lineage + [p1.id] + p2.lineage + [p2.id],
                )
            next_gen_ids.append(cid)
        self.generations.append(next_gen_ids)

    # ------------------------------------------------------------- genetics
    @staticmethod
    def _crossover(a: str, b: str) -> str:
        la = a.splitlines(keepends=True)
        lb = b.splitlines(keepends=True)
        if not la or not lb:
            return a or b
        pivot = random.randint(1, max(1, min(len(la), len(lb)) - 1))
        return "".join(la[:pivot] + lb[pivot:])

    @staticmethod
    def _mutate(code: str) -> str:
        lines = code.splitlines(keepends=True)
        if not lines:
            return code
        i = random.randrange(len(lines))
        op = random.choice(["swap", "drop", "duplicate", "comment"])
        if op == "drop" and len(lines) > 3:
            lines.pop(i)
        elif op == "duplicate":
            lines.insert(i, lines[i])
        elif op == "swap" and i + 1 < len(lines):
            lines[i], lines[i+1] = lines[i+1], lines[i]
        elif op == "comment":
            lines[i] = "# " + lines[i]
        return "".join(lines)

    # ------------------------------------------------------------ reward
    def _default_reward(self, code: str) -> float:
        """Heuristic reward (replace with real test execution + benchmarks in production."""
        score = 0.0
        score += min(len(code), 2000) / 2000.0
        score += code.count("def ") * 0.2
        score += code.count("async def ") * 0.4
        score -= code.count("TODO") * 0.05
        score -= code.count("#pragma: no cover") * 0.03
        try:
            compile(code, "<evo-candidate>", "exec")
            score += 2.0
        except SyntaxError:
            score -= 3.0
        # Encourage diversity via uniqueness against known patterns (heuristic structural)
        diff_unique = len(set(code.split())) / max(1, len(code.split()))
        score += diff_unique * 2.0
        return round(score, 4)

    # -------------------------------------------------------------- misc
    @staticmethod
    def _new_id(code: str) -> str:
        return "cand-" + hashlib.sha1(code.encode("utf-8")).hexdigest()[:12]

    def diff(self, id_a: str, id_b: str) -> str:
        a = self.population[id_a].code.splitlines(keepends=True)
        b = self.population[id_b].code.splitlines(keepends=True)
        return "".join(difflib.unified_diff(a, b, fromfile=id_a, tofile=id_b))
