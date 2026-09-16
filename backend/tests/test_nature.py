import os

import pytest
from sqlalchemy import text

from app.database import get_engine
from app.nature.importer import load_snapshot, records, run


def test_nature_snapshot_has_real_green_and_water_geometry():
    parsed = list(records(load_snapshot()))
    assert len(parsed) >= 1000
    categories = {item.category_id for _, _, item in parsed}
    assert categories == {"nature-green", "nature-water"}
    assert {item.geometry["type"] for _, _, item in parsed} >= {"Polygon", "LineString"}
    assert all(record_id.startswith("way-") for record_id, _, _ in parsed)


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_nature_import_and_provenance():
    _, stats = run()
    assert stats.found >= 1000
    assert stats.errors == 0
    with get_engine().connect() as connection:
        counts = dict(connection.execute(text("""
            SELECT category_id,count(*) FROM project_objects
            WHERE source='osm-nature' GROUP BY category_id
        """)).all())
        assert counts["nature-green"] > 0
        assert counts["nature-water"] > 0
        assert connection.execute(text("""
            SELECT bool_and(ST_IsValid(geometry)) FROM project_objects
            WHERE source='osm-nature'
        """)).scalar_one()
