import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.normalize import normalize_name
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-schools",
    name="OpenStreetMap Petersburg schools",
    type="osm-overpass-snapshot",
    url="https://overpass-api.de/api/interpreter",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors",
    priority=50,
    notes="All amenity=school nodes/ways/relations within Petersburg OSM area.",
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_schools.json"


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def school_type(tags: dict[str, Any]) -> str:
    name = normalize_name(tags.get("name")) or ""
    if "лицей" in name:
        return "lyceum"
    if "гимнази" in name:
        return "gymnasium"
    if "специализирован" in name or tags.get("school:type") == "specialized":
        return "specialized"
    return "school"


def operator_type(tags: dict[str, Any]) -> str:
    value = tags.get("operator:type")
    return value if value in {"public", "private"} else "unknown"


def address(tags: dict[str, Any]) -> str | None:
    return (
        tags.get("addr:full")
        or ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:housenumber")]))
        or None
    )


def confidence(tags: dict[str, Any]) -> float:
    return round(
        0.5
        + sum(
            (
                0.1 if address(tags) else 0,
                0.1 if tags.get("website") or tags.get("contact:website") else 0,
                0.1 if tags.get("ref") else 0,
                0.1 if operator_type(tags) != "unknown" else 0,
            )
        ),
        2,
    )


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        center = element.get("center", element)
        if not name or "lon" not in center or "lat" not in center:
            continue
        record_id = f"{element['type']}-{element['id']}"
        yield (
            record_id,
            element,
            ImportRecord(
                source_id=SOURCE.id,
                name=name,
                category_id="school",
                geometry={"type": "Point", "coordinates": [center["lon"], center["lat"]]},
                description="Школа по данным OpenStreetMap",
                address=address(tags),
                aliases=tuple(filter(None, [tags.get("alt_name")])),
                properties={
                    "schoolType": school_type(tags),
                    "operatorType": operator_type(tags),
                    "address": address(tags),
                    "website": tags.get("website") or tags.get("contact:website"),
                    "sourceDataAt": payload.get("osm3s", {}).get("timestamp_osm_base"),
                    "objectCheckDate": tags.get("check_date"),
                    "confidence": confidence(tags),
                },
                confidence=confidence(tags),
            ),
        )


def _upsert_school(
    connection: Connection, object_id: str, record: ImportRecord, raw: dict[str, Any]
) -> None:
    tags = raw.get("tags", {})
    connection.execute(
        text("""
        INSERT INTO schools(object_id,school_type,operator_type,address,official_id,website,phone,
          source_checked_at,source_data_at,object_check_date,confidence)
        VALUES (:id,:type,:operator,:address,:official,:website,:phone,now(),:source_data,
          :check_date,:confidence)
        ON CONFLICT (object_id) DO UPDATE SET school_type=EXCLUDED.school_type,
          operator_type=EXCLUDED.operator_type,address=EXCLUDED.address,
          official_id=EXCLUDED.official_id,website=EXCLUDED.website,phone=EXCLUDED.phone,
          source_checked_at=EXCLUDED.source_checked_at,source_data_at=EXCLUDED.source_data_at,
          object_check_date=EXCLUDED.object_check_date,confidence=EXCLUDED.confidence
    """),
        {
            "id": object_id,
            "type": school_type(tags),
            "operator": operator_type(tags),
            "address": address(tags),
            "official": tags.get("ref"),
            "website": tags.get("website") or tags.get("contact:website"),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "source_data": datetime.fromisoformat(
                record.properties["sourceDataAt"].replace("Z", "+00:00")
            ),
            "check_date": tags.get("check_date") if _valid_date(tags.get("check_date")) else None,
            "confidence": record.confidence,
        },
    )


def _valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def run() -> tuple[int, ImportStats]:
    return import_records(SOURCE, "schools", records(load_snapshot()), _upsert_school)
