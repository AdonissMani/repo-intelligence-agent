from __future__ import annotations

from pathlib import Path

from app.db.models import RepositoryRecord


LIST_FIELDS = {"provides", "consumes", "apis", "depends_on", "consumed_by", "publishes", "subscribes", "data_owned"}


def parse_simple_yaml(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current = key
            if value == "[]":
                data[key] = []
            elif value:
                data[key] = value
            elif key in LIST_FIELDS:
                data[key] = []
            else:
                data[key] = ""
        elif line.strip().startswith("- ") and current:
            data.setdefault(current, [])
            assert isinstance(data[current], list)
            data[current].append(line.strip()[2:])
    return data


def read_documents(repo_dir: Path) -> dict[str, str]:
    docs = {}
    for rel in ["README.md", "ARCHITECTURE.md", "API.md", "OWNERS"]:
        path = repo_dir / rel
        if path.exists():
            docs[rel] = path.read_text(encoding="utf-8")
    for path in (repo_dir / "docs").rglob("*.md") if (repo_dir / "docs").exists() else []:
        docs[str(path.relative_to(repo_dir))] = path.read_text(encoding="utf-8")
    return docs


def ingest_repository(repo_dir: Path) -> RepositoryRecord:
    metadata = parse_simple_yaml(repo_dir / "SERVICE.yaml")
    return RepositoryRecord(
        name=str(metadata["name"]),
        team=str(metadata["team"]),
        business_unit=str(metadata["business_unit"]),
        domain=str(metadata["domain"]),
        type=str(metadata["type"]),
        provides=list(metadata.get("provides", [])),
        consumes=list(metadata.get("consumes", [])),
        depends_on=list(metadata.get("depends_on", [])),
        consumed_by=list(metadata.get("consumed_by", [])),
        publishes=list(metadata.get("publishes", [])),
        subscribes=list(metadata.get("subscribes", [])),
        data_owned=list(metadata.get("data_owned", [])),
        criticality=str(metadata.get("criticality", "medium")),
        apis=list(metadata.get("apis", [])),
        documents=read_documents(repo_dir),
    )


def ingest_enterprise(root: Path) -> list[RepositoryRecord]:
    return [ingest_repository(path) for path in sorted(root.iterdir()) if (path / "SERVICE.yaml").exists()]
