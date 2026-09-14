from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque

from app.db.models import Relationship


EDGE_WEIGHTS = {
    "DEPENDS_ON": 1.0,
    "CONSUMES": 0.9,
    "PRODUCES_EVENT": 0.75,
    "CONSUMES_EVENT": 0.75,
    "EXPOSES_API": 0.7,
    "REFERENCES_SERVICE": 0.55,
    "REFERENCES_API": 0.45,
    "REFERENCES_EVENT": 0.35,
}
DECAY_BY_HOP = 0.7


@dataclass
class GraphPath:
    repository: str
    score: float
    path: list[str]
    relationships: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


class RepositoryGraph:
    def __init__(self, relationships: list[Relationship], repositories: set[str]):
        self.relationships = relationships
        self.repositories = repositories
        self.adjacency = self._build_adjacency()

    def _build_adjacency(self) -> dict[str, list[tuple[str, str, str]]]:
        adjacency: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        produced_by: dict[str, list[str]] = defaultdict(list)
        consumed_by: dict[str, list[str]] = defaultdict(list)
        exposed_by: dict[str, list[str]] = defaultdict(list)
        referenced_by: dict[str, list[str]] = defaultdict(list)

        for rel in self.relationships:
            if rel.source in self.repositories and rel.target in self.repositories:
                weight_name = rel.type
                adjacency[rel.source].append((rel.target, weight_name, rel.evidence))
                if rel.type in {"DEPENDS_ON", "CONSUMES"}:
                    adjacency[rel.target].append((rel.source, f"REVERSE_{rel.type}", rel.evidence))
            elif rel.type == "PRODUCES_EVENT":
                produced_by[rel.target].append(rel.source)
            elif rel.type == "CONSUMES_EVENT":
                consumed_by[rel.target].append(rel.source)
            elif rel.type == "EXPOSES_API":
                exposed_by[rel.target].append(rel.source)
            elif rel.type == "REFERENCES_API":
                referenced_by[rel.target].append(rel.source)

        for event, producers in produced_by.items():
            for producer in producers:
                for consumer in consumed_by.get(event, []):
                    if producer != consumer:
                        adjacency[producer].append((consumer, "EVENT_FLOW", event))
                        adjacency[consumer].append((producer, "REVERSE_EVENT_FLOW", event))

        for api, providers in exposed_by.items():
            for provider in providers:
                for consumer in referenced_by.get(api, []):
                    if provider != consumer:
                        adjacency[consumer].append((provider, "API_CALL", api))
                        adjacency[provider].append((consumer, "REVERSE_API_CALL", api))
        return adjacency

    def expand(self, seeds: dict[str, float], depth: int, max_nodes: int | None = None) -> dict[str, GraphPath]:
        best: dict[str, GraphPath] = {}
        queue = deque()
        for name, score in seeds.items():
            if name not in self.repositories or score <= 0:
                continue
            if max_nodes is not None and len(best) >= max_nodes:
                break
            best[name] = GraphPath(name, score, [name])
            queue.append((name, score, [name], [], [], 0))

        while queue:
            current, score, path, rels, evidence, hops = queue.popleft()
            if hops >= depth:
                continue
            if max_nodes is not None and len(best) >= max_nodes:
                break
            for target, rel_type, rel_evidence in sorted(
                self.adjacency.get(current, []),
                key=lambda item: (item[0], item[1], item[2] or ""),
            ):
                if target in path:
                    continue
                if max_nodes is not None and len(best) >= max_nodes:
                    break
                if target in best:
                    continue
                edge_weight = relationship_weight(rel_type)
                next_score = score * edge_weight * DECAY_BY_HOP
                next_path = path + [target]
                next_rels = rels + [rel_type]
                next_evidence = evidence + [rel_evidence]
                if max_nodes is not None and len(best) >= max_nodes:
                    break
                existing = best.get(target)
                if existing is None or next_score > existing.score:
                    best[target] = GraphPath(target, next_score, next_path, next_rels, next_evidence)
                    queue.append((target, next_score, next_path, next_rels, next_evidence, hops + 1))
                    if max_nodes is not None and len(best) >= max_nodes:
                        break
        return best


def relationship_weight(relationship_type: str) -> float:
    clean_type = relationship_type.removeprefix("REVERSE_")
    if clean_type in {"EVENT_FLOW", "API_CALL"}:
        return 0.8
    return EDGE_WEIGHTS.get(clean_type, 0.25)
