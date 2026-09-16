import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.kindergartens.importer import load_snapshot, records, run
from app.main import app


def test_kindergarten_snapshot_has_real_public_and_private_data():
    parsed = list(records(load_snapshot()))
    assert len(parsed) > 1400
    assert len({record_id for record_id, _, _ in parsed}) == len(parsed)
    assert {item.category_id for _, _, item in parsed} == {
        "kindergarten-public",
        "kindergarten-private",
        "kindergarten-unknown",
    }


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_kindergarten_import_api_and_proximity():
    _, first = run()
    _, second = run()
    assert first.found == second.found > 1400
    assert second.inserted == 0
    assert second.updated == second.duplicates == second.found
    assert second.errors == 0
    with get_engine().connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM kindergartens")).scalar_one()
            == second.found
        )
        counts = dict(
            connection.execute(
                text("SELECT operator_type,count(*) FROM kindergartens GROUP BY operator_type")
            ).all()
        )
        assert counts["public"] > 0 and counts["private"] > 0
        assert connection.execute(
            text("""
            SELECT bool_and(ST_IsValid(geometry)) FROM project_objects
            WHERE source='osm-kindergartens'
        """)
        ).scalar_one()
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM object_provenance WHERE source_id='osm-kindergartens'
        """)
            ).scalar_one()
            == second.found
        )
    with TestClient(app) as client:
        assert len(client.get("/api/kindergartens?limit=2000").json()) == second.found
        assert client.get("/api/kindergartens?bbox=30.2,59.8,30.4,60.0").status_code == 200
        assert client.get("/api/kindergartens?operator=private").status_code == 200
        nearby = client.get("/api/kindergartens/nearby?lon=30.3158&lat=59.9391").json()
        assert nearby["method"] == "straight-line"
        assert nearby["counts"]["total"] >= 0
        assert nearby["nearest"]["distance_meters"] >= 0
        assert (
            client.get("/api/kindergartens/admissions").json()["sources"][0]["representation"]
            == "text_rule"
        )
