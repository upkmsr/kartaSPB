"""Read-only canonical object repository and API; no external providers."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, JsonValue
from sqlalchemy import String, bindparam, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


class Category(BaseModel):
    id: str
    name: str
    description: str
    color: str
    defaultVisible: bool


class MapObject(BaseModel):
    id: str
    name: str
    categoryId: str
    description: str
    geometry: dict[str, JsonValue]
    properties: dict[str, JsonValue]
    source: Optional[str]
    sourceId: Optional[str]


def read_objects(
    category: Optional[str] = None,
    object_id: Optional[str] = None,
    exclude_category: Optional[str] = None,
    exclude_category_prefix: Optional[str] = None,
) -> list[MapObject]:
    query = """SELECT id, name, category_id AS "categoryId", description,
        ST_AsGeoJSON(geometry)::json AS geometry, properties, source, source_id AS "sourceId"
        FROM project_objects WHERE true"""
    params: dict[str, object] = {}
    if object_id is not None:
        query += " AND id = :object_id"
        params["object_id"] = object_id
    if category is not None:
        query += " AND category_id IN :categories"
        params["categories"] = [value.strip() for value in category.split(",") if value.strip()]
    if exclude_category is not None:
        query += " AND category_id != :exclude_category"
        params["exclude_category"] = exclude_category
    if exclude_category_prefix is not None:
        query += " AND category_id NOT LIKE :exclude_category_prefix"
        params["exclude_category_prefix"] = exclude_category_prefix.replace("%", "\\%") + "%"
    statement = text(query + " ORDER BY id")
    if category is not None:
        statement = statement.bindparams(bindparam("categories", expanding=True, type_=String))
    with get_engine().connect() as connection:
        return [
            MapObject.model_validate(dict(row))
            for row in connection.execute(statement, params).mappings()
        ]


def unavailable() -> HTTPException:
    # SQLAlchemy exceptions can contain connection secrets; log only the event.
    logger.warning("Project object repository unavailable")
    return HTTPException(status_code=503, detail="Project data temporarily unavailable")


@router.get("/categories")
def categories() -> list[Category]:
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                text(
                    'SELECT id, name, description, color, default_visible AS "defaultVisible" '
                    "FROM categories ORDER BY id"
                )
            )
            return [Category.model_validate(dict(row)) for row in rows.mappings()]
    except SQLAlchemyError:
        raise unavailable() from None


@router.get("/objects")
def objects(
    category: Optional[str] = Query(default=None, max_length=500),
    exclude_category: Optional[str] = Query(default=None, alias="excludeCategory"),
    exclude_category_prefix: Optional[str] = Query(default=None, alias="excludeCategoryPrefix"),
) -> list[MapObject]:
    try:
        return read_objects(
            category=category,
            exclude_category=exclude_category,
            exclude_category_prefix=exclude_category_prefix,
        )
    except SQLAlchemyError:
        raise unavailable() from None


@router.get("/objects/{object_id}")
def object_detail(object_id: str) -> MapObject:
    try:
        found = read_objects(object_id=object_id)
    except SQLAlchemyError:
        raise unavailable() from None
    if not found:
        raise HTTPException(status_code=404, detail="Object not found")
    return found[0]
