import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


def test_live_does_not_need_database():
    with patch("app.main.check_database", side_effect=RuntimeError):
        with TestClient(app) as client:
            assert client.get("/api/health/live").json() == {"status": "ok"}


def test_ready_reports_database_success():
    with patch("app.main.check_database"):
        with TestClient(app) as client:
            assert client.get("/api/health/ready").status_code == 200


def test_ready_failure_does_not_expose_credentials():
    with patch("app.main.check_database", side_effect=RuntimeError("private-password")):
        with TestClient(app) as client:
            response = client.get("/api/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "private-password" not in response.text


def test_database_password_with_url_characters():
    settings = Settings(password="p@ss:/%word")
    assert settings.database_url.password == "p@ss:/%word"
    assert "p@ss" not in str(settings.database_url)


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_real_database_ready():
    with TestClient(app) as client:
        assert client.get("/api/health/ready").status_code == 200
