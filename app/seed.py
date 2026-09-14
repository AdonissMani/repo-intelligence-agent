from __future__ import annotations

from app.config.paths import ENTERPRISE_REPOS
from app.db.registry import save_registry
from app.graph.extractor import extract_relationships
from app.ingestion.parser import ingest_enterprise


def main() -> None:
    repositories = ingest_enterprise(ENTERPRISE_REPOS)
    relationships = extract_relationships(ENTERPRISE_REPOS, repositories)
    save_registry(repositories, relationships)
    print(f"Seeded {len(repositories)} repositories and {len(relationships)} relationships")


if __name__ == "__main__":
    main()
