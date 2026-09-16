import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine
from app.spatial import parse_bbox

router = APIRouter(prefix="/api/kindergartens", tags=["kindergartens"])
logger = logging.getLogger(__name__)


@router.get("")
def kindergartens(
    bbox: str | None = None,
    operator: str | None = Query(default=None, pattern="^(public|private|unknown)$"),
    limit: int = Query(default=500, ge=1, le=2000),
) -> list[dict[str, Any]]:
    bounds = parse_bbox(bbox)
    conditions = ["true"]
    params: dict[str, Any] = {"limit": limit}
    if bounds:
        conditions.append("object.geometry && ST_MakeEnvelope(:west,:south,:east,:north,4326)")
        params.update(zip(("west", "south", "east", "north"), bounds))
    if operator:
        conditions.append("garden.operator_type=:operator")
        params["operator"] = operator
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                text(f"""
                SELECT object.id,object.name,garden.operator_type AS operator,garden.address,
                  garden.official_id AS "officialId",garden.website,
                  garden.source_data_at AS "sourceDataAt",
                  garden.object_check_date AS "objectCheckDate",garden.confidence,
                  object.source,ST_AsGeoJSON(object.geometry)::json AS geometry
                FROM kindergartens garden JOIN project_objects object
                  ON object.id=garden.object_id
                WHERE {" AND ".join(conditions)} ORDER BY object.id LIMIT :limit
            """),
                params,
            ).mappings()
            return [dict(row) for row in rows]
    except SQLAlchemyError:
        logger.warning("Kindergartens repository unavailable")
        raise HTTPException(status_code=503, detail="Kindergartens unavailable") from None


@router.get("/nearby")
def nearby(
    lon: float = Query(ge=-180, le=180),
    lat: float = Query(ge=-90, le=90),
    radius: int = Query(default=500, ge=50, le=5000),
) -> dict[str, Any]:
    point = "ST_SetSRID(ST_Point(:lon,:lat),4326)::geography"
    params = {"lon": lon, "lat": lat, "radius": radius}
    try:
        with get_engine().connect() as connection:
            counts = (
                connection.execute(
                    text(f"""
                SELECT count(*) AS total,
                  count(*) FILTER (WHERE garden.operator_type='public') AS public,
                  count(*) FILTER (WHERE garden.operator_type='private') AS private,
                  count(*) FILTER (WHERE garden.operator_type='unknown') AS unknown
                FROM kindergartens garden JOIN project_objects object
                  ON object.id=garden.object_id
                WHERE ST_DWithin(object.geometry::geography,{point},:radius)
            """),
                    params,
                )
                .mappings()
                .one()
            )
            nearest = (
                connection.execute(
                    text(f"""
                SELECT object.id,object.name,garden.operator_type AS operator,
                  ST_Distance(object.geometry::geography,{point}) AS distance_meters
                FROM kindergartens garden JOIN project_objects object
                  ON object.id=garden.object_id
                ORDER BY object.geometry <-> ST_SetSRID(ST_Point(:lon,:lat),4326)
                LIMIT 1
            """),
                    params,
                )
                .mappings()
                .first()
            )
    except SQLAlchemyError:
        logger.warning("Kindergarten proximity unavailable")
        raise HTTPException(status_code=503, detail="Kindergarten analysis unavailable") from None
    return {
        "method": "straight-line",
        "radiusMeters": radius,
        "counts": dict(counts),
        "nearest": dict(nearest) if nearest else None,
    }


@router.get("/admissions")
def admissions() -> dict[str, Any]:
    with get_engine().connect() as connection:
        rows = connection.execute(
            text("""
            SELECT source_url AS "sourceUrl",source_date AS "sourceDate",
              representation,summary FROM kindergarten_admission_sources ORDER BY id
        """)
        ).mappings()
        return {
            "sources": [dict(row) for row in rows],
            "warning": "Данные о комплектовании не гарантируют зачисление",
        }
