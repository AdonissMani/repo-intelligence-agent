from __future__ import annotations

import json
from pathlib import Path
import time

from app.config.paths import ROOT
from app.db.registry import load_registry
from app.routing.router import RepositoryRouter
from evaluation.metrics import relevant_set_recall, top1_accuracy, top3_recall


def load_questions(path: Path) -> list[dict]:
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8"))["questions"]
    except ModuleNotFoundError:
        return _load_simple_questions(path)


def _load_simple_questions(path: Path) -> list[dict]:
    questions: list[dict] = []
    current: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip() == "questions:":
            continue
        if raw.startswith("  - "):
            if current:
                questions.append(current)
            current = {}
            key, value = raw[4:].split(":", 1)
            current[key.strip()] = _parse_value(value.strip())
        elif raw.startswith("    ") and current is not None:
            key, value = raw.strip().split(":", 1)
            current[key.strip()] = _parse_value(value.strip())
    if current:
        questions.append(current)
    return questions


def _parse_value(value: str):
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip() for item in inner.split(",")]
    return value


def evaluate() -> dict[str, dict[str, float]]:
    repositories, relationships = load_registry()
    router = RepositoryRouter(repositories, relationships)
    questions = load_questions(ROOT / "benchmarks" / "routing_questions.yaml")
    strategies = ["semantic", "metadata", "graph", "hybrid"]
    report = {}
    experiments_dir = ROOT / "experiments"
    experiments_dir.mkdir(exist_ok=True)
    run_records = []
    for strategy in strategies:
        top1 = top3 = set_recall = latency = tokens = explored = 0.0
        for item in questions:
            results, stats = router.route(item["question"], strategy=strategy, limit=5)
            predicted = [result.name for result in results]
            primary = item["primary_repositories"]
            relevant = list(dict.fromkeys(primary + item.get("secondary_repositories", [])))
            top1 += top1_accuracy(predicted, primary)
            top3 += top3_recall(predicted, relevant)
            set_recall += relevant_set_recall(predicted, relevant)
            latency += float(stats["latency_ms"])
            tokens += float(stats["tokens"])
            explored += float(stats["repositories_considered"])
            run_records.append({
                "question": item["question"],
                "strategy": strategy,
                "retrieved_repositories": predicted,
                "gold_repositories": relevant,
                "latency_ms": stats["latency_ms"],
                "tokens": stats["tokens"],
                "success": bool(predicted and predicted[0] in primary),
            })
        total = len(questions)
        report[strategy] = {
            "top1": round(top1 / total, 3),
            "top3": round(top3 / total, 3),
            "relevant_set_recall": round(set_recall / total, 3),
            "avg_latency_ms": round(latency / total, 2),
            "avg_tokens": round(tokens / total, 2),
            "avg_repositories_explored": round(explored / total, 2),
        }
    run_path = experiments_dir / f"routing_run_{int(time.time())}.json"
    run_path.write_text(json.dumps(run_records, indent=2), encoding="utf-8")
    return report


def main() -> None:
    report = evaluate()
    print("Routing Strategy Comparison")
    for strategy, metrics in report.items():
        print(f"\n{strategy.title()}:")
        print(f"Top-1: {metrics['top1']:.0%}")
        print(f"Top-3: {metrics['top3']:.0%}")
        print(f"Relevant-set recall: {metrics['relevant_set_recall']:.0%}")
        print(f"Avg latency: {metrics['avg_latency_ms']} ms")


if __name__ == "__main__":
    main()
