"""Reproducible OSM snapshot import; each OSM feature is one physical facility."""

import json
import re
from collections.abc import Iterable
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, text

from app.education import address
from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.normalize import normalize_name
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="osm-medical",
    name="OpenStreetMap Petersburg medical facilities",
    type="osm-overpass-snapshot",
    url="https://overpass-api.de/api/interpreter",
    license="ODbL 1.0",
    attribution="© OpenStreetMap contributors",
    priority=50,
    notes=(
        "Petersburg OSM area; amenity hospital/clinic/doctors/dentist/pharmacy or "
        "healthcare hospital/clinic/doctor/dentist/laboratory/centre/pharmacy. "
        "Snapshot collected 2026-09-16; community data may be incomplete."
    ),
)
SNAPSHOT = Path(__file__).parent / "snapshots" / "spb_medical.json"


def load_snapshot(path: Path = SNAPSHOT) -> dict[str, Any]:
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def ownership(tags: dict[str, Any]) -> str:
    operator = str(tags.get("operator", "")).upper()
    if tags.get("operator:type") in {"public", "government"} or "ГБУЗ" in operator:
        return "public"
    if tags.get("operator:type") == "private" or re.match(r"^\s*(ООО|ИП)(?:\s|[«\"'])", operator):
        return "private"
    return "unknown"


def facility_type(tags: dict[str, Any]) -> str:
    amenity = tags.get("amenity")
    healthcare = tags.get("healthcare")
    name = str(tags.get("name", "")).lower()
    speciality = str(tags.get("healthcare:speciality", "")).lower()
    if amenity == "pharmacy" or healthcare == "pharmacy":
        return "pharmacy"
    if amenity == "dentist" or healthcare == "dentist":
        return "dentistry"
    if healthcare == "laboratory":
        return "laboratory"
    if amenity == "hospital" or healthcare == "hospital":
        return "hospital"
    if tags.get("emergency") in {"ambulance", "ambulance_station"}:
        return "emergency_or_24h"
    if "травмпункт" in name or "trauma" in speciality:
        return "trauma_center"
    if "женская консультация" in name or "gynaecology" in speciality:
        return "womens_health"
    if "diagnostic_radiology" in speciality or "диагностическ" in name:
        return "diagnostic_center"
    if "поликлиник" in name and ownership(tags) == "public":
        return "children_polyclinic" if "детск" in name else "public_polyclinic"
    if amenity == "clinic" or healthcare == "clinic":
        return (
            "private_multispecialty_clinic"
            if ownership(tags) == "private"
            else "specialized_center"
        )
    return "specialized_center"


def services(tags: dict[str, Any]) -> list[str]:
    value = tags.get("healthcare:speciality")
    if not isinstance(value, str):
        return []
    return sorted({part.strip().lower() for part in value.split(";") if part.strip()})


def confidence(tags: dict[str, Any]) -> float:
    return round(
        0.45
        + (0.1 if address(tags) else 0)
        + (0.1 if tags.get("website") or tags.get("contact:website") else 0)
        + (0.1 if tags.get("phone") or tags.get("contact:phone") else 0)
        + (0.1 if ownership(tags) != "unknown" else 0)
        + (0.1 if tags.get("opening_hours") else 0),
        2,
    )


def records(payload: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], ImportRecord]]:
    timestamp = payload.get("osm3s", {}).get("timestamp_osm_base")
    for element in payload.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name")
        center = element.get("center", element)
        if (
            not isinstance(name, str)
            or not name.strip()
            or "lon" not in center
            or "lat" not in center
        ):
            continue
        if tags.get("amenity") == "veterinary" or tags.get("healthcare") == "veterinary":
            continue
        kind = facility_type(tags)
        is_24h = tags.get("opening_hours") == "24/7"
        owner = ownership(tags)
        yield (
            f"{element['type']}-{element['id']}",
            element,
            ImportRecord(
                source_id=SOURCE.id,
                name=name,
                category_id=f"medical-{kind}",
                geometry={"type": "Point", "coordinates": [center["lon"], center["lat"]]},
                description="Медицинский объект по данным OpenStreetMap",
                address=address(tags),
                aliases=tuple(filter(None, [tags.get("alt_name")])),
                properties={
                    "facilityType": kind,
                    "ownershipType": owner,
                    "address": address(tags),
                    "website": tags.get("website") or tags.get("contact:website"),
                    "phone": tags.get("phone") or tags.get("contact:phone"),
                    "openingHours": tags.get("opening_hours"),
                    "is24h": is_24h,
                    "emergency": tags.get("emergency") in {"yes", "ambulance", "ambulance_station"},
                    "services": services(tags),
                    "organization": tags.get("brand") or tags.get("operator"),
                    "sourceDataAt": timestamp,
                    "confidence": confidence(tags),
                },
                confidence=confidence(tags),
            ),
        )


def _upsert(
    connection: Connection, object_id: str, record: ImportRecord, raw: dict[str, Any]
) -> None:
    tags = raw["tags"]
    organization = tags.get("brand") or tags.get("operator")
    organization_id = None
    if isinstance(organization, str) and organization.strip():
        key = normalize_name(organization) or organization
        organization_id = f"{SOURCE.id}-organization-{sha256(key.encode()).hexdigest()[:20]}"
        connection.execute(
            text("""
            INSERT INTO medical_organizations(id,name,source_id) VALUES (:id,:name,:source)
            ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name
        """),
            {"id": organization_id, "name": organization, "source": SOURCE.id},
        )
    connection.execute(
        text("""
        INSERT INTO medical_facilities(object_id,organization_id,facility_type,ownership_type,
          address,official_id,website,phone,opening_hours,is_24h,emergency,
          source_data_at,source_checked_at,confidence)
        VALUES (:id,:organization,:type,:owner,:address,:official,:website,:phone,:hours,
          :is_24h,:emergency,:source_data,now(),:confidence)
        ON CONFLICT (object_id) DO UPDATE SET
          organization_id=EXCLUDED.organization_id,facility_type=EXCLUDED.facility_type,
          ownership_type=EXCLUDED.ownership_type,address=EXCLUDED.address,
          official_id=EXCLUDED.official_id,website=EXCLUDED.website,phone=EXCLUDED.phone,
          opening_hours=EXCLUDED.opening_hours,is_24h=EXCLUDED.is_24h,
          emergency=EXCLUDED.emergency,source_data_at=EXCLUDED.source_data_at,
          source_checked_at=EXCLUDED.source_checked_at,confidence=EXCLUDED.confidence
    """),
        {
            "id": object_id,
            "organization": organization_id,
            "type": facility_type(tags),
            "owner": ownership(tags),
            "address": address(tags),
            "official": tags.get("ref"),
            "website": tags.get("website") or tags.get("contact:website"),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "hours": tags.get("opening_hours"),
            "is_24h": tags.get("opening_hours") == "24/7",
            "emergency": tags.get("emergency") in {"yes", "ambulance", "ambulance_station"},
            "source_data": datetime.fromisoformat(
                record.properties["sourceDataAt"].replace("Z", "+00:00")
            ),
            "confidence": record.confidence,
        },
    )
    connection.execute(
        text("DELETE FROM medical_services WHERE facility_id=:id"), {"id": object_id}
    )
    for service in services(tags):
        connection.execute(
            text("""
            INSERT INTO medical_services(facility_id,service,source_tag)
            VALUES (:id,:service,'healthcare:speciality')
        """),
            {"id": object_id, "service": service},
        )


def run() -> tuple[int, ImportStats]:
    return import_records(SOURCE, "medical", records(load_snapshot()), _upsert)
