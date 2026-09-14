import unittest

from app.config.paths import ENTERPRISE_REPOS
from app.graph.extractor import extract_relationships
from app.ingestion.parser import ingest_enterprise


class IngestionTests(unittest.TestCase):
    def test_ingests_expected_repository_count(self):
        repos = ingest_enterprise(ENTERPRISE_REPOS)
        self.assertEqual(len(repos), 15)

    def test_extracts_payment_dependencies(self):
        repos = ingest_enterprise(ENTERPRISE_REPOS)
        rels = extract_relationships(ENTERPRISE_REPOS, repos)
        self.assertTrue(
            any(rel.source == "payment-core" and rel.type == "DEPENDS_ON" and rel.target == "ledger-core" for rel in rels)
        )


if __name__ == "__main__":
    unittest.main()
