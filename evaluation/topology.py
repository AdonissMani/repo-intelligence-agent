from __future__ import annotations

from pathlib import Path

from app.db.models import Relationship


EVALUATED_TYPES = {"DEPENDS_ON", "CONSUMES", "PRODUCES_EVENT", "CONSUMES_EVENT"}


def load_ground_truth_relationships(path: Path) -> set[tuple[str, str, str]]:
    relationships: set[tuple[str, str, str]] = set()
    current: dict[str, str] | None = None
    in_relationships = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped == "relationships:":
            in_relationships = True
            continue
        if not in_relationships or not stripped:
            continue
        if stripped.startswith("- source:"):
            if current:
                relationships.add((current["source"], current["type"], current["target"]))
            current = {"source": stripped.split(":", 1)[1].strip()}
        elif current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        relationships.add((current["source"], current["type"], current["target"]))
    return relationships


def discovered_relationship_set(relationships: list[Relationship]) -> set[tuple[str, str, str]]:
    return {(rel.source, rel.type, rel.target) for rel in relationships if rel.type in EVALUATED_TYPES}


def topology_metrics(discovered: set[tuple[str, str, str]], ground_truth: set[tuple[str, str, str]]) -> dict[str, float]:
    metrics = _precision_recall_f1(discovered, ground_truth)
    for relationship_type in sorted(EVALUATED_TYPES):
        discovered_for_type = {rel for rel in discovered if rel[1] == relationship_type}
        truth_for_type = {rel for rel in ground_truth if rel[1] == relationship_type}
        for key, value in _precision_recall_f1(discovered_for_type, truth_for_type).items():
            metrics[f"{relationship_type.lower()}_{key}"] = value
    return metrics


def _precision_recall_f1(discovered: set[tuple[str, str, str]], ground_truth: set[tuple[str, str, str]]) -> dict[str, float]:
    true_positive = len(discovered & ground_truth)
    precision = true_positive / len(discovered) if discovered else 0.0
    recall = true_positive / len(ground_truth) if ground_truth else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "relationship_precision": round(precision, 3),
        "relationship_recall": round(recall, 3),
        "relationship_f1": round(f1, 3),
    }
