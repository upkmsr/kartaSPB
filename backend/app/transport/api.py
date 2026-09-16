import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

router = APIRouter(prefix="/api/analysis/transport", tags=["transport"])
logger = logging.getLogger(__name__)


@router.get("/nearby")
def nearby(
    lon: float = Query(ge=-180, le=180),
    lat: float = Query(ge=-90, le=90),
    radius: int = Query(default=500, ge=50, le=5000),
) -> dict[str, Any]:
    point = "ST_SetSRID(ST_Point(:lon,:lat),4326)::geography"
    try:
        with get_engine().connect() as connection:
            rows = (
                connection.execute(
                    text(f"""
                SELECT id,name,properties->'routes' AS routes,
                  ST_Distance(geometry::geography,{point}) AS distance_meters
                FROM project_objects WHERE category_id='transport-stop'
                  AND ST_DWithin(geometry::geography,{point},:radius)
                ORDER BY distance_meters LIMIT 10
            """),
                    {"lon": lon, "lat": lat, "radius": radius},
                )
                .mappings()
                .all()
            )
            stop_count = connection.execute(
                text(f"""
                SELECT count(*) FROM project_objects WHERE category_id='transport-stop'
                  AND ST_DWithin(geometry::geography,{point},:radius)
            """),
                {"lon": lon, "lat": lat, "radius": radius},
            ).scalar_one()
            route_count = connection.execute(
                text(f"""
                SELECT count(DISTINCT route_id) FROM project_objects object,
                  jsonb_array_elements_text(object.properties->'routeIds') AS route_id
                WHERE category_id='transport-stop'
                  AND ST_DWithin(geometry::geography,{point},:radius)
            """),
                {"lon": lon, "lat": lat, "radius": radius},
            ).scalar_one()
    except SQLAlchemyError:
        logger.warning("Transport analysis unavailable")
        raise HTTPException(
            status_code=503, detail="Transport analysis temporarily unavailable"
        ) from None
    return {
        "method": "straight-line",
        "radiusMeters": radius,
        "nearbyStopCount": stop_count,
        "nearbyRouteCount": route_count,
        "nearestStops": [dict(row) for row in rows],
    }
