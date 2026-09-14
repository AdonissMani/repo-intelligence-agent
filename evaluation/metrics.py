from __future__ import annotations


def top1_accuracy(predicted: list[str], primary: list[str]) -> float:
    return float(bool(predicted) and predicted[0] in primary)


def topk_recall(predicted: list[str], relevant: list[str], k: int) -> float:
    return float(bool(set(predicted[:k]) & set(relevant)))


def top3_recall(predicted: list[str], relevant: list[str]) -> float:
    return topk_recall(predicted, relevant, 3)


def relevant_set_recall(predicted: list[str], relevant: list[str]) -> float:
    if not relevant:
        return 1.0
    return len(set(predicted) & set(relevant)) / len(set(relevant))


def mean_reciprocal_rank(predicted: list[str], primary: list[str]) -> float:
    primary_set = set(primary)
    for index, repo in enumerate(predicted, start=1):
        if repo in primary_set:
            return 1.0 / index
    return 0.0


def path_accuracy(result_paths: list[list[str]], expected_relationships: list[str]) -> float:
    expected_edges = []
    for relationship in expected_relationships:
        if " -> " in relationship:
            parts = [part.strip() for part in relationship.split(" -> ")]
            expected_edges.extend(zip(parts, parts[1:]))
    if not expected_edges:
        return 0.0
    discovered_edges = set()
    for path in result_paths:
        discovered_edges.update(zip(path, path[1:]))
    if not discovered_edges:
        return 0.0
    return len(set(expected_edges) & discovered_edges) / len(set(expected_edges))
