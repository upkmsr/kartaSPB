import os

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.main import app
from app.roads.importer import run as run_roads
from app.user_geometries.api import validate_geometry


def test_geojson_validation():
    assert validate_geometry({"type": "Point", "coordinates": [30.3, 59.9]}) == "Point"
    for geometry in (
        {"type": "MultiPoint", "coordinates": [[30.3, 59.9]]},
        {"type": "Point", "coordinates": [181, 59.9]},
        {"type": "Point", "coordinates": [True, 59.9]},
        {"type": "LineString", "coordinates": [[30.3, 59.9]]},
        {"type": "Polygon", "coordinates": [[[30, 59], [31, 59], [31, 60]]]},
    ):
        with pytest.raises(HTTPException) as error:
            validate_geometry(geometry)
        assert error.value.status_code == 422


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_user_geometries_crud_persistence_and_import_isolation():
    shapes = [
        {"type": "Point", "coordinates": [30.31, 59.94]},
        {"type": "LineString", "coordinates": [[30.31, 59.94], [30.32, 59.95]]},
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [30.30, 59.93],
                    [30.32, 59.93],
                    [30.32, 59.95],
                    [30.30, 59.93],
                ]
            ],
        },
    ]
    ids = []
    try:
        with TestClient(app) as client:
            for index, shape in enumerate(shapes):
                response = client.post(
                    "/api/user/geometries",
                    json={
                        "name": f"User test {index}",
                        "description": "Persisted drawing",
                        "geometry": shape,
                    },
                )
                assert response.status_code == 201, response.text
                item = response.json()
                assert item["geometryType"] == shape["type"]
                ids.append(item["id"])
            listed = client.get("/api/user/geometries").json()
            assert {item["id"] for item in listed}.issuperset(ids)
            assert client.get(f"/api/user/geometries/{ids[0]}").json()["name"] == "User test 0"
            updated = client.patch(
                f"/api/user/geometries/{ids[1]}",
                json={
                    "name": "Edited line",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[30.31, 59.94], [30.34, 59.96]],
                    },
                },
            )
            assert updated.status_code == 200, updated.text
            assert updated.json()["name"] == "Edited line"
            assert updated.json()["geometry"]["coordinates"][1] == [30.34, 59.96]
            for invalid in (
                {"type": "MultiPolygon", "coordinates": []},
                {"type": "LineString", "coordinates": [[30, 59]]},
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [30.30, 59.93],
                            [30.32, 59.95],
                            [30.30, 59.95],
                            [30.32, 59.93],
                            [30.30, 59.93],
                        ]
                    ],
                },
            ):
                assert (
                    client.post(
                        "/api/user/geometries",
                        json={
                            "name": "Invalid",
                            "geometry": invalid,
                        },
                    ).status_code
                    == 422
                )
            assert (
                client.patch(
                    f"/api/user/geometries/{ids[0]}",
                    json={
                        "geometry": {"type": "Point", "coordinates": [190, 50]},
                    },
                ).status_code
                == 422
            )
        with get_engine().connect() as connection:
            result = connection.execute(
                text("""
                SELECT count(*),bool_and(ST_IsValid(geometry)) FROM user_geometries
                WHERE id::text=ANY(CAST(:ids AS text[]))
            """),
                {"ids": ids},
            ).one()
            assert result == (3, True)
            assert (
                connection.execute(
                    text("""
                SELECT count(*) FROM project_objects WHERE id=ANY(CAST(:ids AS text[]))
            """),
                    {"ids": ids},
                ).scalar_one()
                == 0
            )
        run_roads()
        with TestClient(app) as client:
            assert client.get(f"/api/user/geometries/{ids[0]}").status_code == 200
            assert client.get(f"/api/user/geometries/{ids[1]}").json()["name"] == "Edited line"
            for geometry_id in ids:
                assert client.delete(f"/api/user/geometries/{geometry_id}").status_code == 204
                assert client.get(f"/api/user/geometries/{geometry_id}").status_code == 404
    finally:
        with get_engine().begin() as connection:
            connection.execute(
                text("""
                DELETE FROM user_geometries WHERE id::text=ANY(CAST(:ids AS text[]))
            """),
                {"ids": ids},
            )
