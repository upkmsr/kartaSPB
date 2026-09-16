"""Metro categories."""

from alembic import op

revision = "0006_metro"
down_revision = "0005_nature"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible) VALUES
          ('metro-line','Линии метро','Линии Петербургского метрополитена','#d7dce2',true),
          ('metro-station','Станции метро','Станции метро','#ffffff',true),
          ('metro-entrance','Входы в метро','Входы и выходы метро','#9aa8b5',false)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM categories WHERE id IN ('metro-line','metro-station','metro-entrance')")
