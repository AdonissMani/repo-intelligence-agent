import unittest

from app.db.models import Relationship
from app.graph.extractor import extract_relationships
from app.graph.traversal import RepositoryGraph
from app.config.paths import ENTERPRISE_REPOS
from app.ingestion.parser import ingest_enterprise


class GraphTests(unittest.TestCase):
    def test_duplicate_relationships_are_removed(self):
        repos = ingest_enterprise(ENTERPRISE_REPOS)
        rels = extract_relationships(ENTERPRISE_REPOS, repos)
        keys = [(rel.source, rel.type, rel.target, rel.evidence) for rel in rels]
        self.assertEqual(len(keys), len(set(keys)))

    def test_graph_depth_controls_expansion_and_records_path(self):
        repos = {"merchant-service", "payment-core", "ledger-core"}
        graph = RepositoryGraph(
            [
                Relationship("merchant-service", "DEPENDS_ON", "payment-core", "test"),
                Relationship("payment-core", "DEPENDS_ON", "ledger-core", "test"),
            ],
            repos,
        )
        zero_hop = graph.expand({"merchant-service": 1.0}, depth=0)
        two_hop = graph.expand({"merchant-service": 1.0}, depth=2)
        self.assertNotIn("ledger-core", zero_hop)
        self.assertEqual(two_hop["ledger-core"].path, ["merchant-service", "payment-core", "ledger-core"])
        self.assertEqual(two_hop["ledger-core"].relationships, ["DEPENDS_ON", "DEPENDS_ON"])


if __name__ == "__main__":
    unittest.main()
