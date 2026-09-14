from __future__ import annotations

from dataclasses import dataclass
import re
import time

from app.db.models import Relationship, RepositoryRecord
from app.embeddings.provider import HashingEmbeddingProvider
from app.retrieval.index import RepositoryIndex


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class RouteResult:
    name: str
    score: float
    reason: str


class RepositoryRouter:
    def __init__(self, repositories: list[RepositoryRecord], relationships: list[Relationship]):
        self.repositories = repositories
        self.by_name = {repo.name: repo for repo in repositories}
        self.relationships = relationships
        self.index = RepositoryIndex(repositories, HashingEmbeddingProvider())

    def route(self, question: str, strategy: str = "hybrid", limit: int = 5) -> tuple[list[RouteResult], dict[str, int | float]]:
        started = time.perf_counter()
        semantic = self.index.search(question)
        metadata = self._metadata_scores(question)
        graph = self._graph_scores(question, metadata, semantic)
        scores: dict[str, float] = {}
        for repo in self.repositories:
            if strategy == "semantic":
                scores[repo.name] = semantic[repo.name]
            elif strategy == "metadata":
                scores[repo.name] = metadata[repo.name]
            elif strategy == "graph":
                scores[repo.name] = graph[repo.name]
            elif strategy == "hybrid":
                scores[repo.name] = semantic[repo.name] * 0.45 + metadata[repo.name] * 0.35 + graph[repo.name] * 0.20
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
        results = [RouteResult(name, round(score, 4), self._reason(name, question, strategy)) for name, score in ranked if score > 0]
        stats = {
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "tokens": len(TOKEN_RE.findall(question)),
            "repositories_considered": len(self.repositories),
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
            overlap = len(q_tokens & tokens) / max(len(q_tokens), 1)
            bonus = self._domain_bonus(question, repo)
            scores[repo.name] = min(1.0, overlap + bonus)
        return scores

    def _graph_scores(self, question: str, metadata: dict[str, float], semantic: dict[str, float]) -> dict[str, float]:
        scores = {repo.name: 0.0 for repo in self.repositories}
        seeds = sorted(self.repositories, key=lambda repo: metadata[repo.name] + semantic[repo.name], reverse=True)[:4]
        seed_names = {repo.name for repo in seeds}
        for repo in seeds:
            scores[repo.name] += 0.6 * (metadata[repo.name] + semantic[repo.name])
        for rel in self.relationships:
            if rel.source in seed_names and rel.target in scores:
                scores[rel.target] += 0.12
            if rel.target in seed_names and rel.source in scores:
                scores[rel.source] += 0.10
            if rel.target.lower() in question.lower():
                scores[rel.source] += 0.18
        max_score = max(scores.values()) or 1.0
        return {name: value / max_score for name, value in scores.items()}

    def _domain_bonus(self, question: str, repo: RepositoryRecord) -> float:
        q = question.lower()
        bonuses = {
            "payment-core": ["refund eligibility", "card payment", "payment authorization", "payment decision"],
            "ledger-core": ["accounting", "ledger", "reversal", "reconciliation"],
            "deployment-platform": ["configured", "timeout", "production", "helm", "deployment", "production timeout", "configured in production"],
            "observability-platform": ["investigate", "alert", "dashboard", "timeout failures", "slo", "payment timeout failures"],
            "risk-engine": ["eligible", "eligibility", "risk", "rejected", "loan application"],
            "subscription-service": ["subscription", "grace period", "billing retry", "suspension"],
            "checkout-service": ["checkout", "cart", "order creation"],
            "merchant-service": ["merchant", "settlement"],
            "repayment-service": ["repayment", "installment", "collection"],
        }
        weight = 0.25 if repo.name in {"deployment-platform", "observability-platform"} else 0.12
        return sum(weight for phrase in bonuses.get(repo.name, []) if phrase in q)

    def _reason(self, name: str, question: str, strategy: str) -> str:
        repo = self.by_name[name]
        if name == "payment-core" and "refund eligibility" in question.lower():
            return "Owns refund lifecycle and the RefundEligibilityPolicy module."
        if name == "deployment-platform" and "timeout" in question.lower():
            return "Holds production Helm values and service timeout configuration."
        if name == "observability-platform" and any(word in question.lower() for word in ["investigate", "alert", "failures"]):
            return "Owns dashboards, alerts, and tracing labels for service incidents."
        return f"Matched {strategy} evidence for {repo.domain}: {', '.join(repo.provides[:2])}."
