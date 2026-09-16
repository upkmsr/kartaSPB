"""Import tagged road ways and junction nodes from a dated OSM snapshot."""

import json
import re
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-roads",
    name="OpenStreetMap Petersburg major roads",
    type="osm-composite-snapshot",
    url="https://www.openstreetmap.org/copyright",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors",
    priority=50,
    notes=(
        "Bounded BBBike city PBF (2026-09-11) plus Overpass motorway/junction bbox "
        "(2026-07-15), deduplicated by OSM type/id. Retrieval URLs, timestamps and "
        "methods are retained in the snapshot. No inferred junctions."
    ),
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_roads.json"
ROAD_CLASSES = {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def corridor(tags: dict[str, Any]) -> str:
    ref = str(tags.get("ref", ""))
    names = " ".join(str(tags.get(key, "")) for key in ("name", "short_name", "official_name"))
    if re.search(r"(?:^|[^\w])[АA]-?118(?:$|[^\d])", ref, re.IGNORECASE) or re.search(
        r"\bКАД\b|Кольцев(?:ая|ой) автомобильн", names, re.IGNORECASE
    ):
        return "kad"
    if re.search(r"\bЗСД\b|Западн\w* скоростн\w* диаметр", names, re.IGNORECASE):
        return "zsd"
    return "other"


def road_type(element: dict[str, Any]) -> str:
    if element.get("type") == "node":
        return "interchange"
    highway = element.get("tags", {}).get("highway", "")
    if highway.endswith("_link"):
        return "ramp"
    return "motorway" if highway == "motorway" else "major"


def category(element: dict[str, Any]) -> str:
    kind = road_type(element)
    if kind == "interchange":
        return "road-interchange"
    road_corridor = corridor(element.get("tags", {}))
    if road_corridor != "other":
        return f"road-{road_corridor}"
    return "road-ramp" if kind == "ramp" else "road-major"


def lanes(tags: dict[str, Any]) -> int | None:
    value = str(tags.get("lanes", ""))
    return int(value) if value.isdecimal() and int(value) > 0 else None


def toll(tags: dict[str, Any]) -> bool | None:
    value = tags.get("toll")
    if value == "yes":
        return True
    if value == "no":
        return False
    return None


def confidence(tags: dict[str, Any]) -> float:
    return round(
        0.5
        + sum(
            0.1
            for present in (
                bool(tags.get("name") or tags.get("ref")),
                bool(tags.get("lanes")),
                bool(tags.get("maxspeed")),
                bool(tags.get("access")),
                tags.get("toll") in {"yes", "no"},
            )
            if present
        ),
        2,
    )


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        timestamp = element.get("_source_data_at") or payload.get("osm3s", {}).get(
            "timestamp_osm_base"
        )
        if element.get("type") == "way" and tags.get("highway") in ROAD_CLASSES:
            points = element.get("geometry", [])
            if len(points) < 2:
                continue
            geometry: dict[str, Any] = {
                "type": "LineString",
                "coordinates": [[point["lon"], point["lat"]] for point in points],
            }
        elif element.get("type") == "node" and tags.get("highway") == "motorway_junction":
            if "lon" not in element or "lat" not in element:
                continue
            geometry = {"type": "Point", "coordinates": [element["lon"], element["lat"]]}
        else:
            continue
        record_id = f"{element['type']}-{element['id']}"
        name = (
            tags.get("name")
            or tags.get("ref")
            or ("Транспортная развязка" if element["type"] == "node" else "Дорожный сегмент")
        )
        yield (
            record_id,
            element,
            ImportRecord(
                source_id=SOURCE.id,
                name=str(name),
                category_id=category(element),
                geometry=geometry,
                description="Дорожная инфраструктура по данным OpenStreetMap",
                properties={
                    "roadType": road_type(element),
                    "corridor": corridor(tags),
                    "roadClass": tags.get("highway"),
                    "ref": tags.get("ref"),
                    "operator": tags.get("operator"),
                    "access": tags.get("access"),
                    "toll": toll(tags),
                    "lanes": lanes(tags),
                    "maxspeed": tags.get("maxspeed"),
                    "sourceDataAt": timestamp,
                    "confidence": confidence(tags),
                },
                confidence=confidence(tags),
            ),
        )


def _upsert(
    connection: Connection, object_id: str, record: ImportRecord, raw: dict[str, Any]
) -> None:
    tags = raw.get("tags", {})
    connection.execute(
        text("""
        INSERT INTO roads(object_id,road_type,corridor,road_class,ref,operator,access,toll,
          lanes,maxspeed,source_data_at,source_checked_at,confidence)
        VALUES (:id,:type,:corridor,:class,:ref,:operator,:access,:toll,:lanes,:maxspeed,
          :source_data,now(),:confidence)
        ON CONFLICT (object_id) DO UPDATE SET road_type=EXCLUDED.road_type,
          corridor=EXCLUDED.corridor,road_class=EXCLUDED.road_class,ref=EXCLUDED.ref,
          operator=EXCLUDED.operator,access=EXCLUDED.access,toll=EXCLUDED.toll,
          lanes=EXCLUDED.lanes,maxspeed=EXCLUDED.maxspeed,
          source_data_at=EXCLUDED.source_data_at,source_checked_at=EXCLUDED.source_checked_at,
          confidence=EXCLUDED.confidence
    """),
        {
            "id": object_id,
            "type": road_type(raw),
            "corridor": corridor(tags),
            "class": tags.get("highway"),
            "ref": tags.get("ref"),
            "operator": tags.get("operator"),
            "access": tags.get("access"),
            "toll": toll(tags),
            "lanes": lanes(tags),
            "maxspeed": tags.get("maxspeed"),
            "source_data": datetime.fromisoformat(
                record.properties["sourceDataAt"].replace("Z", "+00:00")
            ),
            "confidence": record.confidence,
        },
    )


def run() -> tuple[int, ImportStats]:
    return import_records(SOURCE, "roads", records(load_snapshot()), _upsert)
