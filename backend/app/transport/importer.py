import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-transport",
    name="OpenStreetMap surface transport sample",
    type="osm-overpass-snapshot",
    url="https://overpass-api.de/api/interpreter",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors",
    priority=50,
    notes="Deterministic sample of three route relations per supported transport type.",
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_transport.json"
ROUTE_TYPES = {"bus", "tram", "trolleybus"}


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    elements = payload.get("elements", [])
    stop_routes: dict[int, list[dict[str, str]]] = defaultdict(list)
    for relation in elements:
        tags = relation.get("tags", {})
        route_type = tags.get("route")
        if relation.get("type") != "relation" or route_type not in ROUTE_TYPES:
            continue
        route_ref = str(tags.get("ref", relation["id"]))
        for member in relation.get("members", []):
            if member.get("type") == "node" and member.get("role") in {
                "stop",
                "platform",
                "stop_entry_only",
                "stop_exit_only",
            }:
                stop_routes[int(member["ref"])].append(
                    {
                        "type": route_type,
                        "ref": route_ref,
                        "id": f"osm-transport-relation-{relation['id']}",
                    }
                )
        segments = [
            [[point["lon"], point["lat"]] for point in member["geometry"]]
            for member in relation.get("members", [])
            if len(member.get("geometry", [])) >= 2
        ]
        if segments:
            yield (
                f"relation-{relation['id']}",
                relation,
                ImportRecord(
                    source_id=SOURCE.id,
                    name=tags.get("name", f"Маршрут {route_ref}"),
                    category_id=f"transport-{route_type}",
                    geometry={"type": "MultiLineString", "coordinates": segments},
                    description="Маршрут наземного транспорта по данным OpenStreetMap",
                    properties={
                        "routeType": route_type,
                        "routeRef": route_ref,
                        "directionFrom": tags.get("from"),
                        "directionTo": tags.get("to"),
                        "osmId": relation["id"],
                    },
                ),
            )
    for node in elements:
        tags = node.get("tags", {})
        if node.get("type") != "node" or node["id"] not in stop_routes:
            continue
        routes = stop_routes[node["id"]]
        yield (
            f"node-{node['id']}",
            node,
            ImportRecord(
                source_id=SOURCE.id,
                name=tags.get("name", "Остановка"),
                category_id="transport-stop",
                geometry={"type": "Point", "coordinates": [node["lon"], node["lat"]]},
                description="Остановка наземного транспорта по данным OpenStreetMap",
                properties={
                    "routes": routes,
                    "routeTypes": sorted({r["type"] for r in routes}),
                    "routeRefs": sorted({r["ref"] for r in routes}),
                    "routeIds": sorted({r["id"] for r in routes}),
                    "osmId": node["id"],
                },
            ),
        )


def run() -> tuple[int, ImportStats]:
    return import_records(SOURCE, "transport", records(load_snapshot()))
