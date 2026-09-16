import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.main import app
from app.transport.importer import load_snapshot, records, run


def test_transport_snapshot_separates_routes_and_stops():
    parsed = list(records(load_snapshot()))
    routes = [item for _, _, item in parsed if item.category_id != "transport-stop"]
    stops = [item for _, _, item in parsed if item.category_id == "transport-stop"]
    assert len(routes) == 9
    assert len(stops) == 441
    assert {item.category_id for item in routes} == {
        "transport-bus",
        "transport-tram",
        "transport-trolleybus",
    }
    assert all(item.geometry["type"] == "MultiLineString" for item in routes)
    assert all(item.geometry["type"] == "Point" for item in stops)
    assert all(item.properties["routeIds"] for item in stops)
    assert len({record_id for record_id, _, _ in parsed}) == 450


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_transport_import_provenance_and_nearby_analysis():
    _, first = run()
    _, second = run()
    assert first.found == second.found == 450
    assert second.inserted == 0
    assert second.updated == second.duplicates == 450
    assert second.errors == 0
    with get_engine().connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM project_objects WHERE source='osm-transport'")
            ).scalar_one()
            == 450
        )
        assert connection.execute(
            text(
                "SELECT bool_and(ST_IsValid(geometry)) FROM project_objects "
                "WHERE source='osm-transport'"
            )
        ).scalar_one()
    with TestClient(app) as client:
        response = client.get("/api/analysis/transport/nearby?lon=30.3158&lat=59.9391&radius=1000")
        assert response.status_code == 200
        result = response.json()
        assert result["method"] == "straight-line"
        assert result["nearbyStopCount"] >= len(result["nearestStops"])
        assert result["nearbyRouteCount"] >= 0
        assert all("id" in route for stop in result["nearestStops"] for route in stop["routes"])
