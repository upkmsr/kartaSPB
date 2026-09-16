import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.ingestion.deduplicate import match_key
from app.ingestion.models import ImportRecord, SourceDefinition
from app.ingestion.normalize import (
    normalize_coordinates,
    normalize_identifier,
    normalize_name,
    remove_empty,
)
from app.ingestion.pipeline import canonical_id, import_records
from app.ingestion.validate import validate_record
from app.main import app


def record(**overrides: object) -> ImportRecord:
    values: dict[str, object] = {
        "source_id": "fixture", "name": "  Летний   сад ", "category_id": "demo",
        "geometry": {"type": "Point", "coordinates": [30.335, 59.945]},
        "address": " Санкт-Петербург ", "aliases": ("Summer Garden",),
    }
    values.update(overrides)
    return ImportRecord(**values)  # type: ignore[arg-type]


def test_normalization_validation_and_match_key():
    assert normalize_name("  ЛЕТНИЙ  сад ") == "летний сад"
    assert normalize_identifier("Open Data: 42") == "open-data:-42"
    assert normalize_coordinates([30.3, 59.9]) == (30.3, 59.9)
    assert normalize_coordinates([300, 59.9]) is None
    assert remove_empty({"blank": "  ", "name": "  Сад  "}) == {"name": "Сад"}
    assert validate_record(record()).valid
    assert not validate_record(record(geometry={"type": "Point", "coordinates": [0, 0]})).valid
    key = match_key(record())
    assert key.normalized_name == "летний сад"
    assert key.address == "санкт-петербург"
    assert key.longitude == 30.335
    assert canonical_id("Fixture", "Point 1") == "fixture-point-1"


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_idempotent_import_staging_provenance_and_api():
    source = SourceDefinition(
        id="integration-fixture", name="Integration fixture", type="fixture",
        url="local://test_ingestion", license="project fixture", attribution="KARTASPB",
    )
    items = [(
        "same-1", {"raw": "value"}, record(source_id=source.id, category_id="other")
    )]
    first_run, first = import_records(source, "integration", items)
    second_run, second = import_records(source, "integration", items)
    assert first.inserted + first.updated == 1
    assert second.inserted == 0
    assert second.updated == second.duplicates == 1
    with get_engine().connect() as connection:
        assert connection.execute(text(
            "SELECT count(*) FROM project_objects WHERE id='integration-fixture-same-1'"
        )).scalar_one() == 1
        assert connection.execute(text(
            "SELECT count(*) FROM ingestion_staging WHERE run_id IN (:first,:second)"
        ), {"first": first_run, "second": second_run}).scalar_one() == 2
        assert connection.execute(text(
            "SELECT count(*) FROM object_provenance WHERE object_id='integration-fixture-same-1'"
        )).scalar_one() == 1
    with TestClient(app) as client:
        assert client.get("/api/import/status").status_code == 200
        assert client.get("/api/import/runs").status_code == 200
        assert client.get("/api/import/errors").status_code == 200
