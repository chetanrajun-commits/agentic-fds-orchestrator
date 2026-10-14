"""Vector memory: dependency-free stand-in for Pinecone / pgvector.

The README describes a Vector Isolation Architecture with strict namespace
isolation inside Pinecone or pgvector. This module provides the same
interface — `upsert` and `query` — but backed by an in-process list, so the
reference implementation runs identically on a laptop and in CI without any
external service or API key.

In production, swap this class for a Pinecone client. The call sites in
`agents/remediation.py` do not change.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

EMBED_DIM = 64


def _embed(text: str, dim: int = EMBED_DIM) -> list[float]:
    """Bag-of-words hashing embedder. Deterministic, no model, no network."""
    vec = [0.0] * dim
    for token in text.lower().split():
        h = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % dim
        vec[h] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


@dataclass
class MemoryEntry:
    id: str
    vector: list[float]
    text: str
    metadata: dict


@dataclass
class VectorMemory:
    """Namespace-isolated vector store, in-memory implementation."""

    namespace: str = "default"
    entries: list[MemoryEntry] = field(default_factory=list)

    def upsert(self, id: str, text: str, metadata: dict | None = None) -> None:
        self.entries.append(
            MemoryEntry(id=id, vector=_embed(text), text=text, metadata=metadata or {})
        )

    def query(self, text: str, top_k: int = 3) -> list[MemoryEntry]:
        if not self.entries:
            return []
        q = _embed(text)
        scored = [(_cosine(q, e.vector), e) for e in self.entries]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def __len__(self) -> int:
        return len(self.entries)
