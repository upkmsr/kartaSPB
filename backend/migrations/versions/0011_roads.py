"""Structured roads over canonical PostGIS geometries."""

from alembic import op

revision = "0011_roads"
down_revision = "0010_medical"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible) VALUES
          ('road-major','Крупные дороги','Дорожная инфраструктура','#8e9cac',false),
          ('road-kad','КАД','Дорожная инфраструктура','#d69d59',true),
          ('road-zsd','ЗСД','Дорожная инфраструктура','#7bb0d6',true),
          ('road-ramp','Съезды','Дорожная инфраструктура','#a2a4a9',false),
          ('road-interchange','Развязки и съезды','Дорожная инфраструктура','#d8ba7e',false)
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        CREATE TABLE roads (
            object_id text PRIMARY KEY REFERENCES project_objects(id) ON DELETE CASCADE,
            road_type text NOT NULL CHECK (road_type IN ('major','motorway','ramp','interchange')),
            corridor text NOT NULL CHECK (corridor IN ('other','kad','zsd')),
            road_class text,
            ref text,
            operator text,
            access text,
            toll boolean,
            lanes integer CHECK (lanes > 0),
            maxspeed text,
            source_data_at timestamptz,
            source_checked_at timestamptz NOT NULL,
            confidence double precision NOT NULL CHECK (confidence BETWEEN 0 AND 1)
        )
    """)
    op.execute("CREATE INDEX ix_roads_type ON roads(road_type)")
    op.execute("CREATE INDEX ix_roads_corridor ON roads(corridor)")
    op.execute("""
        CREATE INDEX ix_roads_geometry ON project_objects USING gist(geometry)
        WHERE category_id IN ('road-major','road-kad','road-zsd','road-ramp','road-interchange')
    """)


def downgrade() -> None:
    op.execute("DROP INDEX ix_roads_geometry")
    op.drop_table("roads")
    op.execute("""
        DELETE FROM categories WHERE id IN
          ('road-major','road-kad','road-zsd','road-ramp','road-interchange')
    """)
