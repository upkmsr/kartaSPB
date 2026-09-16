import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from app.education import address, confidence, operator_type, valid_check_date
from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-kindergartens",
    name="OpenStreetMap Petersburg kindergartens",
    type="osm-overpass-snapshot",
    url="https://overpass-api.de/api/interpreter",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors",
    priority=50,
    notes="All amenity=kindergarten nodes/ways/relations within Petersburg OSM area.",
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_kindergartens.json"


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        center = element.get("center", element)
        if not name or "lon" not in center or "lat" not in center:
            continue
        kind = operator_type(tags)
        yield (
            f"{element['type']}-{element['id']}",
            element,
            ImportRecord(
                source_id=SOURCE.id,
                name=name,
                category_id=f"kindergarten-{kind}",
                geometry={"type": "Point", "coordinates": [center["lon"], center["lat"]]},
                description="Детский сад по данным OpenStreetMap",
                address=address(tags),
                aliases=tuple(filter(None, [tags.get("alt_name")])),
                properties={
                    "operatorType": kind,
                    "address": address(tags),
                    "website": tags.get("website") or tags.get("contact:website"),
                    "sourceDataAt": payload.get("osm3s", {}).get("timestamp_osm_base"),
                    "objectCheckDate": tags.get("check_date"),
                    "confidence": confidence(tags),
                },
                confidence=confidence(tags),
            ),
        )


def _upsert_kindergarten(
    connection: Connection, object_id: str, record: ImportRecord, raw: dict[str, Any]
) -> None:
    tags = raw.get("tags", {})
    connection.execute(
        text("""
        INSERT INTO kindergartens(object_id,operator_type,address,official_id,website,
          source_checked_at,source_data_at,object_check_date,confidence)
        VALUES (:id,:operator,:address,:official,:website,now(),:source_data,
          :check_date,:confidence)
        ON CONFLICT (object_id) DO UPDATE SET operator_type=EXCLUDED.operator_type,
          address=EXCLUDED.address,official_id=EXCLUDED.official_id,website=EXCLUDED.website,
          source_checked_at=EXCLUDED.source_checked_at,source_data_at=EXCLUDED.source_data_at,
          object_check_date=EXCLUDED.object_check_date,confidence=EXCLUDED.confidence
    """),
        {
            "id": object_id,
            "operator": operator_type(tags),
            "address": address(tags),
            "official": tags.get("ref"),
            "website": tags.get("website") or tags.get("contact:website"),
            "source_data": datetime.fromisoformat(
                record.properties["sourceDataAt"].replace("Z", "+00:00")
            ),
            "check_date": valid_check_date(tags.get("check_date")),
            "confidence": record.confidence,
        },
    )


def run() -> tuple[int, ImportStats]:
    return import_records(SOURCE, "kindergartens", records(load_snapshot()), _upsert_kindergarten)
