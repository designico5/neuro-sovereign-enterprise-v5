"""
LAYER 4 - Data Knowledge
------------------------
Unified vector store + knowledge graph + versioned document archive.
Backends: ChromaDB (vectors), Neo4j/networkx (graphs), SQLite for metadata.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .base import BaseNSELayer

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class KnowledgeChunk:
    id: str
    source: str
    content: str
    embedding: Optional[List[float]] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class KnowledgeDataLayer(BaseNSELayer):
    layer_id = 4
    layer_name = "Data Knowledge"

    def __init__(self, config: Any) -> None:
        super().__init__(config)
        self.root = os.path.join(getattr(config, "data_dir", "./state"), "knowledge")
        os.makedirs(self.root, exist_ok=True)
        self.db_path = os.path.join(self.root, "knowledge.sqlite3")
        self._conn: Optional[sqlite3.Connection] = None
        self._graph: Optional[Any] = None
        self._vector_store: Optional[Any] = None
        self._dims = 384  # sentence-transformers/all-MiniLM-L6-v2 default

    async def _initialize(self) -> None:
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("""CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY, source TEXT, content TEXT,
            embedding_json TEXT, meta_json TEXT, created_at REAL
        )""")
        self._conn.execute("""CREATE TABLE IF NOT EXISTS graph_edges (
            src TEXT, dst TEXT, kind TEXT, weight REAL, meta_json TEXT,
            PRIMARY KEY(src, dst, kind)
        )""")
        self._conn.commit()
        self._init_graph()
        self._init_vector_store()
        self.add_extra("chunks_count", self._chunk_count())
        self.add_extra("edges_count", self._edge_count())
        self.add_extra("vector_dims", self._dims)

    # -------------------------------------------------------------- backends
    def _init_graph(self) -> None:
        try:
            import networkx as nx  # type: ignore

            self._graph = nx.DiGraph()
            for (src, dst, kind, w) in self._conn.execute(  # type: ignore[union-attr]
                "SELECT src,dst,kind,weight FROM graph_edges"
            ):
                self._graph.add_edge(src, dst, kind=kind, weight=w)
        except ImportError:
            self._graph = {"nodes": set(), "edges": []}

    def _init_vector_store(self) -> None:
        try:
            import chromadb  # type: ignore

            client = chromadb.PersistentClient(path=os.path.join(self.root, "chroma"))
            self._vector_store = client.get_or_create_collection(name="nse_knowledge")
            return
        except Exception:
            pass
        # Fallback: in-memory dict vector table with cosine similarity
        self._vector_store = {"__fallback__": True, "rows": {}}

    # ----------------------------------------------------------------- API
    def add(self, source: str, content: str, meta: Optional[Dict[str, Any]] = None) -> KnowledgeChunk:
        cid = hashlib.sha256(f"{source}|{content}".encode()).hexdigest()[:16]
        chunk = KnowledgeChunk(id=cid, source=source, content=content, meta=meta or {})
        chunk.embedding = self._embed(content)
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?)",
            (cid, source, content, json.dumps(chunk.embedding), json.dumps(chunk.meta), chunk.created_at),
        )
        self._conn.commit()
        if isinstance(self._vector_store, dict) and self._vector_store.get("__fallback__"):
            self._vector_store["rows"][cid] = {"e": chunk.embedding, "c": content}
        else:  # pragma: no cover - chroma path
            try:
                self._vector_store.upsert(  # type: ignore[call-arg]
                    ids=[cid], documents=[content], embeddings=[chunk.embedding], metadatas=[chunk.meta]
                )
            except Exception:
                pass
        self.bump_ok()
        self.add_extra("chunks_count", self._chunk_count())
        return chunk

    def add_edge(self, src: str, dst: str, kind: str = "relates_to", weight: float = 1.0) -> None:
        assert self._conn is not None
        self._conn.execute(
            "INSERT OR REPLACE INTO graph_edges VALUES (?,?,?,?,?)",
            (src, dst, kind, weight, "{}"),
        )
        self._conn.commit()
        try:
            if hasattr(self._graph, "add_edge"):
                self._graph.add_edge(src, dst, kind=kind, weight=weight)
        except Exception:
            pass
        self.add_extra("edges_count", self._edge_count())

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._conn:
            return []
        q_emb = self._embed(query)
        # Fallback cosine search (runs always; Chroma gets used via add path only)
        cursor = self._conn.execute("SELECT id,source,content,embedding_json FROM chunks")
        scored: List[Tuple[float, str, str, str]] = []
        for cid, src, content, emb_json in cursor:
            try:
                e = json.loads(emb_json) if emb_json else []
            except Exception:
                e = []
            if len(e) != len(q_emb):
                continue
            sim = self._cosine(e, q_emb)
            scored.append((sim, cid, src, content))
        scored.sort(reverse=True)
        return [
            {"score": round(s, 4), "id": cid, "source": src, "content": c[:200]}
            for (s, cid, src, c) in scored[:top_k]
        ]

    def graph_traverse(self, start: str, depth: int = 3) -> List[Dict[str, Any]]:
        if self._graph is None or not hasattr(self._graph, "successors"):
            return []
        result: List[Dict[str, Any]] = []
        visited: set = {start}
        frontier: List[Tuple[str, int]] = [(start, 0)]
        while frontier:
            node, d = frontier.pop(0)
            if d >= depth:
                continue
            if hasattr(self._graph, "successors"):
                for nxt in self._graph.successors(node):  # type: ignore[union-attr]
                    if nxt in visited:
                        continue
                    visited.add(nxt)
                    result.append({"src": node, "dst": nxt, "depth": d + 1})
                    frontier.append((nxt, d + 1))
        return result

    # -------------------------------------------------------------- helpers
    def _embed(self, text: str) -> List[float]:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            model = SentenceTransformer("all-MiniLM-L6-v2")
            vec = model.encode(text, show_progress_bar=False).tolist()
            return list(map(float, vec))[: self._dims]
        except Exception:
            pass
        # Deterministic pseudo-embedding fallback (hash-based, NOT semantic)
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(0, len(h), 4):
            quad = h[i : i + 4] or b"\x00\x00\x00\x00"
            val = int.from_bytes(quad, "big", signed=True) / 2**31
            vec.append(val)
        while len(vec) < self._dims:
            h = hashlib.sha256(h).digest()
            for i in range(0, len(h), 4):
                quad = h[i : i + 4] or b"\x00\x00\x00\x00"
                vec.append(int.from_bytes(quad, "big", signed=True) / 2**31)
                if len(vec) >= self._dims:
                    break
        return vec[: self._dims]

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5 or 1e-9
        nb = sum(y * y for y in b) ** 0.5 or 1e-9
        return dot / (na * nb)

    def _chunk_count(self) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute("SELECT COUNT(*) FROM chunks")), (0,))
        return int(c or 0)

    def _edge_count(self) -> int:
        if not self._conn:
            return 0
        (c,) = next(iter(self._conn.execute("SELECT COUNT(*) FROM graph_edges")), (0,))
        return int(c or 0)
