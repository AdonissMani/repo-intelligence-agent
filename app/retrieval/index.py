from __future__ import annotations

from app.db.models import RepositoryRecord
from app.embeddings.provider import EmbeddingProvider, cosine


def repository_text(repo: RepositoryRecord) -> str:
    docs = "\n".join(repo.documents.values())
    metadata = " ".join(repo.provides + repo.apis + repo.depends_on + repo.publishes + repo.subscribes + repo.data_owned)
    return f"{repo.name} {repo.team} {repo.business_unit} {repo.domain} {metadata}\n{docs}"


class RepositoryIndex:
    def __init__(self, repositories: list[RepositoryRecord], provider: EmbeddingProvider):
        self.repositories = repositories
        self.provider = provider
        self.vectors = {repo.name: provider.embed(repository_text(repo)) for repo in repositories}

    def search(self, question: str) -> dict[str, float]:
        query = self.provider.embed(question)
        return {repo.name: cosine(query, self.vectors[repo.name]) for repo in self.repositories}
