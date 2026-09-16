"""Read-only road viewport and straight-line proximity queries."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine
from app.spatial import parse_bbox

router = APIRouter(prefix="/api/roads", tags=["roads"])
analysis_router = APIRouter(prefix="/api/analysis/roads", tags=["roads"])
logger = logging.getLogger(__name__)
ROAD_CATEGORIES = {"road-major", "road-kad", "road-zsd", "road-ramp", "road-interchange"}


def _conditions(
    bounds: tuple[float, float, float, float] | None,
    road_type: str | None,
    corridor: str | None,
    categories: list[str] | None,
) -> tuple[str, dict[str, Any]]:
    clauses = ["true"]
    params: dict[str, Any] = {}
    if bounds:
        clauses.append("object.geometry && ST_MakeEnvelope(:west,:south,:east,:north,4326)")
        params.update(zip(("west", "south", "east", "north"), bounds))
    if road_type:
        clauses.append("road.road_type=:road_type")
        params["road_type"] = road_type
    if corridor:
        clauses.append("road.corridor=:corridor")
        params["corridor"] = corridor
    if categories:
        clauses.append("object.category_id = ANY(CAST(:categories AS text[]))")
        params["categories"] = categories
    return " AND ".join(clauses), params


def _rows(
    bounds: tuple[float, float, float, float] | None,
    road_type: str | None,
    corridor: str | None,
    categories: list[str] | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    condition, params = _conditions(bounds, road_type, corridor, categories)
    with get_engine().connect() as connection:
        rows = connection.execute(
            text(f"""
            SELECT object.id,object.name,object.category_id AS "categoryId",
              road.road_type AS "roadType",road.corridor,road.road_class AS "roadClass",
              road.ref,road.operator,road.access,road.toll,road.lanes,road.maxspeed,
              road.confidence,road.source_data_at AS "sourceDataAt",object.source,
              ST_AsGeoJSON(object.geometry)::json AS geometry
            FROM roads road JOIN project_objects object ON object.id=road.object_id
            WHERE {condition} ORDER BY object.id LIMIT :limit OFFSET :offset
        """),
            {**params, "limit": limit, "offset": offset},
        ).mappings()
        return [dict(row) for row in rows]


@router.get("")
def roads(
    bbox: str | None = None,
    road_type: str | None = Query(
        default=None, alias="type", pattern="^(major|motorway|ramp|interchange)$"
    ),
    corridor: str | None = Query(default=None, pattern="^(other|kad|zsd)$"),
    category: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=500, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    bounds = parse_bbox(bbox)
    categories = _parse_categories(category)
    try:
        return _rows(bounds, road_type, corridor, categories, limit, offset)
    except SQLAlchemyError:
        logger.warning("Road repository unavailable")
        raise HTTPException(status_code=503, detail="Road data unavailable") from None


@router.get("/viewport.geojson")
def viewport(
    bbox: str,
    category: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=6000, ge=1, le=10000),
) -> dict[str, Any]:
    bounds = parse_bbox(bbox)
    if bounds is None:
        raise HTTPException(status_code=422, detail="bbox is required")
    categories = _parse_categories(category)
    try:
        features = _rows(bounds, None, None, categories, limit, 0)
        return {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": row.pop("geometry"), "properties": row}
                for row in features
            ],
        }
    except SQLAlchemyError:
        logger.warning("Road viewport unavailable")
        raise HTTPException(status_code=503, detail="Road data unavailable") from None


def _parse_categories(value: str | None) -> list[str] | None:
    if value is None:
        return None
    categories = [part.strip() for part in value.split(",") if part.strip()]
    if not categories or any(category not in ROAD_CATEGORIES for category in categories):
        raise HTTPException(status_code=422, detail="Unknown road category")
    return categories


def _nearest(
    connection: Connection, lon: float, lat: float, condition: str
) -> dict[str, Any] | None:
    point = "ST_SetSRID(ST_Point(:lon,:lat),4326)"
    row = (
        connection.execute(
            text(f"""
        SELECT object.id,object.name,road.road_type AS "roadType",road.corridor,
          ST_Distance(object.geometry::geography,{point}::geography) AS "distanceMeters"
        FROM roads road JOIN project_objects object ON object.id=road.object_id
        WHERE {condition}
        ORDER BY ST_Distance(object.geometry::geography,{point}::geography) LIMIT 1
    """),
            {"lon": lon, "lat": lat},
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


@analysis_router.get("/nearest")
def nearest(
    lon: float = Query(ge=-180, le=180),
    lat: float = Query(ge=-90, le=90),
) -> dict[str, Any]:
    try:
        with get_engine().connect() as connection:
            return {
                "method": "straight-line",
                "nearestMajorRoad": _nearest(
                    connection, lon, lat, "road.road_type IN ('major','motorway')"
                ),
                "nearestKad": _nearest(connection, lon, lat, "road.corridor='kad'"),
                "nearestZsd": _nearest(connection, lon, lat, "road.corridor='zsd'"),
                "nearestInterchange": _nearest(
                    connection, lon, lat, "road.road_type='interchange'"
                ),
            }
    except SQLAlchemyError:
        logger.warning("Road proximity unavailable")
        raise HTTPException(status_code=503, detail="Road analysis unavailable") from None
