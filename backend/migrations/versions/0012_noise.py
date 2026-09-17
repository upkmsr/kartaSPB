"""Distinct environmental influence sources over canonical spatial objects."""

from alembic import op

revision = "0012_noise"
down_revision = "0011_roads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible) VALUES
          ('noise-road','Дорожное влияние','Оценочный признак, не уровень шума','#d78658',false),
          ('noise-railway','Железнодорожное влияние','Положение путей, не уровень шума','#b48cca',false),
          ('noise-aviation','Авиационный шум','Данные отсутствуют','#7697b7',false),
          ('noise-helicopter','Вертолётный шум','Данные отсутствуют','#90a5b3',false)
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        CREATE TABLE noise_sources (
          object_id text PRIMARY KEY REFERENCES project_objects(id) ON DELETE CASCADE,
          noise_type text NOT NULL CHECK (noise_type IN
            ('road_noise','railway_noise','aviation_noise','helicopter_noise')),
          origin_type text NOT NULL CHECK (origin_type IN
            ('measured','modeled','estimated','unknown')),
          confidence_label text NOT NULL CHECK (confidence_label IN
            ('HIGH','MEDIUM','LOW','UNKNOWN')),
          influence_class text CHECK (influence_class IN ('low','medium','high')),
          intensity_db double precision,
          source_data_at timestamptz,
          source_checked_at timestamptz NOT NULL,
          method text NOT NULL,
          source_object_id text REFERENCES project_objects(id)
        )
    """)
    op.execute("CREATE INDEX ix_noise_type ON noise_sources(noise_type)")
    op.execute("""
        CREATE INDEX ix_noise_geometry ON project_objects USING gist(geometry)
        WHERE category_id IN ('noise-road','noise-railway','noise-aviation','noise-helicopter')
    """)


def downgrade() -> None:
    op.execute("DROP INDEX ix_noise_geometry")
    op.drop_table("noise_sources")
    op.execute("""
        DELETE FROM categories WHERE id IN
          ('noise-road','noise-railway','noise-aviation','noise-helicopter')
    """)
