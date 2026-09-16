import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

router = APIRouter(prefix="/api/analysis/metro", tags=["metro"])
logger = logging.getLogger(__name__)


@router.get("/nearest")
def nearest(
    lon: float = Query(ge=-180, le=180), lat: float = Query(ge=-90, le=90)
) -> dict[str, Any]:
    try:
        with get_engine().connect() as connection:
            row = connection.execute(text("""
                SELECT id,name,properties->'lineRefs' AS lines,
                  ST_Distance(geometry::geography,ST_SetSRID(ST_Point(:lon,:lat),4326)::geography)
                    AS distance_meters
                FROM project_objects WHERE category_id='metro-station'
                ORDER BY geometry <-> ST_SetSRID(ST_Point(:lon,:lat),4326) LIMIT 1
            """), {"lon": lon, "lat": lat}).mappings().first()
    except SQLAlchemyError:
        logger.warning("Metro analysis unavailable")
        raise HTTPException(
            status_code=503, detail="Metro analysis temporarily unavailable"
        ) from None
    if row is None:
        raise HTTPException(status_code=404, detail="No metro stations imported")
    return {**dict(row), "method": "straight-line"}
