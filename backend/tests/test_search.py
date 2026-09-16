import os
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.search import NominatimProvider
from app.seed_demo import seed


class JsonResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_geocoder_normalizes_and_caches_provider_response():
    provider = NominatimProvider()
    response = (
        b'[{"osm_type":"node","osm_id":1,"display_name":"Place",'
        b'"lon":"30.3","lat":"59.9","type":"city"}]'
    )
    with patch("app.search.urllib.request.urlopen", return_value=JsonResponse(response)) as request:
        assert provider.search("Place", 5)[0].model_dump() == {
            "id": "nominatim-node-1",
            "label": "Place",
            "coordinates": (30.3, 59.9),
            "type": "city",
            "provider": "nominatim",
        }
        provider.search("Place", 5)
        assert request.call_count == 1


def test_geocoder_error_is_controlled():
    with patch("app.search.geocoder.search", side_effect=RuntimeError):
        with TestClient(app) as client:
            assert client.get("/api/search/geocode?q=address").status_code == 503


def test_search_query_validation():
    with TestClient(app) as client:
        assert client.get("/api/search/objects?q=").status_code == 422
        assert client.get("/api/search/geocode?q=ab").status_code == 422
        assert client.get("/api/search/objects?q=test&limit=51").status_code == 422


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_project_search_real_database():
    seed()
    with TestClient(app) as client:
        result = client.get("/api/search/objects?q=Тестовый").json()
        assert result[0]["id"] == "demo-object-1"
        assert (
            client.get("/api/search/objects?q=Демонстрационные").json()[0]["id"] == "demo-object-1"
        )
        assert client.get("/api/search/objects?q=unknown-object").json() == []
        assert len(client.get("/api/search/objects?q=объект&limit=1").json()) <= 1
