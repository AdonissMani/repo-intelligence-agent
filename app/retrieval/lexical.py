from __future__ import annotations

from collections import Counter
import math
import re

from app.db.models import RepositoryRecord
from app.retrieval.index import repository_text


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower().replace("-", " "))


class BM25Index:
    def __init__(self, repositories: list[RepositoryRecord], k1: float = 1.5, b: float = 0.75):
        self.repositories = repositories
        self.k1 = k1
        self.b = b
        self.documents = {repo.name: tokenize(repository_text(repo)) for repo in repositories}
        self.term_counts = {name: Counter(tokens) for name, tokens in self.documents.items()}
        self.lengths = {name: len(tokens) for name, tokens in self.documents.items()}
        self.avg_len = sum(self.lengths.values()) / max(len(self.lengths), 1)
        self.doc_freq = self._document_frequencies()

    def _document_frequencies(self) -> Counter[str]:
        freq: Counter[str] = Counter()
        for tokens in self.documents.values():
            freq.update(set(tokens))
        return freq

    def search(self, question: str) -> dict[str, float]:
        query_terms = tokenize(question)
        raw = {repo.name: self._score(repo.name, query_terms) for repo in self.repositories}
        max_score = max(raw.values()) or 1.0
        return {name: score / max_score for name, score in raw.items()}

    def _score(self, name: str, query_terms: list[str]) -> float:
        score = 0.0
        total_docs = len(self.repositories)
        doc_len = self.lengths[name] or 1
        for term in query_terms:
            if term not in self.term_counts[name]:
                continue
            df = self.doc_freq[term]
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            tf = self.term_counts[name][term]
            denom = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_len)
            score += idf * (tf * (self.k1 + 1)) / denom
        return score
