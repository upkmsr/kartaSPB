import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.main import app
from app.noise.importer import rail_records, road_influence, run
from app.roads.importer import run as run_roads


def test_rail_snapshot_and_qualitative_method():
    records = rail_records()
    assert len(records) > 500
    assert len({record_id for record_id, _, _ in records}) == len(records)
    assert all(item.category_id == "noise-railway" for _, _, item in records)
    assert all(item.properties["intensityDb"] is None for _, _, item in records)
    assert road_influence("motorway", None) == "high"
    assert road_influence("trunk", 4) == "high"
    assert road_influence("trunk", 2) == "medium"
    assert road_influence("primary_link", None) == "low"


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_noise_import_and_spatial_api():
    run_roads()
    (rail_id, rail), (road_id, road) = run()
    (_, rail_again), (_, road_again) = run()
    assert rail_id > 0 and road_id > rail_id
    assert rail.found > 500 and road.found > 1000
    assert rail.errors == road.errors == 0
    assert rail_again.found == rail.found and road_again.found == road.found
    assert rail_again.inserted == road_again.inserted == 0
    assert rail_again.updated == rail.found and road_again.updated == road.found
    with get_engine().connect() as connection:
        counts = dict(
            connection.execute(
                text("""
            SELECT noise_type,count(*) FROM noise_sources GROUP BY noise_type
        """)
            ).all()
        )
        assert counts == {"road_noise": road.found, "railway_noise": rail.found}
        assert connection.execute(
            text("""
            SELECT bool_and(ST_IsValid(object.geometry)) FROM noise_sources noise
            JOIN project_objects object ON object.id=noise.object_id
        """)
        ).scalar_one()
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM noise_sources WHERE intensity_db IS NOT NULL
              OR (noise_type='road_noise' AND origin_type!='estimated')
              OR (noise_type='railway_noise' AND origin_type!='unknown')
        """)
            ).scalar_one()
            == 0
        )
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM object_provenance WHERE source_id='osm-rail-noise'
        """)
            ).scalar_one()
            == rail.found
        )
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM object_provenance WHERE source_id='road-influence'
        """)
            ).scalar_one()
            == road.found
        )
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM pg_indexes WHERE indexname='ix_noise_geometry'
        """)
            ).scalar_one()
            == 1
        )
    with TestClient(app) as client:
        assert client.get("/api/noise?type=wrong").status_code == 422
        assert client.get("/api/noise/viewport.geojson").status_code == 422
        availability = client.get("/api/noise/availability").json()
        assert availability["road_noise"]["count"] == road.found
        assert availability["railway_noise"]["count"] == rail.found
        assert availability["aviation_noise"]["status"] == "no_data"
        assert availability["helicopter_noise"]["status"] == "no_data"
        assert availability["aviation_noise"]["checkedAt"] == "2026-09-16"
        assert availability["helicopter_noise"]["reason"]
        viewport = client.get(
            "/api/noise/viewport.geojson?bbox=30.1,59.8,30.6,60.1&type=railway_noise&limit=10"
        ).json()
        assert len(viewport["features"]) == 10
        assert all(
            item["properties"]["noiseType"] == "railway_noise" for item in viewport["features"]
        )
        point = client.get("/api/analysis/noise/point?lon=30.3158&lat=59.9391").json()
        assert point["road"]["distanceMeters"] >= 0
        assert point["railway"]["distanceMeters"] >= 0
        assert point["aviationZone"] is None and point["helicopter"] is None
        assert point["availableNoiseIntensityDb"] is None
        assert all(
            not item["categoryId"].startswith("noise-")
            for item in client.get("/api/objects?excludeCategoryPrefix=road-,noise-").json()
        )

    # An explicitly measured contour must remain distinct from estimated source lines.
    fixture_id = "noise-test-measured-contour"
    try:
        with get_engine().begin() as connection:
            connection.execute(
                text("""
                INSERT INTO project_objects(id,name,category_id,geometry,properties,source)
                VALUES (:id,'Test measured contour','noise-aviation',
                  ST_GeomFromText(:wkt,4326),
                  '{}'::jsonb,'test-fixture')
            """),
                {
                    "id": fixture_id,
                    "wkt": "POLYGON((30.30 59.93,30.33 59.93,30.33 59.95,30.30 59.95,30.30 59.93))",
                },
            )
            connection.execute(
                text("""
                INSERT INTO noise_sources(object_id,noise_type,origin_type,confidence_label,
                  influence_class,intensity_db,source_checked_at,method)
                VALUES (:id,'aviation_noise','measured','HIGH',NULL,65,now(),'test fixture')
            """),
                {"id": fixture_id},
            )
        with TestClient(app) as client:
            point = client.get("/api/analysis/noise/point?lon=30.3158&lat=59.9391").json()
            assert point["aviationZone"]["id"] == fixture_id
            assert point["availableNoiseIntensityDb"] == 65
            outside = client.get("/api/analysis/noise/point?lon=30.5&lat=59.9391").json()
            assert outside["aviationZone"] is None
    finally:
        with get_engine().begin() as connection:
            connection.execute(text("DELETE FROM project_objects WHERE id=:id"), {"id": fixture_id})
