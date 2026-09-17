"""Persist local user drawings separately from imported project objects."""

from alembic import op

revision = "0013_user_geometries"
down_revision = "0012_noise"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE user_geometries (
          id uuid PRIMARY KEY,
          name text NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 120),
          description text NOT NULL DEFAULT '' CHECK (length(description) <= 2000),
          geometry_type text NOT NULL CHECK (geometry_type IN ('Point','LineString','Polygon')),
          geometry geometry(Geometry,4326) NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now(),
          CHECK (GeometryType(geometry) = upper(geometry_type)),
          CHECK (ST_IsValid(geometry) AND NOT ST_IsEmpty(geometry)),
          CHECK (ST_XMin(geometry) >= -180 AND ST_XMax(geometry) <= 180
             AND ST_YMin(geometry) >= -90 AND ST_YMax(geometry) <= 90)
        )
    """)
    op.execute("CREATE INDEX ix_user_geometries_geometry ON user_geometries USING gist(geometry)")
    op.execute("CREATE INDEX ix_user_geometries_updated ON user_geometries(updated_at DESC)")


def downgrade() -> None:
    op.drop_table("user_geometries")
