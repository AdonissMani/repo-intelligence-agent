from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class AdaptiveConfig:
    initial_seed_count: int = 5
    max_depth: int = 3
    max_nodes: int = 20
    max_rounds: int = 4
    min_confidence: float = 0.70
    min_margin: float = 0.10
    min_evidence_gain: float = 0.05


@dataclass
class RetrievalState:
    question: str
    round_number: int
    depth_reached: int
    candidates: list[str]
    explored_repositories: set[str] = field(default_factory=set)
    explored_edges: list[tuple[str, str]] = field(default_factory=list)
    confidence: float = 0.0
    margin: float = 0.0
    evidence_gain: float = 0.0
    sufficient: bool = False
    stop_reason: str | None = None


@dataclass
class QueryProfile:
    category: str
    likely_multi_repo: bool = False


@dataclass
class SufficiencyResult:
    sufficient: bool
    confidence: float
    margin: float
    reason: str
    evidence_gain: float = 0.0


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
        adaptive_config: AdaptiveConfig | None = None,
    ):
        self.repositories = repositories
        self.by_name = {repo.name: repo for repo in repositories}
        self.relationships = relationships
        self.lexical_index = BM25Index(repositories)
        self.semantic_index = RepositoryIndex(repositories, embedding_provider or make_embedding_provider())
        self.graph = RepositoryGraph(relationships, set(self.by_name))
        self.adaptive_config = adaptive_config or AdaptiveConfig()

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

        if strategy == "adaptive":
            return self._route_adaptive(question, lexical, semantic, metadata, limit)

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
            "repository_universe_size": len(self.repositories),
            "candidate_count": len(results),
            "graph_depth": graph_depth,
            "depth_reached": graph_depth,
            "nodes_expanded": len(graph_paths),
            "edges_traversed": sum(len(path.path) - 1 for path in graph_paths.values() if path.path),
        }
        return results, stats

    def _route_adaptive(
        self,
        question: str,
        lexical: dict[str, float],
        semantic: dict[str, float],
        metadata: dict[str, float],
        limit: int,
    ) -> tuple[list[RouteResult], dict[str, int | float | str | bool | list[dict]]]:
        started = time.perf_counter()
        config = self.adaptive_config
        profile = self._query_profile(question)
        final_scores = self._hybrid_scores(lexical, semantic, metadata, {})
        final_depth = 0
        final_reason = "NO_EVIDENCE"
        final_evidence_gain = 0.0
        adaptive_sufficient = False
        rounds = 0
        bind_graph_paths: dict[str, GraphPath] = {}
        explored_nodes: set[str] = set()
        explored_edges: list[tuple[str, str]] = []
        round_traces: list[dict] = []
        previous_nodes: set[str] = set()
        previous_edges: set[tuple[str, str]] = set()

        for depth in range(0, config.max_depth + 1):
            if rounds >= config.max_rounds:
                final_reason = "MAX_ROUNDS_REACHED"
                break
            graph_paths = self._graph_paths(lexical, semantic, metadata, depth, max_nodes=config.max_nodes)
            current_nodes = set(graph_paths.keys())
            current_edges = set()
            for path in graph_paths.values():
                current_edges.update(zip(path.path, path.path[1:]))
            graph = self._graph_scores(graph_paths)
            candidate_scores = self._hybrid_scores(lexical, semantic, metadata, graph)
            ranked = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
            if ranked:
                top_name, top_score = ranked[0]
                second_score = ranked[1][1] if len(ranked) > 1 else 0.0
                margin = max(0.0, top_score - second_score)
                confidence = top_score
                new_nodes = current_nodes - previous_nodes
                new_edges = current_edges - previous_edges
                evidence_gain = (
                    0.6 * (len(new_nodes) / max(len(current_nodes), 1))
                    + 0.4 * (len(new_edges) / max(len(current_edges), 1))
                    if current_edges or current_nodes else 0.0
                )
                ranking_gain = max(0.0, confidence - max(0.0, max((score for _, score in ranked[1:]), default=0.0)))
                sufficiency = self._evaluate_sufficiency(candidate_scores, profile, config, confidence, margin, evidence_gain)
                final_scores = candidate_scores
                bind_graph_paths = graph_paths
                final_depth = depth
                final_reason = sufficiency.reason
                final_evidence_gain = evidence_gain
                adaptive_sufficient = sufficiency.sufficient
                rounds = depth + 1
                explored_nodes = current_nodes
                explored_edges = sorted(current_edges)
                previous_nodes = current_nodes
                previous_edges = current_edges
                round_traces.append(
                    {
                        "round": depth,
                        "depth": depth,
                        "candidates": [name for name, _ in ranked[: min(5, len(ranked))]],
                        "nodes_explored": len(explored_nodes),
                        "edges_explored": len(explored_edges),
                        "new_nodes": len(new_nodes),
                        "new_edges": len(new_edges),
                        "confidence": round(confidence, 4),
                        "margin": round(margin, 4),
                        "ranking_gain": round(ranking_gain, 4),
                        "evidence_gain": round(evidence_gain, 4),
                        "sufficient": sufficiency.sufficient,
                        "stop_reason": sufficiency.reason,
                    }
                )
                if sufficiency.sufficient:
                    break
            if len(explored_nodes) >= config.max_nodes:
                final_reason = "MAX_NODES_REACHED"
                adaptive_sufficient = False
                break
            if depth >= config.max_depth:
                final_reason = "MAX_DEPTH_REACHED"
                adaptive_sufficient = False
                break
        ranked = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)[:limit]
        results = [self._result(name, score, "adaptive", bind_graph_paths.get(name)) for name, score in ranked if score > 0]
        state = RetrievalState(
            question=question,
            round_number=max(1, rounds),
            depth_reached=final_depth,
            candidates=[name for name, _ in ranked],
            explored_repositories=set(explored_nodes),
            explored_edges=explored_edges,
            confidence=max(0.0, max(score for _, score in ranked) if ranked else 0.0),
            margin=max(0.0, (ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else ranked[0][1]),
            evidence_gain=final_evidence_gain,
            sufficient=adaptive_sufficient,
            stop_reason=final_reason,
        )
        budget_exhausted = len(explored_nodes) >= config.max_nodes and final_reason == "MAX_NODES_REACHED"
        stats: dict[str, int | float | str | bool | list[dict]] = {
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "tokens": len(TOKEN_RE.findall(question)),
            "repositories_considered": len(self.repositories),
            "repository_universe_size": len(self.repositories),
            "candidate_count": len(results),
            "graph_depth": final_depth,
            "depth_reached": final_depth,
            "nodes_expanded": len(explored_nodes),
            "edges_traversed": len(explored_edges),
            "budget_exhausted": budget_exhausted,
            "adaptive_depth_reached": final_depth,
            "adaptive_sufficient": adaptive_sufficient,
            "adaptive_stop_reason": final_reason,
            "adaptive_rounds": rounds,
            "adaptive_nodes_expanded": len(explored_nodes),
            "adaptive_edges_traversed": len(explored_edges),
            "adaptive_trace": round_traces,
            "adaptive_config": {
                "max_depth": config.max_depth,
                "max_nodes": config.max_nodes,
                "max_rounds": config.max_rounds,
                "min_confidence": config.min_confidence,
                "min_margin": config.min_margin,
                "min_evidence_gain": config.min_evidence_gain,
            },
            "adaptive_state": {
                "question": state.question,
                "depth_reached": state.depth_reached,
                "explored_repositories": sorted(state.explored_repositories),
                "edges_traversed": len(state.explored_edges),
                "confidence": round(state.confidence, 4),
                "margin": round(state.margin, 4),
                "evidence_gain": round(state.evidence_gain, 4),
                "sufficient": state.sufficient,
                "stop_reason": state.stop_reason,
                "budget_exhausted": budget_exhausted,
            },
        }
        return results, stats

    def _query_profile(self, question: str) -> QueryProfile:
        q = question.lower()
        if any(phrase in q for phrase in ["what systems are involved", "what happens after", "if ", "affected", "participate", "flow", "what repositories participate"]):
            return QueryProfile(category="cross_repository", likely_multi_repo=True)
        if any(phrase in q for phrase in ["alert", "deployment", "terraform", "kubernetes", "timeout", "observability", "production"]):
            return QueryProfile(category="infrastructure", likely_multi_repo=False)
        if any(phrase in q for phrase in ["which service", "which repo", "where is", "where are", "which repository", "owns", "owner"]):
            return QueryProfile(category="direct", likely_multi_repo=False)
        return QueryProfile(category="architecture", likely_multi_repo=True)

    def _compute_evidence_gain(
        self,
        previous_scores: dict[str, float],
        current_scores: dict[str, float],
    ) -> float:
        if not previous_scores and not current_scores:
            return 0.0
        previous_set = set(previous_scores)
        current_set = set(current_scores)
        new_candidates = current_set - previous_set
        new_candidate_gain = len(new_candidates) / max(len(current_set), 1)

        shared = current_set & previous_set
        improvements = []
        for repo in sorted(shared):
            delta = current_scores.get(repo, 0.0) - previous_scores.get(repo, 0.0)
            if delta > 0.0:
                improvements.append(delta)

        score_gain = sum(improvements) / max(len(current_set), 1)
        return min(1.0, 0.7 * new_candidate_gain + 0.3 * max(0.0, score_gain))

    def _evaluate_sufficiency(
        self,
        scores: dict[str, float],
        profile: QueryProfile,
        config: AdaptiveConfig,
        confidence: float,
        margin: float,
        evidence_gain: float,
    ) -> SufficiencyResult:
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        if not ranked:
            return SufficiencyResult(False, 0.0, 0.0, "NO_EVIDENCE", 0.0)
        top_score = ranked[0][1]
        second_score = ranked[1][1] if len(ranked) > 1 else 0.0
        confidence = max(confidence, top_score)
        margin = max(margin, top_score - second_score)
        direct_threshold = config.min_confidence if not profile.likely_multi_repo else config.min_confidence - 0.08
        if confidence >= direct_threshold and margin >= config.min_margin:
            return SufficiencyResult(True, confidence, margin, "HIGH_CONFIDENCE", evidence_gain)
        if profile.likely_multi_repo and evidence_gain < config.min_evidence_gain:
            return SufficiencyResult(False, confidence, margin, "NO_MEANINGFUL_NEW_EVIDENCE", evidence_gain)
        if profile.likely_multi_repo and confidence >= 0.60 and margin >= 0.05:
            return SufficiencyResult(False, confidence, margin, "MULTI_REPO_CONTINUE", evidence_gain)
        return SufficiencyResult(False, confidence, margin, "INSUFFICIENT_EVIDENCE", evidence_gain)

    def _hybrid_scores(
        self,
        lexical: dict[str, float],
        semantic: dict[str, float],
        metadata: dict[str, float],
        graph: dict[str, float],
    ) -> dict[str, float]:
        scores: dict[str, float] = {}
        for repo in self.repositories:
            scores[repo.name] = (
                lexical[repo.name] * HYBRID_WEIGHTS["lexical"]
                + semantic[repo.name] * HYBRID_WEIGHTS["semantic"]
                + metadata[repo.name] * HYBRID_WEIGHTS["metadata"]
                + graph.get(repo.name, 0.0) * HYBRID_WEIGHTS["graph"]
            )
        return scores

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
        max_nodes: int | None = None,
    ) -> dict[str, GraphPath]:
        seed_scores = {}
        for repo in self.repositories:
            seed_scores[repo.name] = max(lexical[repo.name], semantic[repo.name], metadata[repo.name])
        seeds = dict(sorted(seed_scores.items(), key=lambda item: item[1], reverse=True)[:SEED_COUNT])
        return self.graph.expand(seeds, max(0, graph_depth), max_nodes=max_nodes)

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
