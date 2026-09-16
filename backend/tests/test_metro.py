import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.main import app
from app.metro.importer import load_snapshot, records, run


def test_metro_snapshot_has_lines_stations_and_entrances():
    parsed = list(records(load_snapshot()))
    counts = {
        category: sum(item.category_id == category for _, _, item in parsed)
        for category in {"metro-line", "metro-station", "metro-entrance"}
    }
    assert counts == {"metro-line": 6, "metro-station": 72, "metro-entrance": 261}
    assert all(record_id.startswith(("relation-", "node-")) for record_id, _, _ in parsed)
    assert {item.geometry["type"] for _, _, item in parsed} == {"MultiLineString", "Point"}


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_metro_import_provenance_and_nearest_analysis():
    _, stats = run()
    assert stats.found == 339
    assert stats.errors == 0
    with get_engine().connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM project_objects WHERE source='osm-metro'")
            ).scalar_one()
            == 339
        )
        assert connection.execute(
            text(
                "SELECT bool_and(ST_IsValid(geometry)) FROM project_objects "
                "WHERE source='osm-metro'"
            )
        ).scalar_one()
    with TestClient(app) as client:
        response = client.get("/api/analysis/metro/nearest?lon=30.3158&lat=59.9391")
        assert response.status_code == 200
        result = response.json()
        assert result["method"] == "straight-line"
        assert result["distance_meters"] >= 0
        assert isinstance(result["lines"], list)
