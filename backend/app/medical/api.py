"""Spatial medical queries. Pharmacy GeoJSON requires a viewport."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine
from app.spatial import parse_bbox

router = APIRouter(prefix="/api/medical", tags=["medical"])
logger = logging.getLogger(__name__)
FACILITY_TYPES = (
    "public_polyclinic",
    "children_polyclinic",
    "hospital",
    "private_multispecialty_clinic",
    "diagnostic_center",
    "laboratory",
    "dentistry",
    "womens_health",
    "specialized_center",
    "trauma_center",
    "pharmacy",
    "emergency_or_24h",
)


@router.get("")
def facilities(
    bbox: str | None = None,
    facility_type: str | None = Query(default=None, alias="type"),
    ownership: str | None = Query(default=None, pattern="^(public|private|unknown)$"),
    is_24h: bool | None = None,
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    if facility_type is not None and facility_type not in FACILITY_TYPES:
        raise HTTPException(status_code=422, detail="Unknown medical facility type")
    bounds = parse_bbox(bbox)
    conditions = ["true"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if bounds:
        conditions.append("object.geometry && ST_MakeEnvelope(:west,:south,:east,:north,4326)")
        params.update(zip(("west", "south", "east", "north"), bounds))
    if facility_type:
        conditions.append("facility.facility_type=:type")
        params["type"] = facility_type
    if ownership:
        conditions.append("facility.ownership_type=:ownership")
        params["ownership"] = ownership
    if is_24h is not None:
        conditions.append("facility.is_24h=:is_24h")
        params["is_24h"] = is_24h
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                text(f"""
                SELECT object.id,object.name,facility.facility_type AS "facilityType",
                  facility.ownership_type AS "ownershipType",facility.address,
                  facility.official_id AS "officialId",facility.website,facility.phone,
                  facility.opening_hours AS "openingHours",facility.is_24h AS "is24h",
                  facility.emergency,facility.confidence,
                  facility.source_data_at AS "sourceDataAt",object.source,
                  organization.name AS organization,
                  ST_AsGeoJSON(object.geometry)::json AS geometry
                FROM medical_facilities facility JOIN project_objects object
                  ON object.id=facility.object_id
                LEFT JOIN medical_organizations organization
                  ON organization.id=facility.organization_id
                WHERE {" AND ".join(conditions)} ORDER BY object.id LIMIT :limit OFFSET :offset
            """),
                params,
            ).mappings()
            return [dict(row) for row in rows]
    except SQLAlchemyError:
        logger.warning("Medical repository unavailable")
        raise HTTPException(status_code=503, detail="Medical data unavailable") from None


@router.get("/pharmacies.geojson")
def pharmacies(bbox: str, limit: int = Query(default=3000, ge=1, le=3000)) -> dict[str, Any]:
    bounds = parse_bbox(bbox)
    if bounds is None:
        raise HTTPException(status_code=422, detail="bbox is required")
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                text("""
                SELECT object.id,object.name,object.properties,
                  ST_AsGeoJSON(object.geometry)::json AS geometry
                FROM medical_facilities facility JOIN project_objects object
                  ON object.id=facility.object_id
                WHERE facility.facility_type='pharmacy'
                  AND object.geometry && ST_MakeEnvelope(:west,:south,:east,:north,4326)
                ORDER BY object.id LIMIT :limit
            """),
                {**dict(zip(("west", "south", "east", "north"), bounds)), "limit": limit},
            ).mappings()
            return {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": row.geometry,
                        "properties": {"id": row.id, "name": row.name, **row.properties},
                    }
                    for row in rows
                ],
            }
    except SQLAlchemyError:
        logger.warning("Pharmacy repository unavailable")
        raise HTTPException(status_code=503, detail="Pharmacies unavailable") from None
