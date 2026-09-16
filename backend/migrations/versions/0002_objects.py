"""Canonical project objects and controlled categories."""

from alembic import op

revision = "0002_objects"
down_revision = "0001_postgis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE categories (
            id text PRIMARY KEY,
            name text NOT NULL,
            description text NOT NULL DEFAULT '',
            color text NOT NULL CHECK (color ~ '^#[0-9a-fA-F]{6}$'),
            default_visible boolean NOT NULL DEFAULT true
        )
    """)
    op.execute("""
        INSERT INTO categories (id, name, description, color) VALUES
        ('demo', 'Демонстрационные', 'Тестовые объекты проекта', '#77dfcc'),
        ('other', 'Прочее', 'Объекты без специализированной категории', '#ffc078')
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        CREATE TABLE project_objects (
            id text PRIMARY KEY,
            name text NOT NULL,
            category_id text NOT NULL REFERENCES categories(id),
            description text NOT NULL DEFAULT '',
            geometry geometry(Geometry,4326) NOT NULL,
            properties jsonb NOT NULL DEFAULT '{}'::jsonb,
            source text,
            source_id text,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            CHECK (GeometryType(geometry) IN ('POINT','LINESTRING','POLYGON',
                'MULTIPOINT','MULTILINESTRING','MULTIPOLYGON')),
            CHECK (ST_IsValid(geometry) AND NOT ST_IsEmpty(geometry)),
            CHECK (ST_XMin(geometry) >= -180 AND ST_XMax(geometry) <= 180
                AND ST_YMin(geometry) >= -90 AND ST_YMax(geometry) <= 90),
            CHECK (jsonb_typeof(properties) = 'object')
        )
    """)
    op.execute("CREATE INDEX ix_project_objects_geometry ON project_objects USING gist(geometry)")
    op.execute("CREATE INDEX ix_project_objects_category ON project_objects(category_id)")


def downgrade() -> None:
    op.drop_table("project_objects")
    op.drop_table("categories")
