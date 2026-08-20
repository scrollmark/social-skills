"""Embedding backends.

Default is fastembed with nomic-embed-text-v1.5 — ONNX, no torch, no daemon,
and the same model family + dimension (768) as the Ollama vectors the TS tool
used. The prefix trap, stated loudly: nomic is trained with task prefixes
(`search_document:` / `search_query:`) that Ollama does NOT apply, so vectors
from the two backends are not interchangeable despite identical dimension.
The Embedder owns the prefixes; call sites never prepend.

FakeEmbedder is deterministic and dependency-free — the test backend, and the
offline fallback for structural work where ranking quality is irrelevant.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol


class Embedder(Protocol):
    model_id: str
    dim: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class FakeEmbedder:
    """Deterministic hashed unit vectors. Useful ranking? No. Stable? Yes."""

    model_id = "fake:blake2s-16d"
    dim = 16

    def _one(self, text: str) -> list[float]:
        digest = hashlib.blake2s(text.encode("utf-8"), digest_size=self.dim * 2).digest()
        vals = [int.from_bytes(digest[i * 2 : i * 2 + 2], "big") - 32768 for i in range(self.dim)]
        norm = math.sqrt(sum(v * v for v in vals)) or 1.0
        return [v / norm for v in vals]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._one(text)


class FastembedEmbedder:
    """nomic-embed-text-v1.5 via fastembed (ONNX). ~130 MB one-time download."""

    model_id = "fastembed:nomic-ai/nomic-embed-text-v1.5"
    dim = 768
    _DOC_PREFIX = "search_document: "
    _QUERY_PREFIX = "search_query: "

    def __init__(self) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding("nomic-ai/nomic-embed-text-v1.5")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prefixed = [self._DOC_PREFIX + t for t in texts]
        return [list(map(float, v)) for v in self._model.embed(prefixed)]

    def embed_query(self, text: str) -> list[float]:
        (vec,) = list(self._model.embed([self._QUERY_PREFIX + text]))
        return list(map(float, vec))


def resolve_embedder(name: str = "fastembed") -> Embedder:
    if name == "fake":
        return FakeEmbedder()
    if name == "fastembed":
        return FastembedEmbedder()
    raise ValueError(f"unknown embedder backend: {name}")
