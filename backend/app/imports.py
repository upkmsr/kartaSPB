import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_engine

router = APIRouter(prefix="/api/import", tags=["imports"])
logger = logging.getLogger(__name__)


def _query(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with get_engine().connect() as connection:
        return [dict(row) for row in connection.execute(text(sql), params or {}).mappings()]


def unavailable() -> HTTPException:
    logger.warning("Ingestion repository unavailable")
    return HTTPException(status_code=503, detail="Import data temporarily unavailable")


@router.get("/status")
def status() -> dict[str, Any]:
    try:
        running = _query(
            "SELECT count(*) AS count FROM ingestion_runs WHERE status='running'"
        )[0]["count"]
        latest = _query(
            "SELECT id,status,module,source_id,started_at,finished_at "
            "FROM ingestion_runs ORDER BY id DESC LIMIT 1"
        )
        return {"running": running, "latest": latest[0] if latest else None}
    except SQLAlchemyError:
        raise unavailable() from None


@router.get("/runs")
def runs(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    try:
        return _query(
            "SELECT * FROM ingestion_runs ORDER BY id DESC LIMIT :limit", {"limit": limit}
        )
    except SQLAlchemyError:
        raise unavailable() from None


@router.get("/errors")
def errors(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    try:
        return _query(
            "SELECT * FROM ingestion_errors ORDER BY id DESC LIMIT :limit", {"limit": limit}
        )
    except SQLAlchemyError:
        raise unavailable() from None
