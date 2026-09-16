import os

import pytest
from sqlalchemy import text

from app.database import get_engine
from app.open_data.overpass import SOURCE, load_snapshot, records, run


def test_checked_in_osm_snapshot_is_real_and_bounded():
    payload = load_snapshot()
    parsed = list(records(payload))
    assert len(parsed) == 18
    assert all(item.source_id == SOURCE.id for _, _, item in parsed)
    assert {raw["type"] for _, raw, _ in parsed} == {"relation"}
    assert len({record_id for record_id, _, _ in parsed}) == 18
    assert all(27 <= item.geometry["coordinates"][0] <= 32.5 for _, _, item in parsed)
    assert all(58 <= item.geometry["coordinates"][1] <= 61.5 for _, _, item in parsed)


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="Requires migrated PostGIS")
def test_open_data_import_is_repeatable_with_provenance():
    _, first = run()
    _, second = run()
    assert first.found == second.found == 18
    assert second.inserted == 0
    assert second.updated == second.duplicates == 18
    assert second.errors == 0
    with get_engine().connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM project_objects WHERE source='osm-overpass'")
            ).scalar_one()
            == 18
        )
        assert connection.execute(
            text(
                "SELECT bool_and(ST_IsValid(geometry)) FROM project_objects "
                "WHERE source='osm-overpass'"
            )
        ).scalar_one()
        assert (
            connection.execute(
                text("SELECT count(*) FROM object_provenance WHERE source_id='osm-overpass'")
            ).scalar_one()
            == 18
        )
