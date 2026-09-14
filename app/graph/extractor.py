from __future__ import annotations

from pathlib import Path
import re

from app.db.models import Relationship, RepositoryRecord


SERVICE_PATTERN = re.compile(r"['\"]([a-z][a-z0-9-]+(?:-[a-z0-9]+)+)['\"]")
EVENT_PATTERN = re.compile(r"['\"]([A-Z][A-Za-z]+(?:Created|Verified|Authorized|Captured|Requested|Failed|Approved|Rejected|Completed|Posted|Renewed|Suspended|Collected|Calculated))['\"]")
API_PATTERN = re.compile(r"['\"]((?:GET|POST|PATCH|DELETE) /v1/[^'\"]+)['\"]")


def metadata_relationships(repo: RepositoryRecord) -> list[Relationship]:
    rels: list[Relationship] = []
    for dep in repo.depends_on:
        rels.append(Relationship(repo.name, "DEPENDS_ON", dep, "SERVICE.yaml depends_on"))
    for consumer in repo.consumed_by:
        rels.append(Relationship(consumer, "CONSUMES", repo.name, "SERVICE.yaml consumed_by"))
    for api in repo.apis:
        rels.append(Relationship(repo.name, "EXPOSES_API", api, "SERVICE.yaml apis"))
    for event in repo.publishes:
        rels.append(Relationship(repo.name, "PRODUCES_EVENT", event, "SERVICE.yaml publishes"))
    for event in repo.subscribes:
        rels.append(Relationship(repo.name, "CONSUMES_EVENT", event, "SERVICE.yaml subscribes"))
    rels.append(Relationship(repo.name, "OWNED_BY", repo.team, "SERVICE.yaml team"))
    rels.append(Relationship(repo.name, "IN_BUSINESS_UNIT", repo.business_unit, "SERVICE.yaml business_unit"))
    return rels


def code_relationships(repo_dir: Path, known_repos: set[str], source: str) -> list[Relationship]:
    rels: list[Relationship] = []
    for path in repo_dir.rglob("*"):
        if path.suffix not in {".py", ".md", ".yaml", ".yml", ".tf", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        evidence = str(path.relative_to(repo_dir))
        for service in SERVICE_PATTERN.findall(text):
            if service in known_repos and service != source:
                rels.append(Relationship(source, "REFERENCES_SERVICE", service, evidence))
        for api in API_PATTERN.findall(text):
            rels.append(Relationship(source, "REFERENCES_API", api, evidence))
        for event in EVENT_PATTERN.findall(text):
            rels.append(Relationship(source, "REFERENCES_EVENT", event, evidence))
    return rels


def extract_relationships(root: Path, repositories: list[RepositoryRecord]) -> list[Relationship]:
    known = {repo.name for repo in repositories}
    rels: list[Relationship] = []
    for repo in repositories:
        rels.extend(metadata_relationships(repo))
        rels.extend(code_relationships(root / repo.name, known, repo.name))
    seen = set()
    unique = []
    for rel in rels:
        key = (rel.source, rel.type, rel.target, rel.evidence)
        if key not in seen:
            seen.add(key)
            unique.append(rel)
    return unique
