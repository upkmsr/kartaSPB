import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-nature", name="OpenStreetMap nature features", type="osm-overpass-snapshot",
    url="https://overpass-api.de/api/interpreter", license="ODbL 1.0",
    attribution="© OpenStreetMap contributors", priority=50,
    notes="Named green/water ways in bounded Petersburg region snapshot.",
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_nature.json"
GREEN_KEYS = {"park", "garden", "forest", "grass", "recreation_ground", "wood"}
WATER_KEYS = {"water", "river", "canal", "embankment"}


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _kind(tags: dict[str, Any]) -> tuple[str, str] | None:
    for key in ("leisure", "landuse", "natural", "waterway", "man_made"):
        value = tags.get(key)
        if value in GREEN_KEYS:
            return "nature-green", str(value)
        if value in WATER_KEYS:
            return "nature-water", str(value)
    return None


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        classification = _kind(tags)
        geometry = element.get("geometry", [])
        if not tags.get("name") or not classification or len(geometry) < 2:
            continue
        category, kind = classification
        coordinates = [[point["lon"], point["lat"]] for point in geometry]
        closed = len(coordinates) >= 4 and coordinates[0] == coordinates[-1]
        geojson: dict[str, Any] = {
            "type": "Polygon" if closed else "LineString",
            "coordinates": [coordinates] if closed else coordinates,
        }
        record_id = f"{element['type']}-{element['id']}"
        yield record_id, element, ImportRecord(
            source_id=SOURCE.id, name=tags["name"], category_id=category,
            geometry=geojson, description="Природный объект по данным OpenStreetMap",
            properties={"natureType": kind, "osmType": element["type"],
                        "osmId": element["id"]},
        )


def run() -> tuple[int, ImportStats]:
    return import_records(SOURCE, "nature", records(load_snapshot()))
