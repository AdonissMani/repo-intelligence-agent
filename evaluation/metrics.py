from __future__ import annotations


def top1_accuracy(predicted: list[str], primary: list[str]) -> float:
    return float(bool(predicted) and predicted[0] in primary)


def top3_recall(predicted: list[str], relevant: list[str]) -> float:
    return float(bool(set(predicted[:3]) & set(relevant)))


def relevant_set_recall(predicted: list[str], relevant: list[str]) -> float:
    if not relevant:
        return 1.0
    return len(set(predicted) & set(relevant)) / len(set(relevant))
