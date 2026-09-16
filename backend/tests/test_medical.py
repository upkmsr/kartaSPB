import os
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import get_engine
from app.main import app
from app.medical.importer import facility_type, load_snapshot, ownership, records, run


def test_medical_snapshot_and_classification():
    parsed = list(records(load_snapshot()))
    counts = Counter(record.category_id for _, _, record in parsed)
    assert len(parsed) > 5000
    assert len({record_id for record_id, _, _ in parsed}) == len(parsed)
    for category in (
        "medical-pharmacy",
        "medical-hospital",
        "medical-dentistry",
        "medical-laboratory",
        "medical-diagnostic_center",
    ):
        assert counts[category] > 0
    names = [record.name for _, _, record in parsed]
    assert any("СМ-Клиника" in name for name in names)
    assert any("Немецкая семейная клиника" in name for name in names)
    assert ownership({"name": "Городская поликлиника"}) == "unknown"
    assert ownership({"operator:type": "government"}) == "public"
    assert ownership({"operator": "ООО «Медицинская компания»"}) == "private"
    assert facility_type({"amenity": "pharmacy", "name": "Аптека"}) == "pharmacy"


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_medical_import_api_and_provenance():
    _, first = run()
    _, second = run()
    assert first.found == second.found > 5000
    assert second.inserted == 0
    assert second.updated == second.duplicates == second.found
    assert second.errors == 0
    with get_engine().connect() as connection:
        assert (
            connection.execute(text("SELECT count(*) FROM medical_facilities")).scalar_one()
            == second.found
        )
        assert connection.execute(text("SELECT count(*) FROM medical_services")).scalar_one() > 0
        assert (
            connection.execute(text("SELECT count(*) FROM medical_organizations")).scalar_one() > 0
        )
        assert (
            connection.execute(
                text("""
            SELECT count(*) FROM object_provenance WHERE source_id='osm-medical'
        """)
            ).scalar_one()
            == second.found
        )
        assert connection.execute(
            text("""
            SELECT bool_and(ST_IsValid(geometry)) FROM project_objects WHERE source='osm-medical'
        """)
        ).scalar_one()
        owners = dict(
            connection.execute(
                text("""
            SELECT ownership_type,count(*) FROM medical_facilities GROUP BY ownership_type
        """)
            ).all()
        )
        assert owners["public"] > 0 and owners["private"] > 0 and owners["unknown"] > 0
        assert (
            connection.execute(
                text("""
            SELECT count(DISTINCT facility.object_id) FROM medical_facilities facility
            JOIN medical_organizations organization ON organization.id=facility.organization_id
                WHERE organization.name='Инвитро'
        """)
            ).scalar_one()
            > 1
        )
    with TestClient(app) as client:
        assert client.get("/api/medical?bbox=30.2,59.8,30.4,60.0").status_code == 200
        first_page = client.get("/api/medical?limit=1&offset=0").json()
        next_page = client.get("/api/medical?limit=1&offset=1").json()
        assert first_page[0]["id"] != next_page[0]["id"]
        assert (
            client.get("/api/medical?type=pharmacy&ownership=unknown&is_24h=true").status_code
            == 200
        )
        assert client.get("/api/medical?type=invalid").status_code == 422
        assert client.get("/api/medical/pharmacies.geojson").status_code == 422
        pharmacies = client.get("/api/medical/pharmacies.geojson?bbox=30.2,59.8,30.4,60.0").json()
        assert pharmacies["type"] == "FeatureCollection"
        assert len(pharmacies["features"]) > 0
        assert all(
            item["properties"]["facilityType"] == "pharmacy" for item in pharmacies["features"]
        )
        objects = client.get("/api/objects?excludeCategory=medical-pharmacy").json()
        assert all(item["categoryId"] != "medical-pharmacy" for item in objects)
