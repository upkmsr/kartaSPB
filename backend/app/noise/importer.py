"""Repeatable OSM rail import and transparent road influence extraction."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from app.database import get_engine
from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.pipeline import import_records

RAIL_SOURCE = SourceDefinition(
    id="osm-rail-noise",
    name="OSM Petersburg active rail alignments",
    type="osm-bbbike-snapshot",
    url="https://download.bbbike.org/osm/bbbike/SanktPetersburg/SanktPetersburg.osm.pbf",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors",
    priority=50,
    notes=(
        "BBBike city extract 2026-09-11; railway=rail without "
        "service=spur/siding/yard/crossover. Alignment is not measured acoustic exposure."
    ),
)
ROAD_SOURCE = SourceDefinition(
    id="road-influence",
    name="KARTASPB qualitative road influence",
    type="derived-estimate",
    url="https://www.openstreetmap.org/copyright",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors; KARTASPB qualitative classification",
    priority=60,
    notes=(
        "Derived from imported Roads geometry and OSM road_class/lanes. "
        "No traffic volume, fleet, time, propagation or measured dB; "
        "not a noise model or acoustic contour."
    ),
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_railway.json"
METHOD = "OSM alignment only; no acoustic measurement or propagation model"


def road_influence(road_class: str | None, lanes: int | None) -> str:
    """Potential exposure tier from road hierarchy/width, not sound intensity."""
    if road_class == "motorway" or (road_class == "trunk" and (lanes or 0) >= 4):
        return "high"
    if road_class in {"trunk", "primary"}:
        return "medium"
    return "low"


def rail_records() -> list[tuple[str, dict[str, Any], ImportRecord]]:
    payload = json.loads(SNAPSHOT.read_text())
    result = []
    for element in payload["elements"]:
        tags = element["tags"]
        if tags.get("railway") != "rail" or tags.get("service"):
            continue
        record_id = f"way-{element['id']}"
        result.append(
            (
                record_id,
                element,
                ImportRecord(
                    source_id=RAIL_SOURCE.id,
                    name=tags.get("name") or "Железнодорожный путь",
                    category_id="noise-railway",
                    geometry={"type": "LineString", "coordinates": element["geometry"]},
                    description="Положение железнодорожного пути; уровень шума неизвестен",
                    properties={
                        "noiseType": "railway_noise",
                        "originType": "unknown",
                        "confidenceLabel": "MEDIUM",
                        "sourceDataAt": element["_source_data_at"],
                        "method": METHOD,
                        "intensityDb": None,
                        "influenceClass": None,
                    },
                    confidence=0.6,
                ),
            )
        )
    return result


def road_records() -> list[tuple[str, dict[str, Any], ImportRecord]]:
    with get_engine().connect() as connection:
        rows = (
            connection.execute(
                text("""
            SELECT o.id,o.name,ST_AsGeoJSON(o.geometry)::json AS geojson,
              r.road_class,r.lanes,r.source_data_at
            FROM roads r JOIN project_objects o ON o.id=r.object_id
            WHERE r.road_type IN ('major','motorway','ramp')
            ORDER BY o.id
        """)
            )
            .mappings()
            .all()
        )
    result = []
    for row in rows:
        tier = road_influence(row["road_class"], row["lanes"])
        timestamp = row["source_data_at"].isoformat() if row["source_data_at"] else None
        raw = {
            "source_object_id": row["id"],
            "road_class": row["road_class"],
            "lanes": row["lanes"],
            "source_data_at": timestamp,
            "influence_class": tier,
        }
        result.append(
            (
                row["id"],
                raw,
                ImportRecord(
                    source_id=ROAD_SOURCE.id,
                    name=row["name"],
                    category_id="noise-road",
                    geometry=row["geojson"],
                    description="Оценочный признак влияния дороги; не уровень шума",
                    properties={
                        "noiseType": "road_noise",
                        "originType": "estimated",
                        "confidenceLabel": "LOW",
                        "sourceDataAt": timestamp,
                        "method": (
                            "Qualitative tier from OSM road_class and lanes; "
                            "no traffic or propagation model"
                        ),
                        "intensityDb": None,
                        "influenceClass": tier,
                        "roadClass": row["road_class"],
                        "lanes": row["lanes"],
                    },
                    confidence=0.4,
                ),
            )
        )
    return result


def _upsert(
    connection: Connection, object_id: str, record: ImportRecord, raw: dict[str, Any]
) -> None:
    connection.execute(
        text("""
        INSERT INTO noise_sources(object_id,noise_type,origin_type,confidence_label,
          influence_class,intensity_db,source_data_at,source_checked_at,method,source_object_id)
        VALUES (:id,:type,:origin,:confidence,:tier,NULL,:source_data,now(),:method,:source_object)
        ON CONFLICT (object_id) DO UPDATE SET noise_type=EXCLUDED.noise_type,
          origin_type=EXCLUDED.origin_type,confidence_label=EXCLUDED.confidence_label,
          influence_class=EXCLUDED.influence_class,intensity_db=EXCLUDED.intensity_db,
          source_data_at=EXCLUDED.source_data_at,source_checked_at=EXCLUDED.source_checked_at,
          method=EXCLUDED.method,source_object_id=EXCLUDED.source_object_id
    """),
        {
            "id": object_id,
            "type": record.properties["noiseType"],
            "origin": record.properties["originType"],
            "confidence": record.properties["confidenceLabel"],
            "tier": record.properties["influenceClass"],
            "source_data": datetime.fromisoformat(record.properties["sourceDataAt"])
            if record.properties["sourceDataAt"]
            else None,
            "method": record.properties["method"],
            "source_object": raw.get("source_object_id"),
        },
    )


def run() -> tuple[tuple[int, ImportStats], tuple[int, ImportStats]]:
    rail = import_records(RAIL_SOURCE, "noise", rail_records(), _upsert)
    road = import_records(ROAD_SOURCE, "noise", road_records(), _upsert)
    return rail, road
