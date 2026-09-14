import unittest

from app.config.paths import ENTERPRISE_REPOS
from app.graph.extractor import extract_relationships
from app.ingestion.parser import ingest_enterprise
from app.routing.router import RepositoryRouter


def build_router():
    repos = ingest_enterprise(ENTERPRISE_REPOS)
    return RepositoryRouter(repos, extract_relationships(ENTERPRISE_REPOS, repos))


class RouterTests(unittest.TestCase):
    def test_routes_refund_eligibility_to_payment_core(self):
        results, _ = build_router().route("Where is refund eligibility decided?", strategy="hybrid")
        self.assertEqual(results[0].name, "payment-core")

    def test_routes_payment_timeout_to_deployment_platform(self):
        results, _ = build_router().route("Where is the production timeout for payment-core configured?", strategy="hybrid")
        self.assertEqual(results[0].name, "deployment-platform")


if __name__ == "__main__":
    unittest.main()
