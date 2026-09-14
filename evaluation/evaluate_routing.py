from __future__ import annotations

import json
from pathlib import Path
import time

from app.config.paths import ROOT
from app.db.registry import load_registry
from app.routing.router import RepositoryRouter
from evaluation.metrics import mean_reciprocal_rank, path_accuracy, relevant_set_recall, top1_accuracy, topk_recall
from evaluation.topology import discovered_relationship_set, load_ground_truth_relationships, topology_metrics


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
    report = {}
    run_records = []

    for strategy in ["lexical", "semantic", "metadata", "graph", "hybrid", "adaptive"]:
        depths = [0, 1, 2, 3] if strategy in {"graph", "hybrid"} else [0]
        if strategy == "adaptive":
            depths = [0]
        for graph_depth in depths:
            key = f"{strategy}_d{graph_depth}" if strategy in {"graph", "hybrid"} else strategy
            report[key] = _evaluate_strategy(router, questions, strategy, graph_depth, run_records)

    experiments_dir = ROOT / "experiments"
    experiments_dir.mkdir(exist_ok=True)
    run_path = experiments_dir / f"routing_run_{int(time.time())}.json"
    run_path.write_text(json.dumps(run_records, indent=2), encoding="utf-8")

    ground_truth = load_ground_truth_relationships(ROOT / "benchmarks" / "ground_truth" / "enterprise_graph.yaml")
    report["topology"] = topology_metrics(discovered_relationship_set(relationships), ground_truth)
    return report


def _evaluate_strategy(
    router: RepositoryRouter,
    questions: list[dict],
    strategy: str,
    graph_depth: int,
    run_records: list[dict],
) -> dict[str, float]:
    top1 = primary_top3 = set_recall = mrr = path_score = latency = tokens = explored = edges = depth = 0.0
    for item in questions:
        results, stats = router.route(item["question"], strategy=strategy, limit=5, graph_depth=graph_depth)
        predicted = [result.name for result in results]
        paths = [result.path for result in results if result.path]
        primary = item["primary_repositories"]
        secondary = item.get("secondary_repositories", [])
        relevant = list(dict.fromkeys(primary + secondary))
        top1 += top1_accuracy(predicted, primary)
        primary_top3 += topk_recall(predicted, primary, 3)
        set_recall += relevant_set_recall(predicted, relevant)
        mrr += mean_reciprocal_rank(predicted, primary)
        path_score += path_accuracy(paths, item.get("expected_relationships", []))
        latency += float(stats["latency_ms"])
        tokens += float(stats["tokens"])
        explored += float(stats.get("adaptive_nodes_expanded", stats.get("repositories_considered", 0)))
        edges += float(stats.get("adaptive_edges_traversed", sum(len(path) - 1 for path in paths if path)))
        depth += float(stats.get("adaptive_depth_reached", graph_depth))
        run_records.append({
            "question": item["question"],
            "strategy": strategy,
            "predicted_repositories": predicted,
            "primary_repositories": primary,
            "secondary_repositories": secondary,
            "graph_depth": graph_depth,
            "latency_ms": stats["latency_ms"],
            "tokens": stats["tokens"],
            "repositories_considered": stats["repositories_considered"],
            "exploration_nodes": stats.get("adaptive_nodes_expanded", len(predicted)),
            "exploration_edges": stats.get("adaptive_edges_traversed", sum(len(path) - 1 for path in paths if path)),
            "depth_reached": stats.get("adaptive_depth_reached", graph_depth),
            "success": bool(predicted and predicted[0] in primary),
            "paths": [
                {
                    "repository": result.name,
                    "path": result.path or [result.name],
                    "relationships": result.relationships or [],
                    "evidence": result.evidence or [],
                }
                for result in results
            ],
        })
    total = len(questions)
    return {
        "top1": round(top1 / total, 3),
        "primary_top3": round(primary_top3 / total, 3),
        "mrr": round(mrr / total, 3),
        "relevant_set_recall": round(set_recall / total, 3),
        "path_accuracy": round(path_score / total, 3),
        "avg_latency_ms": round(latency / total, 2),
        "avg_tokens": round(tokens / total, 2),
        "avg_repositories_explored": round(explored / total, 2),
        "avg_depth_reached": round(depth / total, 2),
        "avg_edges_traversed": round(edges / total, 2),
    }


def main() -> None:
    report = evaluate()
    topology = report.pop("topology")
    print("Topology Extraction")
    print(f"Relationship precision: {topology['relationship_precision']:.0%}")
    print(f"Relationship recall: {topology['relationship_recall']:.0%}")
    print(f"Relationship F1: {topology['relationship_f1']:.0%}")
    for relationship_type in ["depends_on", "consumes", "produces_event", "consumes_event"]:
        precision_key = f"{relationship_type}_relationship_precision"
        recall_key = f"{relationship_type}_relationship_recall"
        f1_key = f"{relationship_type}_relationship_f1"
        print(
            f"{relationship_type}: "
            f"P {topology[precision_key]:.0%}, "
            f"R {topology[recall_key]:.0%}, "
            f"F1 {topology[f1_key]:.0%}"
        )
    print("\nRouting Strategy Comparison")
    for strategy, metrics in report.items():
        if strategy == "topology":
            continue
        print(f"\n{strategy.title()}:")
        print(f"Top-1: {metrics['top1']:.0%}")
        print(f"Primary Top-3: {metrics['primary_top3']:.0%}")
        print(f"MRR: {metrics['mrr']:.3f}")
        print(f"Relevant-set recall: {metrics['relevant_set_recall']:.0%}")
        print(f"Path accuracy: {metrics['path_accuracy']:.0%}")
        print(f"Avg latency: {metrics['avg_latency_ms']} ms")
        print(
            "Exploration: "
            f"depth={metrics.get('avg_depth_reached', 0):.2f}, "
            f"nodes={metrics.get('avg_repositories_explored', 0):.2f}, "
            f"edges={metrics.get('avg_edges_traversed', 0):.2f}"
        )


if __name__ == "__main__":
    main()
