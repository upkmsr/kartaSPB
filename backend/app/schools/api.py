import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

router = APIRouter(prefix="/api/schools", tags=["schools"])
logger = logging.getLogger(__name__)


def _bbox(value: str | None) -> tuple[float, float, float, float] | None:
    if value is None:
        return None
    try:
        west, south, east, north = (float(part) for part in value.split(","))
    except ValueError:
        raise HTTPException(status_code=422, detail="bbox must contain four numbers") from None
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise HTTPException(status_code=422, detail="bbox is invalid")
    return west, south, east, north


@router.get("")
def schools(
    bbox: str | None = None,
    operator: str | None = Query(default=None, pattern="^(public|private|unknown)$"),
    limit: int = Query(default=500, ge=1, le=2000),
) -> list[dict[str, Any]]:
    bounds = _bbox(bbox)
    conditions = ["true"]
    params: dict[str, Any] = {"limit": limit}
    if bounds:
        conditions.append("object.geometry && ST_MakeEnvelope(:west,:south,:east,:north,4326)")
        params.update(zip(("west", "south", "east", "north"), bounds))
    if operator:
        conditions.append("school.operator_type=:operator")
        params["operator"] = operator
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                text(f"""
                SELECT object.id,object.name,school.school_type AS type,
                  school.operator_type AS operator,school.address,
                  school.official_id AS "officialId",
                  school.website,school.phone,school.source_data_at AS "sourceDataAt",
                  school.object_check_date AS "objectCheckDate",school.confidence,
                  object.source,ST_AsGeoJSON(object.geometry)::json AS geometry
                FROM schools school JOIN project_objects object ON object.id=school.object_id
                WHERE {" AND ".join(conditions)} ORDER BY object.id LIMIT :limit
            """),
                params,
            ).mappings()
            return [dict(row) for row in rows]
    except SQLAlchemyError:
        logger.warning("Schools repository unavailable")
        raise HTTPException(status_code=503, detail="Schools temporarily unavailable") from None


@router.get("/catchments")
def catchments() -> dict[str, Any]:
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                text("""
                SELECT representation,source_url AS "sourceUrl",source_date AS "sourceDate",
                  source_text AS "sourceText" FROM school_catchments ORDER BY id
            """)
            ).mappings()
            sources = [dict(row) for row in rows]
    except SQLAlchemyError:
        logger.warning("School catchments repository unavailable")
        raise HTTPException(status_code=503, detail="Catchments temporarily unavailable") from None
    return {
        "status": "no_verified_polygons",
        "sources": sources,
        "warning": "Адресные списки не гарантируют право зачисления",
    }
