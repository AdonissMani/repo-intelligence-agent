from __future__ import annotations

from dataclasses import dataclass
import re
import time

from app.db.models import Relationship, RepositoryRecord
from app.embeddings.provider import EmbeddingProvider, make_embedding_provider
from app.graph.traversal import GraphPath, RepositoryGraph
from app.retrieval.lexical import BM25Index
from app.retrieval.index import RepositoryIndex


TOKEN_RE = re.compile(r"[a-z0-9]+")
DEFAULT_GRAPH_DEPTH = 2
SEED_COUNT = 5
HYBRID_WEIGHTS = {
    "lexical": 0.30,
    "semantic": 0.25,
    "metadata": 0.25,
    "graph": 0.20,
}


@dataclass
class RouteResult:
    name: str
    score: float
    reason: str
    path: list[str] | None = None
    relationships: list[str] | None = None
    evidence: list[str] | None = None


class RepositoryRouter:
    def __init__(
        self,
        repositories: list[RepositoryRecord],
        relationships: list[Relationship],
        embedding_provider: EmbeddingProvider | None = None,
    ):
        self.repositories = repositories
        self.by_name = {repo.name: repo for repo in repositories}
        self.relationships = relationships
        self.lexical_index = BM25Index(repositories)
        self.semantic_index = RepositoryIndex(repositories, embedding_provider or make_embedding_provider())
        self.graph = RepositoryGraph(relationships, set(self.by_name))

    def route(
        self,
        question: str,
        strategy: str = "hybrid",
        limit: int = 5,
        graph_depth: int = DEFAULT_GRAPH_DEPTH,
    ) -> tuple[list[RouteResult], dict[str, int | float]]:
        started = time.perf_counter()
        lexical = self.lexical_index.search(question)
        semantic = self.semantic_index.search(question)
        metadata = self._metadata_scores(question)
        graph_paths = self._graph_paths(lexical, semantic, metadata, graph_depth)
        graph = self._graph_scores(graph_paths)
        scores: dict[str, float] = {}
        for repo in self.repositories:
            if strategy == "lexical":
                scores[repo.name] = lexical[repo.name]
            elif strategy == "semantic":
                scores[repo.name] = semantic[repo.name]
            elif strategy == "metadata":
                scores[repo.name] = metadata[repo.name]
            elif strategy == "graph":
                scores[repo.name] = graph[repo.name]
            elif strategy == "hybrid":
                scores[repo.name] = (
                    lexical[repo.name] * HYBRID_WEIGHTS["lexical"]
                    + semantic[repo.name] * HYBRID_WEIGHTS["semantic"]
                    + metadata[repo.name] * HYBRID_WEIGHTS["metadata"]
                    + graph[repo.name] * HYBRID_WEIGHTS["graph"]
                )
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
        results = [self._result(name, score, strategy, graph_paths.get(name)) for name, score in ranked if score > 0]
        stats = {
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "tokens": len(TOKEN_RE.findall(question)),
            "repositories_considered": len(self.repositories),
            "graph_depth": graph_depth,
        }
        return results, stats

    def _metadata_scores(self, question: str) -> dict[str, float]:
        q_tokens = set(TOKEN_RE.findall(question.lower().replace("-", " ")))
        scores = {}
        for repo in self.repositories:
            fields = [repo.name, repo.team, repo.business_unit, repo.domain, repo.type]
            fields.extend(repo.provides + repo.apis + repo.depends_on + repo.consumed_by + repo.publishes + repo.subscribes + repo.data_owned)
            text = " ".join(fields).lower().replace("-", " ")
            tokens = set(TOKEN_RE.findall(text))
            if not q_tokens:
                scores[repo.name] = 0.0
                continue
            coverage = len(q_tokens & tokens) / len(q_tokens)
            precision = len(q_tokens & tokens) / max(len(tokens), 1)
            scores[repo.name] = min(1.0, coverage * 0.85 + precision * 0.15)
        return scores

    def _graph_paths(
        self,
        lexical: dict[str, float],
        semantic: dict[str, float],
        metadata: dict[str, float],
        graph_depth: int,
    ) -> dict[str, GraphPath]:
        seed_scores = {}
        for repo in self.repositories:
            seed_scores[repo.name] = max(lexical[repo.name], semantic[repo.name], metadata[repo.name])
        seeds = dict(sorted(seed_scores.items(), key=lambda item: item[1], reverse=True)[:SEED_COUNT])
        return self.graph.expand(seeds, max(0, graph_depth))

    def _graph_scores(self, graph_paths: dict[str, GraphPath]) -> dict[str, float]:
        raw = {repo.name: graph_paths.get(repo.name, GraphPath(repo.name, 0.0, [repo.name])).score for repo in self.repositories}
        max_score = max(raw.values()) or 1.0
        return {name: score / max_score for name, score in raw.items()}

    def _result(self, name: str, score: float, strategy: str, graph_path: GraphPath | None) -> RouteResult:
        repo = self.by_name[name]
        reason = f"Ranked by {strategy} evidence for {repo.domain}: {', '.join(repo.provides[:2])}."
        if graph_path:
            return RouteResult(
                name=name,
                score=round(score, 4),
                reason=reason,
                path=graph_path.path,
                relationships=graph_path.relationships,
                evidence=graph_path.evidence,
            )
        return RouteResult(name=name, score=round(score, 4), reason=reason)
