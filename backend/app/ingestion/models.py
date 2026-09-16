from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceDefinition:
    id: str
    name: str
    type: str
    url: str
    license: str
    attribution: str
    priority: int = 100
    notes: str = ""


@dataclass(frozen=True)
class ImportRecord:
    source_id: str
    name: str
    category_id: str
    geometry: dict[str, Any]
    description: str = ""
    address: str | None = None
    aliases: tuple[str, ...] = ()
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class ImportStats:
    found: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    duplicates: int = 0
    warnings: int = 0
    errors: int = 0
