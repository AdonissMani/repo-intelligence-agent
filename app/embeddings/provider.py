from __future__ import annotations

from collections import Counter
import math
import re


TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingProvider:
    def embed(self, text: str) -> dict[str, float]:
        raise NotImplementedError


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic sparse bag-of-words embedding used for reproducible baselines."""

    def embed(self, text: str) -> dict[str, float]:
        counts = Counter(TOKEN_RE.findall(text.lower().replace("-", " ")))
        norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
        return {token: value / norm for token, value in counts.items()}


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(token, 0.0) for token, value in left.items())
