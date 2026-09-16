"""Explicit opt-in development seed, safe to repeat; never production import."""

from sqlalchemy import text

from app.database import get_engine


def seed() -> None:
    with get_engine().begin() as connection:
        connection.execute(
            text("""
            INSERT INTO project_objects
            (id, name, category_id, description, geometry, properties, source, source_id)
            VALUES ('demo-object-1', 'Тестовый объект', 'demo',
            'Демонстрационная точка для проверки карты и карточки. '
            'Не является реальным городским объектом.',
            ST_SetSRID(ST_MakePoint(30.3158,59.9391),4326),
            jsonb_build_object('demo', true), 'development-fixture', 'demo-object-1')
            ON CONFLICT (id) DO NOTHING
        """)
        )


if __name__ == "__main__":
    seed()
