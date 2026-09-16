import json
import urllib.parse
import urllib.request
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-overpass",
    name="OpenStreetMap via Overpass API",
    type="osm-overpass",
    url="https://overpass-api.de/api/interpreter",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors",
    priority=50,
    notes="Bounded snapshots only; not a tile endpoint. Public instance has no SLA.",
)
DEFAULT_QUERY = (
    '[out:json][timeout:45];area(3600337422)->.searchArea;'
    'relation["boundary"="administrative"]["admin_level"="5"](area.searchArea);'
    "out tags center;"
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_district_centers.json"


def fetch(query: str = DEFAULT_QUERY) -> dict[str, Any]:
    request = urllib.request.Request(
        SOURCE.url,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": "KARTASPB/0.6 local GIS development"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)  # type: ignore[no-any-return]


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    for element in payload.get("elements", []):
        center = element.get("center")
        tags = element.get("tags", {})
        name = tags.get("name")
        if not center or not name:
            continue
        record_id = f"{element['type']}-{element['id']}"
        properties = {
            "osmType": element["type"], "osmId": element["id"],
            "adminLevel": tags.get("admin_level"), "boundary": tags.get("boundary"),
            "snapshotTimestamp": payload.get("osm3s", {}).get("timestamp_osm_base"),
        }
        yield record_id, element, ImportRecord(
            source_id=SOURCE.id, name=name, category_id="osm-base",
            geometry={"type": "Point", "coordinates": [center["lon"], center["lat"]]},
            description="Центр административного района по данным OpenStreetMap",
            properties=properties,
        )


def run(refresh: bool = False) -> tuple[int, ImportStats]:
    payload = fetch() if refresh else load_snapshot()
    return import_records(SOURCE, "open-data", records(payload))
