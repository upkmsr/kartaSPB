import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import check_database, get_engine
from app.imports import router as import_router
from app.kindergartens.api import router as kindergartens_router
from app.medical.api import router as medical_router
from app.metro.api import router as metro_router
from app.objects import router
from app.schools.api import router as schools_router
from app.search import router as search_router
from app.transport.api import router as transport_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    get_engine().dispose()


app = FastAPI(title="KARTASPB", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.include_router(search_router)
app.include_router(import_router)
app.include_router(metro_router)
app.include_router(transport_router)
app.include_router(schools_router)
app.include_router(kindergartens_router)
app.include_router(medical_router)


@app.get("/api/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health/ready", response_model=None)
def ready() -> JSONResponse:
    try:
        check_database()
    except Exception:
        # Do not log connection exceptions: they may contain credentials.
        logger.warning("Database readiness check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return JSONResponse(content={"status": "ok"})
