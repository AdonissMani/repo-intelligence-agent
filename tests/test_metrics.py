import unittest

from evaluation.metrics import mean_reciprocal_rank, path_accuracy, relevant_set_recall, top1_accuracy, topk_recall


class MetricsTests(unittest.TestCase):
    def test_ranking_metrics(self):
        predicted = ["ledger-core", "payment-core", "merchant-service"]
        self.assertEqual(top1_accuracy(predicted, ["payment-core"]), 0.0)
        self.assertEqual(topk_recall(predicted, ["payment-core"], 2), 1.0)
        self.assertEqual(mean_reciprocal_rank(predicted, ["payment-core"]), 0.5)
        self.assertAlmostEqual(relevant_set_recall(predicted, ["payment-core", "merchant-service"]), 1.0)

    def test_path_accuracy_matches_expected_edges(self):
        paths = [["merchant-service", "payment-core", "ledger-core"]]
        expected = ["merchant-service -> payment-core", "payment-core -> ledger-core"]
        self.assertEqual(path_accuracy(paths, expected), 1.0)


if __name__ == "__main__":
    unittest.main()
