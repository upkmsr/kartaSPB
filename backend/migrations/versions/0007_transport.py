"""Surface transport categories."""

from alembic import op

revision = "0007_transport"
down_revision = "0006_metro"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible) VALUES
          ('transport-bus','Автобусы','Автобусные маршруты','#3f9adb',true),
          ('transport-tram','Трамваи','Трамвайные маршруты','#e25353',true),
          ('transport-trolleybus','Троллейбусы','Троллейбусные маршруты','#58b9ad',true),
          ('transport-stop','Остановки','Остановки наземного транспорта','#f5d06f',true)
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM categories WHERE id IN (
          'transport-bus','transport-tram','transport-trolleybus','transport-stop'
        )
    """)
