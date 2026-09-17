"""Small CRUD API for local Point, LineString and Polygon drawings."""

import json
import logging
import math
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Connection, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

router = APIRouter(prefix="/api/user/geometries", tags=["user-geometries"])
logger = logging.getLogger(__name__)
SELECT = """
    SELECT id::text,name,description,geometry_type AS "geometryType",
      ST_AsGeoJSON(geometry)::json AS geometry,
      created_at AS "createdAt",updated_at AS "updatedAt"
    FROM user_geometries
"""


class CreateGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    geometry: dict[str, Any]


class UpdateGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    geometry: dict[str, Any] | None = None


def _valid_position(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
        and all(math.isfinite(item) for item in value)
        and -180 <= value[0] <= 180
        and -90 <= value[1] <= 90
    )


def validate_geometry(geometry: dict[str, Any]) -> str:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if set(geometry) != {"type", "coordinates"}:
        raise HTTPException(status_code=422, detail="Expected GeoJSON geometry")
    if kind == "Point":
        valid = _valid_position(coordinates)
    elif kind == "LineString":
        valid = (
            isinstance(coordinates, list)
            and 2 <= len(coordinates) <= 1000
            and all(_valid_position(position) for position in coordinates)
            and len({tuple(position) for position in coordinates}) >= 2
        )
    elif kind == "Polygon":
        valid = (
            isinstance(coordinates, list)
            and len(coordinates) == 1
            and isinstance(coordinates[0], list)
            and 4 <= len(coordinates[0]) <= 1001
            and all(_valid_position(position) for position in coordinates[0])
            and coordinates[0][0] == coordinates[0][-1]
            and len({tuple(position) for position in coordinates[0][:-1]}) >= 3
        )
    else:
        raise HTTPException(status_code=422, detail="Only Point, LineString and Polygon supported")
    if not valid:
        raise HTTPException(status_code=422, detail="Invalid geometry coordinates")
    return str(kind)


def _check_postgis(connection: Connection, geometry: dict[str, Any]) -> None:
    try:
        valid = connection.execute(
            text("SELECT ST_IsValid(ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326))"),
            {"geometry": json.dumps(geometry)},
        ).scalar_one()
    except SQLAlchemyError:
        raise HTTPException(status_code=422, detail="Invalid GeoJSON geometry") from None
    if not valid:
        raise HTTPException(status_code=422, detail="Geometry is not spatially valid")


def _row(connection: Connection, geometry_id: UUID) -> dict[str, Any]:
    row = (
        connection.execute(text(SELECT + " WHERE id=:id"), {"id": str(geometry_id)})
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(status_code=404, detail="User geometry not found")
    return dict(row)


def _unavailable() -> HTTPException:
    logger.warning("User geometry repository unavailable")
    return HTTPException(status_code=503, detail="User geometry data unavailable")


@router.get("")
def list_geometries(
    limit: int = Query(default=500, ge=1, le=1000), offset: int = Query(default=0, ge=0)
) -> list[dict[str, Any]]:
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                text(SELECT + " ORDER BY created_at,id LIMIT :limit OFFSET :offset"),
                {"limit": limit, "offset": offset},
            ).mappings()
            return [dict(row) for row in rows]
    except SQLAlchemyError:
        raise _unavailable() from None


@router.post("", status_code=201)
def create_geometry(payload: CreateGeometry) -> dict[str, Any]:
    kind = validate_geometry(payload.geometry)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")
    geometry_id = uuid4()
    try:
        with get_engine().begin() as connection:
            _check_postgis(connection, payload.geometry)
            connection.execute(
                text("""
                INSERT INTO user_geometries(id,name,description,geometry_type,geometry)
                VALUES (:id,:name,:description,:kind,
                  ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326))
            """),
                {
                    "id": str(geometry_id),
                    "name": name,
                    "description": payload.description,
                    "kind": kind,
                    "geometry": json.dumps(payload.geometry),
                },
            )
            return _row(connection, geometry_id)
    except SQLAlchemyError:
        raise _unavailable() from None


@router.get("/{geometry_id}")
def get_geometry(geometry_id: UUID) -> dict[str, Any]:
    try:
        with get_engine().connect() as connection:
            return _row(connection, geometry_id)
    except SQLAlchemyError:
        raise _unavailable() from None


@router.patch("/{geometry_id}")
def update_geometry(geometry_id: UUID, payload: UpdateGeometry) -> dict[str, Any]:
    changes = payload.model_fields_set
    if not changes or any(getattr(payload, field) is None for field in changes):
        raise HTTPException(status_code=422, detail="Provide non-null fields to update")
    if payload.name is not None and not payload.name.strip():
        raise HTTPException(status_code=422, detail="Name is required")
    kind = validate_geometry(payload.geometry) if payload.geometry is not None else None
    try:
        with get_engine().begin() as connection:
            _row(connection, geometry_id)
            if payload.geometry is not None:
                _check_postgis(connection, payload.geometry)
            assignments = ["updated_at=now()"]
            params: dict[str, Any] = {"id": str(geometry_id)}
            if payload.name is not None:
                assignments.append("name=:name")
                params["name"] = payload.name.strip()
            if payload.description is not None:
                assignments.append("description=:description")
                params["description"] = payload.description
            if payload.geometry is not None:
                assignments.extend(
                    (
                        "geometry_type=:kind",
                        "geometry=ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326)",
                    )
                )
                params["kind"] = kind
                params["geometry"] = json.dumps(payload.geometry)
            connection.execute(
                text(f"UPDATE user_geometries SET {','.join(assignments)} WHERE id=:id"), params
            )
            return _row(connection, geometry_id)
    except SQLAlchemyError:
        raise _unavailable() from None


@router.delete("/{geometry_id}", status_code=204)
def delete_geometry(geometry_id: UUID) -> Response:
    try:
        with get_engine().begin() as connection:
            deleted = connection.execute(
                text("DELETE FROM user_geometries WHERE id=:id"), {"id": str(geometry_id)}
            ).rowcount
            if not deleted:
                raise HTTPException(status_code=404, detail="User geometry not found")
            return Response(status_code=204)
    except SQLAlchemyError:
        raise _unavailable() from None
