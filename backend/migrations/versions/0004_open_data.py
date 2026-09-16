"""Base OSM/open-data category."""

from alembic import op

revision = "0004_open_data"
down_revision = "0003_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible)
        VALUES ('osm-base','Базовые открытые данные','Контролируемый импорт OSM','#8aa4b8',false)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM categories WHERE id='osm-base'")
