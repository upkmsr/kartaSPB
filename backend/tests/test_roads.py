import os
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.main import app
from app.roads.importer import category, corridor, load_snapshot, records, run


def test_road_snapshot_has_real_corridors_and_junctions():
    parsed = list(records(load_snapshot()))
    counts = Counter(record.category_id for _, _, record in parsed)
    assert len(parsed) > 1000
    assert counts["road-major"] > 0
    assert counts["road-kad"] > 0
    assert counts["road-zsd"] > 0
    assert counts["road-interchange"] > 0
    assert len({record_id for record_id, _, _ in parsed}) == len(parsed)
    assert corridor({"ref": "А-118"}) == "kad"
    assert corridor({"name": "Западный скоростной диаметр"}) == "zsd"
    assert (
        category({"type": "node", "tags": {"highway": "motorway_junction"}}) == "road-interchange"
    )


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_road_import_spatial_api_and_idempotence():
    _, first = run()
    _, second = run()
    assert first.found == second.found > 1000
    assert second.inserted == 0
    assert second.updated == second.duplicates == second.found
    assert second.errors == 0
    with get_engine().connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM roads")).scalar_one() == second.found
        counts = dict(
            connection.execute(
                text("""
            SELECT corridor,count(*) FROM roads GROUP BY corridor
        """)
            ).all()
        )
        assert counts["kad"] > 0 and counts["zsd"] > 0
        assert connection.execute(
            text("""
            SELECT bool_and(ST_IsValid(geometry)) FROM project_objects WHERE source='osm-roads'
        """)
        ).scalar_one()
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM object_provenance WHERE source_id='osm-roads'
        """)
            ).scalar_one()
            == second.found
        )
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM pg_indexes WHERE indexname='ix_roads_geometry'
        """)
            ).scalar_one()
            == 1
        )
    with TestClient(app) as client:
        assert client.get("/api/roads?corridor=kad&limit=5").status_code == 200
        assert client.get("/api/roads?type=interchange&bbox=29.5,59.6,31.0,60.3").status_code == 200
        assert client.get("/api/roads?category=wrong").status_code == 422
        assert client.get("/api/roads/viewport.geojson").status_code == 422
        viewport = client.get(
            "/api/roads/viewport.geojson?bbox=29.5,59.6,31.0,60.3&category=road-kad&limit=20"
        ).json()
        assert viewport["type"] == "FeatureCollection"
        assert len(viewport["features"]) == 20
        assert all(item["properties"]["categoryId"] == "road-kad" for item in viewport["features"])
        nearest = client.get("/api/analysis/roads/nearest?lon=30.3158&lat=59.9391").json()
        assert nearest["method"] == "straight-line"
        for key in ("nearestMajorRoad", "nearestKad", "nearestZsd", "nearestInterchange"):
            assert nearest[key]["distanceMeters"] >= 0
        objects = client.get("/api/objects?excludeCategoryPrefix=road-").json()
        assert all(not item["categoryId"].startswith("road-") for item in objects)
