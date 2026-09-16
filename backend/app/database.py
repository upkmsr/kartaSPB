from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3},
    )


def check_database() -> None:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT PostGIS_Version()")).scalar_one()
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        if revision != "0005_nature":
            raise RuntimeError("Database migration is not current")
