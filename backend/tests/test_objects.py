import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import get_engine
from app.main import app
from app.seed_demo import seed


def test_repository_error_is_controlled():
    with patch(
        "app.objects.read_objects", side_effect=OperationalError("", {}, Exception("secret"))
    ):
        with TestClient(app) as client:
            response = client.get("/api/objects")
            assert response.status_code == 503
            assert "secret" not in response.text


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_objects_api_real_postgis():
    seed()
    seed()
    with TestClient(app) as client:
        categories = client.get("/api/categories")
        assert categories.status_code == 200
        assert {c["id"] for c in categories.json()} >= {"demo", "other"}
        response = client.get("/api/objects/demo-object-1")
        assert response.status_code == 200
        obj = response.json()
        assert obj["id"] == "demo-object-1"
        assert obj["categoryId"] == "demo"
        assert obj["geometry"] == {"type": "Point", "coordinates": [30.3158, 59.9391]}
        assert obj["properties"]["demo"] is True
        assert client.get("/api/objects/missing-object").status_code == 404
        assert client.get("/api/objects?category=missing").json() == []
        assert client.get("/api/objects?category=").json() == []
        assert all(
            o["categoryId"] == "demo" for o in client.get("/api/objects?category=demo").json()
        )
        assert obj in client.get("/api/objects?category=demo,other").json()
        assert obj in client.get("/api/objects").json()
    with get_engine().connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0004_open_data"
        )
        assert (
            connection.execute(
                text("SELECT count(*) FROM project_objects WHERE id='demo-object-1'")
            ).scalar_one()
            == 1
        )
        assert connection.execute(
            text(
                "SELECT ST_IsValid(geometry) AND ST_SRID(geometry)=4326 "
                "FROM project_objects WHERE id='demo-object-1'"
            )
        ).scalar_one()
        index = connection.execute(
            text("SELECT indexdef FROM pg_indexes WHERE indexname='ix_project_objects_geometry'")
        ).scalar_one()
        assert "USING gist" in index


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_geometry_types_and_constraints():
    with get_engine().connect() as connection:
        transaction = connection.begin()
        try:
            for suffix, wkt in [
                ("line", "LINESTRING(30 59,30.1 59.1)"),
                ("polygon", "POLYGON((30 59,31 59,31 60,30 59))"),
            ]:
                connection.execute(
                    text("""INSERT INTO project_objects(id,name,category_id,geometry)
                    VALUES (:id,'Integration fixture','other',ST_GeomFromText(:wkt,4326))"""),
                    {"id": f"integration-{suffix}", "wkt": wkt},
                )
                assert connection.execute(
                    text("SELECT ST_IsValid(geometry) FROM project_objects WHERE id=:id"),
                    {"id": f"integration-{suffix}"},
                ).scalar_one()
        finally:
            transaction.rollback()
