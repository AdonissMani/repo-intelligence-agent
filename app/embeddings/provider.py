from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
import math
import os
import re
import urllib.request
import json


TOKEN_RE = re.compile(r"[a-z0-9]+")
Vector = dict[str, float] | list[float]


class EmbeddingProvider:
    def embed(self, text: str) -> Vector:
        raise NotImplementedError


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic sparse bag-of-words embedding used for reproducible baselines."""

    def embed(self, text: str) -> dict[str, float]:
        counts = Counter(TOKEN_RE.findall(text.lower().replace("-", " ")))
        norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        return {token: value / norm for token, value in counts.items()}


class SemanticEmbeddingProvider(EmbeddingProvider):
    """Real embedding adapter used when experiment credentials are configured."""

    def __init__(self, model: str | None = None, endpoint: str | None = None, api_key: str | None = None):
        self.model = model or os.getenv("REPO_INTEL_EMBEDDING_MODEL", "text-embedding-3-small")
        self.endpoint = endpoint or os.getenv("REPO_INTEL_EMBEDDING_ENDPOINT", "https://api.openai.com/v1/embeddings")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def embed(self, text: str) -> list[float]:
        if not self.api_key:
            raise RuntimeError("Semantic embeddings require OPENAI_API_KEY or an injected provider.")
        payload = json.dumps({"model": self.model, "input": text}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        return [float(value) for value in body["data"][0]["embedding"]]


def make_embedding_provider(name: str | None = None) -> EmbeddingProvider:
    provider = (name or os.getenv("REPO_INTEL_EMBEDDING_PROVIDER", "hashing")).lower()
    if provider == "hashing":
        return HashingEmbeddingProvider()
    if provider == "semantic":
        return SemanticEmbeddingProvider()
    raise ValueError(f"Unknown embedding provider: {provider}")


def cosine(left: Vector, right: Vector) -> float:
    if isinstance(left, dict) and isinstance(right, dict):
        return _sparse_cosine(left, right)
    if isinstance(left, Sequence) and isinstance(right, Sequence):
        return _dense_cosine(left, right)
    raise TypeError("Cannot compare sparse and dense embeddings")


def _sparse_cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())


def _dense_cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)
