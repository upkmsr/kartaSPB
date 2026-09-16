import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-metro", name="OpenStreetMap Saint Petersburg metro", type="osm-overpass-snapshot",
    url="https://overpass-api.de/api/interpreter", license="ODbL 1.0",
    attribution="© OpenStreetMap contributors", priority=50,
    notes="Subway route relations, station nodes and entrance nodes in Petersburg area.",
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_metro.json"
LINE_BY_COLOR = {
    "red": "1", "blue": "2", "green": "3", "orange": "4", "purple": "5", "brown": "6"
}


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def _memberships(elements: list[dict[str, Any]]) -> dict[int, set[str]]:
    result: dict[int, set[str]] = defaultdict(set)
    for relation in elements:
        if relation.get("type") != "relation":
            continue
        line = relation.get("tags", {}).get("ref")
        if line:
            for member in relation.get("members", []):
                if member.get("type") == "node":
                    result[int(member["ref"])].add(str(line))
    return result


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    elements = payload.get("elements", [])
    memberships = _memberships(elements)
    seen_lines: set[str] = set()
    for element in elements:
        tags = element.get("tags", {})
        if element.get("type") == "relation" and tags.get("route") == "subway":
            line_ref = str(tags.get("ref", element["id"]))
            if line_ref in seen_lines:
                continue
            segments = [
                [[point["lon"], point["lat"]] for point in member["geometry"]]
                for member in element.get("members", []) if len(member.get("geometry", [])) >= 2
            ]
            if not segments:
                continue
            seen_lines.add(line_ref)
            yield f"relation-{element['id']}", element, ImportRecord(
                source_id=SOURCE.id, name=tags.get("name", f"Линия {line_ref}"),
                category_id="metro-line",
                geometry={"type": "MultiLineString", "coordinates": segments},
                description="Линия метро по данным OpenStreetMap",
                properties={"lineRef": line_ref, "lineColor": tags.get("colour"),
                            "osmId": element["id"]},
            )
        elif element.get("type") == "node" and tags.get("railway") in {
            "station", "subway_entrance"
        }:
            is_station = tags["railway"] == "station"
            category = "metro-station" if is_station else "metro-entrance"
            name = tags.get("name") or ("Вход в метро" if not is_station else None)
            if not name:
                continue
            line_refs = memberships.get(element["id"], set()).copy()
            if line := LINE_BY_COLOR.get(tags.get("colour")):
                line_refs.add(line)
            yield f"node-{element['id']}", element, ImportRecord(
                source_id=SOURCE.id, name=name, category_id=category,
                geometry={"type": "Point", "coordinates": [element["lon"], element["lat"]]},
                description=("Станция метро" if is_station else "Вход или выход метро")
                + " по данным OpenStreetMap",
                properties={
                    "lineRefs": sorted(line_refs),
                    "osmId": element["id"],
                    "interchange": len(line_refs) > 1,
                },
            )


def run() -> tuple[int, ImportStats]:
    return import_records(SOURCE, "metro", records(load_snapshot()))
