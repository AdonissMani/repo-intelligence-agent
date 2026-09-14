import unittest
from pathlib import Path

from app.config.paths import ENTERPRISE_REPOS
from app.graph.extractor import extract_relationships
from app.ingestion.parser import ingest_enterprise
from app.routing.router import RepositoryRouter


def build_router():
    repos = ingest_enterprise(ENTERPRISE_REPOS)
    return RepositoryRouter(repos, extract_relationships(ENTERPRISE_REPOS, repos))


class RouterTests(unittest.TestCase):
    def test_strategy_selection_includes_lexical(self):
        results, _ = build_router().route("merchant settlement views", strategy="lexical")
        self.assertEqual(results[0].name, "merchant-service")

    def test_adaptive_strategy_stops_early_for_direct_question(self):
        results, stats = build_router().route("Which repository owns customer contact preferences?", strategy="adaptive")
        self.assertEqual(results[0].name, "customer-profile")
        self.assertTrue(stats["adaptive_sufficient"])
        self.assertIn(stats["adaptive_stop_reason"], {"HIGH_CONFIDENCE", "HIGH_MARGIN"})

    def test_adaptive_strategy_expands_for_multi_repo_question(self):
        results, stats = build_router().route("What systems are involved when a merchant requests a refund?", strategy="adaptive")
        self.assertTrue(len(results) >= 3)
        self.assertGreaterEqual(stats["adaptive_depth_reached"], 1)
        self.assertTrue(stats["adaptive_rounds"] >= 1)

    def test_invalid_strategy_raises(self):
        with self.assertRaises(ValueError):
            build_router().route("anything", strategy="answer_key")

    def test_graph_depth_changes_path_availability(self):
        router = build_router()
        shallow, _ = router.route("merchant payment ledger", strategy="graph", graph_depth=0)
        deeper, _ = router.route("merchant payment ledger", strategy="graph", graph_depth=2)
        self.assertTrue(all(len(result.path or []) <= 1 for result in shallow))
        self.assertTrue(any(result.path and len(result.path) > 1 for result in deeper))

    def test_router_has_no_benchmark_specific_phrase_rules(self):
        source = Path("app/routing/router.py").read_text()
        forbidden = ["refund eligibility", "production timeout", "payment timeout failures", "_domain_bonus"]
        for phrase in forbidden:
            self.assertNotIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
