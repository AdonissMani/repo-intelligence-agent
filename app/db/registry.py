from __future__ import annotations

from dataclasses import asdict
import json

from app.config.paths import DATA_DIR, REGISTRY_PATH
from app.db.models import Relationship, RepositoryRecord


def save_registry(repositories: list[RepositoryRecord], relationships: list[Relationship]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "repositories": [asdict(repo) for repo in repositories],
        "relationships": [asdict(rel) for rel in relationships],
    }
    REGISTRY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_registry() -> tuple[list[RepositoryRecord], list[Relationship]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    repositories = [RepositoryRecord(**item) for item in payload["repositories"]]
    relationships = [Relationship(**item) for item in payload["relationships"]]
    return repositories, relationships
