import unittest

from app.config.paths import ENTERPRISE_REPOS
from app.graph.extractor import extract_relationships
from app.ingestion.parser import ingest_enterprise


class IngestionTests(unittest.TestCase):
    def test_ingests_expected_repository_count(self):
        repos = ingest_enterprise(ENTERPRISE_REPOS)
        self.assertEqual(len(repos), 15)

    def test_required_metadata_fields_are_present(self):
        repos = ingest_enterprise(ENTERPRISE_REPOS)
        for repo in repos:
            self.assertTrue(repo.name)
            self.assertTrue(repo.team)
            self.assertTrue(repo.business_unit)
            self.assertTrue(repo.domain)
            self.assertTrue(repo.type)

    def test_discovers_documents(self):
        repo = next(repo for repo in ingest_enterprise(ENTERPRISE_REPOS) if repo.name == "payment-core")
        self.assertIn("README.md", repo.documents)
        self.assertIn("docs/RUNBOOK.md", repo.documents)

    def test_extracts_payment_dependencies(self):
        repos = ingest_enterprise(ENTERPRISE_REPOS)
        rels = extract_relationships(ENTERPRISE_REPOS, repos)
        self.assertTrue(
            any(rel.source == "payment-core" and rel.type == "DEPENDS_ON" and rel.target == "ledger-core" for rel in rels)
        )


if __name__ == "__main__":
    unittest.main()
