import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.main import app
from app.schools.importer import load_snapshot, records, run


def test_school_snapshot_is_broad_real_source():
    parsed = list(records(load_snapshot()))
    assert len(parsed) > 1000
    assert len({record_id for record_id, _, _ in parsed}) == len(parsed)
    assert {item.properties["schoolType"] for _, _, item in parsed} >= {
        "school",
        "lyceum",
        "gymnasium",
    }
    assert {item.properties["operatorType"] for _, _, item in parsed} >= {"public", "private"}
    assert all(item.geometry["type"] == "Point" for _, _, item in parsed)


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_school_import_api_and_catchment_uncertainty():
    _, first = run()
    _, second = run()
    assert first.found == second.found > 1000
    assert second.inserted == 0
    assert second.updated == second.duplicates == second.found
    assert second.errors == 0
    with get_engine().connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM schools")).scalar_one() == second.found
        assert connection.execute(
            text("""
            SELECT bool_and(ST_IsValid(geometry)) FROM project_objects WHERE source='osm-schools'
        """)
        ).scalar_one()
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM object_provenance WHERE source_id='osm-schools'
        """)
            ).scalar_one()
            == second.found
        )
    with TestClient(app) as client:
        assert len(client.get("/api/schools?limit=2000").json()) == second.found
        assert client.get("/api/schools?bbox=30.2,59.8,30.4,60.0").status_code == 200
        assert client.get("/api/schools?bbox=bad").status_code == 422
        catchments = client.get("/api/schools/catchments").json()
        assert catchments["status"] == "no_verified_polygons"
        assert catchments["sources"][0]["representation"] == "address_list"
