import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.database import check_database, get_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    get_engine().dispose()


app = FastAPI(title="KARTASPB", version="0.1.0", lifespan=lifespan)


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
