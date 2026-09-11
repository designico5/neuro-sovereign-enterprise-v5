"""
LAYER 9 - Cognition Neuro-Symbolic
-----------------------------------
Hybrid reasoning: neural (LLM routing via Ollama/OpenAI) + symbolic (prolog-like
clause resolution + rule engine). Thought Visualizer renders the DSR pipeline steps.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DSRStep:
    idx: int
    kind: str  # "deduct","induct","abduct","query","answer"
    content: str
    elapsed_ms: float
    trace: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Clause:
    head: str
    body: Tuple[str, ...]
    weight: float = 1.0


class NeuroSymbolicEngine(BaseNSELayer):
    layer_id = 9
    layer_name = "Neuro-Symbolic Cognition"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.kb: List[Clause] = []
        self.facts: set = set()
        self.llm_provider: Optional[str] = None
        self.llm_base_url: Optional[str] = None
        self.llm_api_key: Optional[str] = None
        self._dsr_steps: List[DSRStep] = []
        self._routing_rules: List[Tuple[str, str]] = [  # (regex_pattern, model/provider)
            (r"^(analyse|analyze|compare|contrast|review)", "deep-reasoner"),
            (r"^(translate|übersetze|traducir|traduire)", "multilingual"),
            (r"(code|function|bug|implement|fix|refactor)", "coder"),
        ]

    async def _initialize(self) -> None:
        import os

        self.llm_provider = os.getenv("NSE_LLM_PROVIDER", "ollama")
        self.llm_base_url = os.getenv("NSE_LLM_URL", "http://localhost:11434")
        self.llm_api_key = os.getenv("NSE_LLM_API_KEY")
        self.add_extra("kb_clauses", len(self.kb))
        self.add_extra("facts", len(self.facts))
        self.add_extra("provider", self.llm_provider)

    # ---------------------------------------------------------------- KB
    def add_clause(self, head: str, body: List[str], weight: float = 1.0) -> None:
        self.kb.append(Clause(head, tuple(body), float(weight)))
        self.add_extra("kb_clauses", len(self.kb))
        self.bump_ok()

    def add_fact(self, fact: str) -> None:
        self.facts.add(fact.lower())
        self.add_extra("facts", len(self.facts))
        self.bump_ok()

    def prove(self, goal: str, max_depth: int = 6) -> Tuple[bool, List[List[str]]]:
        """Backward-chaining symbolic resolver."""
        start = time.time()
        result_paths: List[List[str]] = []
        def walk(g: str, depth: int, path: List[str]) -> bool:
            if depth > max_depth:
                return False
            if g.lower() in self.facts:
                result_paths.append(path + [f"FACT[{g}]"])
                return True
            ok_any = False
            for c in self.kb:
                if c.head.lower() != g.lower():
                    continue
                sub_ok = all(walk(b, depth + 1, path + [f"{c.head}←{b}"]) for b in c.body)
                if sub_ok:
                    ok_any = True
            return ok_any
        ok = walk(goal, 0, [])
        self._dsr_steps.append(DSRStep(
            idx=len(self._dsr_steps), kind="deduct", content=goal,
            elapsed_ms=(time.time()-start)*1000,
            trace={"paths_found": len(result_paths), "ok": ok}
        ))
        if ok:
            self.bump_ok()
        else:
            self.bump_fail()
        return ok, result_paths

    # ------------------------------------------------------- LLM routing
    def route(self, query: str) -> Dict[str, Any]:
        import re
        for pattern, lane in self._routing_rules:
            if re.search(pattern, query, re.I):
                return {"lane": lane, "pattern": pattern, "provider": self.llm_provider}
        return {"lane": "default-chat", "pattern": None, "provider": self.llm_provider}

    async def neural_call(self, prompt: str, model: str = "qwen2.5:7b",
                          system: Optional[str] = None, max_tokens: int = 1024) -> Dict[str, Any]:
        t0 = time.time()
        provider = self.llm_provider or "ollama"
        try:
            if provider == "ollama":
                resp = await self._ollama_generate(model, prompt, system, max_tokens)
            elif provider == "openai":
                resp = await self._openai_generate(model, prompt, system, max_tokens)
            else:
                resp = {"text": self._fallback_generate(prompt), "simulated": True}
            ms = (time.time() - t0) * 1000
            self._dsr_steps.append(DSRStep(
                idx=len(self._dsr_steps), kind="query",
                content=f"llm[{provider}:{model}]", elapsed_ms=ms,
                trace={"tokens_in": len(prompt), "tokens_out": len(resp.get("text", ""))}
            ))
            self.bump_ok()
            return {"text": resp.get("text", ""), "meta": resp, "ms": ms}
        except Exception as exc:
            self.bump_fail()
            return {"text": "", "error": str(exc), "ms": (time.time() - t0) * 1000}

    async def _ollama_generate(self, model: str, prompt: str, system: Optional[str], max_tokens: int) -> Dict[str, Any]:
        import httpx

        payload: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False,
                                  "options": {"num_predict": max_tokens}}
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{self.llm_base_url}/api/generate", json=payload)
            if r.status_code == 200:
                data = r.json()
                return {"text": data.get("response", ""), "model": data.get("model", model)}
            return {"text": "", "status": r.status_code}

    async def _openai_generate(self, model: str, prompt: str, system: Optional[str], max_tokens: int) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover
            return {"text": "", "error": f"openai package missing: {exc}"}
        client = AsyncOpenAI(api_key=self.llm_api_key, base_url=self.llm_base_url or None)
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        r = await client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)
        text = r.choices[0].message.content or ""
        return {"text": text, "usage": dict(r.usage) if r.usage else {}}

    @staticmethod
    def _fallback_generate(prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:32]
        return f"[neuro-symbolic offline fallback] echo: {prompt[:40]}... (sig={digest})"

    # ---------------------------------------------------------------- DSR
    async def dsr(self, question: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Deliberative Symbolic Reasoning: route → symbolic check → neural synthesis."""
        t0 = time.time()
        route = self.route(question)
        symbolic_ok, symbolic_paths = self.prove(question.split(".")[0].strip())
        neural = await self.neural_call(question, system=system)
        steps_snapshot = list(self._dsr_steps)
        answer = self._synthesize(question, symbolic_ok, symbolic_paths, neural.get("text", ""))
        self._dsr_steps.append(DSRStep(
            idx=len(self._dsr_steps), kind="answer",
            content=answer[:200], elapsed_ms=(time.time() - t0) * 1000,
            trace={"lane": route["lane"], "symbolic_ok": symbolic_ok}
        ))
        self.bump_ok()
        return {
            "route": route,
            "symbolic_proved": symbolic_ok,
            "symbolic_paths_count": len(symbolic_paths),
            "neural_response": neural,
            "answer": answer,
            "total_ms": (time.time() - t0) * 1000,
            "steps": [
                {"idx": s.idx, "kind": s.kind, "content": s.content[:100],
                 "ms": round(s.elapsed_ms, 2), "trace": s.trace}
                for s in steps_snapshot
            ],
        }

    # ------------------------------------------------------------- visualizer
    def thought_graph_mermaid(self) -> str:
        lines = ["flowchart TD"]
        for s in self._dsr_steps[-40:]:
            label = s.content.replace('"', "'")[:50]
            lines.append(f'  S{s.idx}["{s.kind}: {label}"]')
            if s.idx > 0:
                lines.append(f"  S{s.idx-1} --> S{s.idx}")
        return "\n".join(lines)

    @staticmethod
    def _synthesize(q: str, proved: bool, paths: List[List[str]], neural_text: str) -> str:
        bits = []
        bits.append(f"Query: {q}")
        bits.append(f"Symbolic proof: {'PASS' if proved else 'FAIL (neural used)'}")
        if paths:
            bits.append(f"Symbolic paths: {len(paths)}")
        bits.append(f"Neural: {neural_text.strip()[:200]}")
        return " | ".join(bits)
