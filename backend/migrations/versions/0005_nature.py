"""Nature categories."""

from alembic import op

revision = "0005_nature"
down_revision = "0004_open_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible) VALUES
          ('nature-green','Зелёные территории','Парки, сады и зелёные зоны','#55b978',true),
          ('nature-water','Вода','Реки, каналы, озёра и пруды','#4ba3d3',true)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM categories WHERE id IN ('nature-green','nature-water')")
