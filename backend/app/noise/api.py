"""Noise source geometry and proximity, with explicit missing-data semantics."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine
from app.noise.aviation import ASSESSMENT as AVIATION_ASSESSMENT
from app.noise.helicopters import ASSESSMENT as HELICOPTER_ASSESSMENT
from app.spatial import parse_bbox

router = APIRouter(prefix="/api/noise", tags=["noise"])
analysis_router = APIRouter(prefix="/api/analysis/noise", tags=["noise"])
logger = logging.getLogger(__name__)
TYPES = {"road_noise", "railway_noise", "aviation_noise", "helicopter_noise"}


def _parse_types(value: str | None) -> list[str] | None:
    if value is None:
        return None
    types = [item.strip() for item in value.split(",") if item.strip()]
    if not types or any(item not in TYPES for item in types):
        raise HTTPException(status_code=422, detail="Unknown noise type")
    return types


def _rows(
    bounds: tuple[float, float, float, float] | None,
    noise_types: list[str] | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    where = ["true"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if bounds:
        where.append("object.geometry && ST_MakeEnvelope(:west,:south,:east,:north,4326)")
        params.update(zip(("west", "south", "east", "north"), bounds))
    if noise_types:
        where.append("noise.noise_type = ANY(CAST(:types AS text[]))")
        params["types"] = noise_types
    with get_engine().connect() as connection:
        rows = connection.execute(
            text(f"""
            SELECT object.id,object.name,object.category_id AS "categoryId",
              noise.noise_type AS "noiseType",noise.origin_type AS "originType",
              noise.confidence_label AS "confidenceLabel",
              noise.influence_class AS "influenceClass",
              noise.intensity_db AS "intensityDb",
              noise.source_data_at AS "sourceDataAt",noise.method,object.source,
              ST_AsGeoJSON(object.geometry)::json AS geometry
            FROM noise_sources noise JOIN project_objects object ON object.id=noise.object_id
            WHERE {" AND ".join(where)} ORDER BY object.id LIMIT :limit OFFSET :offset
        """),
            params,
        ).mappings()
        return [dict(row) for row in rows]


@router.get("")
def noise(
    bbox: str | None = None,
    noise_type: str | None = Query(default=None, alias="type", max_length=100),
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    bounds = parse_bbox(bbox)
    types = _parse_types(noise_type)
    try:
        return _rows(bounds, types, limit, offset)
    except SQLAlchemyError:
        logger.warning("Noise repository unavailable")
        raise HTTPException(status_code=503, detail="Noise data unavailable") from None


@router.get("/availability")
def availability() -> dict[str, Any]:
    try:
        with get_engine().connect() as connection:
            counts: dict[str, int] = {
                str(row[0]): int(row[1])
                for row in connection.execute(
                    text("""
                SELECT noise_type,count(*) FROM noise_sources GROUP BY noise_type
            """)
                ).all()
            }
        result = {
            kind: {
                "count": counts.get(kind, 0),
                "status": "available" if counts.get(kind, 0) else "no_data",
            }
            for kind in sorted(TYPES)
        }
        if not counts.get("aviation_noise"):
            result["aviation_noise"].update(AVIATION_ASSESSMENT)
        if not counts.get("helicopter_noise"):
            result["helicopter_noise"].update(HELICOPTER_ASSESSMENT)
        return result
    except SQLAlchemyError:
        logger.warning("Noise availability unavailable")
        raise HTTPException(status_code=503, detail="Noise data unavailable") from None


@router.get("/viewport.geojson")
def viewport(
    bbox: str,
    noise_type: str | None = Query(default=None, alias="type", max_length=100),
    limit: int = Query(default=7000, ge=1, le=10000),
) -> dict[str, Any]:
    bounds = parse_bbox(bbox)
    if bounds is None:
        raise HTTPException(status_code=422, detail="bbox is required")
    types = _parse_types(noise_type)
    try:
        rows = _rows(bounds, types, limit, 0)
        return {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": row.pop("geometry"), "properties": row}
                for row in rows
            ],
        }
    except SQLAlchemyError:
        logger.warning("Noise viewport unavailable")
        raise HTTPException(status_code=503, detail="Noise data unavailable") from None


def _nearest(connection: Connection, lon: float, lat: float, kind: str) -> dict[str, Any] | None:
    point = "ST_SetSRID(ST_Point(:lon,:lat),4326)"
    row = (
        connection.execute(
            text(f"""
        SELECT object.id,object.name,noise.origin_type AS "originType",
          noise.influence_class AS "influenceClass",noise.intensity_db AS "intensityDb",
          ST_Distance(object.geometry::geography,{point}::geography) AS "distanceMeters"
        FROM noise_sources noise JOIN project_objects object ON object.id=noise.object_id
        WHERE noise.noise_type=:type
        ORDER BY ST_Distance(object.geometry::geography,{point}::geography) LIMIT 1
    """),
            {"lon": lon, "lat": lat, "type": kind},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


@analysis_router.get("/point")
def point(lon: float = Query(ge=-180, le=180), lat: float = Query(ge=-90, le=90)) -> dict[str, Any]:
    try:
        with get_engine().connect() as connection:
            location = "ST_SetSRID(ST_Point(:lon,:lat),4326)"
            aviation = (
                connection.execute(
                    text(f"""
                SELECT object.id,noise.intensity_db AS "intensityDb"
                FROM noise_sources noise JOIN project_objects object ON object.id=noise.object_id
                WHERE noise.noise_type='aviation_noise'
                  AND ST_Intersects(object.geometry,{location}) LIMIT 1
            """),
                    {"lon": lon, "lat": lat},
                )
                .mappings()
                .first()
            )
            return {
                "method": "straight-line-to-source; no inferred noise score",
                "road": _nearest(connection, lon, lat, "road_noise"),
                "railway": _nearest(connection, lon, lat, "railway_noise"),
                "aviationZone": dict(aviation) if aviation else None,
                "helicopter": _nearest(connection, lon, lat, "helicopter_noise"),
                "availableNoiseIntensityDb": aviation["intensityDb"] if aviation else None,
            }
    except SQLAlchemyError:
        logger.warning("Noise analysis unavailable")
        raise HTTPException(status_code=503, detail="Noise analysis unavailable") from None
