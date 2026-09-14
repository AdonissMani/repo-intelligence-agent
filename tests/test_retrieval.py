import unittest

from app.config.paths import ENTERPRISE_REPOS
from app.embeddings.provider import HashingEmbeddingProvider, SemanticEmbeddingProvider, cosine
from app.ingestion.parser import ingest_enterprise
from app.retrieval.lexical import BM25Index


class RetrievalTests(unittest.TestCase):
    def test_lexical_ranking_uses_repository_text(self):
        repos = ingest_enterprise(ENTERPRISE_REPOS)
        scores = BM25Index(repos).search("merchant settlement views")
        self.assertEqual(max(scores, key=scores.get), "merchant-service")

    def test_hashing_embedding_provider_is_offline(self):
        provider = HashingEmbeddingProvider()
        left = provider.embed("refund payment")
        right = provider.embed("payment refund")
        self.assertAlmostEqual(cosine(left, right), 1.0)

    def test_semantic_embedding_provider_can_be_configured_without_calling_network(self):
        provider = SemanticEmbeddingProvider(model="test-model", endpoint="https://example.invalid", api_key="token")
        self.assertEqual(provider.model, "test-model")


if __name__ == "__main__":
    unittest.main()
