"""Independent project search and replaceable development geocoder provider."""

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import get_engine
from app.objects import MapObject

router = APIRouter(prefix="/api/search")


class GeocodingResult(BaseModel):
    id: str
    label: str
    coordinates: tuple[float, float]
    type: str
    provider: str


class NominatimProvider:
    """Small-development-use adapter: single-threaded, cached, <= 1 request/second."""

    def __init__(self) -> None:
        self._cache: dict[str, list[GeocodingResult]] = {}
        self._lock = threading.Lock()
        self._last_request = 0.0

    def search(self, query: str, limit: int) -> list[GeocodingResult]:
        key = f"{query.casefold()}:{limit}"
        with self._lock:
            if key in self._cache:
                return self._cache[key]
            delay = 1.0 - (time.monotonic() - self._last_request)
            if delay > 0:
                time.sleep(delay)
            settings = get_settings()
            params = urllib.parse.urlencode(
                {"q": query, "format": "jsonv2", "limit": limit, "countrycodes": "ru"}
            )
            request = urllib.request.Request(
                f"{settings.geocoder_url}?{params}",
                headers={"User-Agent": settings.geocoder_user_agent, "Accept": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=8) as response:  # noqa: S310
                    payload = json.load(response)
            except (urllib.error.URLError, TimeoutError, ValueError) as error:
                raise RuntimeError("Geocoder unavailable") from error
            finally:
                self._last_request = time.monotonic()
            if not isinstance(payload, list):
                raise RuntimeError("Invalid geocoder response")
            results = []
            for item in payload[:limit]:
                try:
                    results.append(
                        GeocodingResult(
                            id=f"nominatim-{item['osm_type']}-{item['osm_id']}",
                            label=str(item["display_name"]),
                            coordinates=(float(item["lon"]), float(item["lat"])),
                            type=str(item.get("type", "place")),
                            provider="nominatim",
                        )
                    )
                except (KeyError, TypeError, ValueError):
                    continue
            self._cache[key] = results
            return results


geocoder = NominatimProvider()


@router.get("/objects")
def search_objects(
    q: str = Query(min_length=1, max_length=200), limit: int = Query(default=10, ge=1, le=50)
) -> list[MapObject]:
    normalized = q.strip()
    if not normalized:
        return []
    escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    statement = text("""
        SELECT o.id, o.name, o.category_id AS "categoryId", o.description,
          ST_AsGeoJSON(o.geometry)::json AS geometry, o.properties,
          o.source, o.source_id AS "sourceId"
        FROM project_objects o JOIN categories c ON c.id=o.category_id
        WHERE o.name ILIKE :pattern ESCAPE '\\'
           OR o.description ILIKE :pattern ESCAPE '\\'
           OR c.name ILIKE :pattern ESCAPE '\\'
        ORDER BY CASE WHEN lower(o.name)=lower(:exact) THEN 0 ELSE 1 END, o.name, o.id
        LIMIT :limit
    """)
    try:
        with get_engine().connect() as connection:
            rows = connection.execute(
                statement, {"pattern": f"%{escaped}%", "exact": normalized, "limit": limit}
            ).mappings()
            return [MapObject.model_validate(dict(row)) for row in rows]
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Project search unavailable") from None


@router.get("/geocode")
def geocode(
    q: str = Query(min_length=3, max_length=200), limit: int = Query(default=5, ge=1, le=10)
) -> list[GeocodingResult]:
    try:
        return geocoder.search(q.strip(), limit)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Geocoder temporarily unavailable") from None
