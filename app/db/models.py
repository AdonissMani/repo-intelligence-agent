from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RepositoryRecord:
    name: str
    team: str
    business_unit: str
    domain: str
    type: str
    provides: list[str] = field(default_factory=list)
    consumes: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    consumed_by: list[str] = field(default_factory=list)
    publishes: list[str] = field(default_factory=list)
    subscribes: list[str] = field(default_factory=list)
    data_owned: list[str] = field(default_factory=list)
    criticality: str = "medium"
    apis: list[str] = field(default_factory=list)
    documents: dict[str, str] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    source: str
    type: str
    target: str
    evidence: str
