"""
LAYER 10 - Orchestration Swarm
------------------------------
Dynamic-scaling agent swarm. Each agent instance has a lifetime (TTL),
priority queue, token budget, restart policy, and horizontal autoscaling.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    DYING = "dying"
    DEAD = "dead"


@dataclass(slots=True)
class Task:
    id: str
    name: str
    priority: int = 5
    payload: Dict[str, Any] = field(default_factory=dict)
    max_seconds: int = 300
    created_at: float = field(default_factory=time.time)
    handler_name: Optional[str] = None


@dataclass(slots=True)
class AgentRuntime:
    id: str
    name: str
    lanes: set = field(default_factory=lambda: {"default"})
    status: AgentStatus = AgentStatus.IDLE
    token_budget: int = 1_000_000
    token_used: int = 0
    ttl_seconds: int = 3600
    created_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    task_count: int = 0
    error_count: int = 0


class OrchestrationSwarm(BaseNSELayer):
    layer_id = 10
    layer_name = "Orchestration Swarm"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.agents: Dict[str, AgentRuntime] = {}
        self.handlers: Dict[str, Callable[[Task, AgentRuntime], Awaitable[Any]]] = {}
        self._queue: "asyncio.PriorityQueue" = asyncio.PriorityQueue()
        self._loop_task: Optional[asyncio.Task] = None
        self.min_agents: int = 2
        self.max_agents: int = 64
        self.scale_up_threshold = 5  # pending tasks per agent
        self.scale_cooldown_seconds = 30.0
        self._last_scale: float = 0.0

    async def _initialize(self) -> None:
        for i in range(self.min_agents):
            self._spawn(f"agent-{i+1}")
        self._loop_task = asyncio.create_task(self._run_loop(), name="nse-swarm-loop")
        self.add_extra("agents_alive", len(self.agents))
        self.add_extra("queue_depth", self._queue.qsize())
        self.add_extra("handlers", list(self.handlers.keys()))

    # ---------------------------------------------------------------- API
    def register_handler(self, name: str, coro_fn: Callable[[Task, AgentRuntime], Awaitable[Any]]) -> None:
        self.handlers[name] = coro_fn
        self.add_extra("handlers", list(self.handlers.keys()))
        self.bump_ok()

    async def submit(self, task: Task) -> str:
        await self._queue.put((11 - min(max(task.priority, 1), 10), time.time(), task))
        self.add_extra("queue_depth", self._queue.qsize())
        self.bump_ok()
        return task.id

    async def scale(self, delta: int) -> int:
        """Spawn (positive delta) or terminate (negative delta) agents."""
        if delta > 0:
            for _ in range(delta):
                if len(self.agents) < self.max_agents:
                    self._spawn(f"agent-{uuid.uuid4().hex[:8]}")
        else:
            victims = list(self.agents.values())[: abs(delta)]
            for a in victims:
                a.status = AgentStatus.DYING
                self.agents.pop(a.id, None)
        self.add_extra("agents_alive", len(self.agents))
        return len(self.agents)

    # ---------------------------------------------------------------- core
    def _spawn(self, name: str) -> AgentRuntime:
        rid = "agt-" + uuid.uuid4().hex[:8]
        a = AgentRuntime(id=rid, name=name)
        self.agents[rid] = a
        return a

    async def _run_loop(self) -> None:
        while True:
            try:
                await self._autoscale()
                await self._dispatch_one()
                await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                return
            except Exception:
                logger.exception("swarm loop error")

    async def _autoscale(self) -> None:
        now = time.time()
        if now - self._last_scale < self.scale_cooldown_seconds:
            return
        pending = self._queue.qsize()
        alive = sum(1 for a in self.agents.values() if a.status in {AgentStatus.IDLE, AgentStatus.BUSY})
        if alive == 0:
            self._last_scale = now
            await self.scale(self.min_agents)
            return
        ratio = pending / max(1, alive)
        if ratio > self.scale_up_threshold and alive < self.max_agents:
            self._last_scale = now
            await self.scale(+min(4, self.max_agents - alive))
        elif ratio < 0.2 and alive > self.min_agents:
            self._last_scale = now
            await self.scale(-1)

    async def _dispatch_one(self) -> None:
        if self._queue.empty():
            return
        # Pick idle agent, pick highest priority task
        idle = [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
        if not idle:
            return
        priority, ts, task = await self._queue.get()
        agent = idle[0]
        agent.status = AgentStatus.BUSY
        agent.last_heartbeat = time.time()
        handler = self.handlers.get(task.handler_name or "__default__", self._default_handler)
        try:
            await asyncio.wait_for(handler(task, agent), timeout=max(1, task.max_seconds))
            agent.task_count += 1
            self.bump_ok()
        except Exception as exc:
            logger.warning("task %s failed: %s", task.id, exc)
            agent.error_count += 1
            self.bump_fail()
        finally:
            agent.status = AgentStatus.IDLE
            agent.last_heartbeat = time.time()
            self.add_extra("queue_depth", self._queue.qsize())

    # --------------------------------------------------------- built-ins
    @staticmethod
    async def _default_handler(task: Task, agent: AgentRuntime) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"task": task.id, "handled_by": agent.id, "ok": True, "payload_len": len(task.payload)}

    def status_report(self) -> Dict[str, Any]:
        alive = [a for a in self.agents.values() if a.status != AgentStatus.DEAD]
        return {
            "alive": len(alive),
            "queue_depth": self._queue.qsize(),
            "handlers": list(self.handlers.keys()),
            "agents": [
                {"id": a.id, "name": a.name, "status": a.status.value,
                 "tasks": a.task_count, "errors": a.error_count,
                 "token_used": a.token_used}
                for a in alive
            ],
        }
