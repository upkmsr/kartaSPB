"""Medical facilities, organizations and normalized services."""

from alembic import op

revision = "0010_medical"
down_revision = "0009_kindergartens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible) VALUES
        ('medical-public_polyclinic','Взрослые поликлиники','Медицина','#47aac4',true),
        ('medical-children_polyclinic','Детские поликлиники','Медицина','#5cc7d8',true),
        ('medical-hospital','Больницы','Медицина','#d75c70',true),
        ('medical-private_multispecialty_clinic','Частные клиники','Медицина','#ae78d2',true),
        ('medical-diagnostic_center','Диагностика','Медицина','#dbad59',true),
        ('medical-laboratory','Лаборатории','Медицина','#8cbf68',true),
        ('medical-dentistry','Стоматология','Медицина','#e19b70',true),
        ('medical-womens_health','Женское здоровье','Медицина','#db83a9',true),
        ('medical-specialized_center','Специализированные центры','Медицина','#6eadd6',true),
        ('medical-trauma_center','Травмпункты','Медицина','#d96b58',true),
        ('medical-pharmacy','Аптеки','Медицина','#68bb87',true),
        ('medical-emergency_or_24h','Скорая и круглосуточная помощь','Медицина','#e56c6c',true)
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        CREATE TABLE medical_organizations (
            id text PRIMARY KEY,
            name text NOT NULL,
            source_id text NOT NULL REFERENCES data_sources(id)
        )
    """)
    op.execute("""
        CREATE TABLE medical_facilities (
            object_id text PRIMARY KEY REFERENCES project_objects(id) ON DELETE CASCADE,
            organization_id text REFERENCES medical_organizations(id),
            facility_type text NOT NULL CHECK (facility_type IN (
                'public_polyclinic','children_polyclinic','hospital',
                'private_multispecialty_clinic','diagnostic_center','laboratory',
                'dentistry','womens_health','specialized_center','trauma_center',
                'pharmacy','emergency_or_24h')),
            ownership_type text NOT NULL CHECK (ownership_type IN ('public','private','unknown')),
            address text,
            official_id text,
            website text,
            phone text,
            opening_hours text,
            is_24h boolean NOT NULL DEFAULT false,
            emergency boolean NOT NULL DEFAULT false,
            source_data_at timestamptz,
            source_checked_at timestamptz NOT NULL,
            confidence double precision NOT NULL CHECK (confidence BETWEEN 0 AND 1),
            rating numeric,
            review_count integer
        )
    """)
    op.execute("CREATE INDEX ix_medical_type ON medical_facilities(facility_type)")
    op.execute("CREATE INDEX ix_medical_ownership ON medical_facilities(ownership_type)")
    op.execute("CREATE INDEX ix_medical_organization ON medical_facilities(organization_id)")
    op.execute("""
        CREATE TABLE medical_services (
            facility_id text NOT NULL REFERENCES medical_facilities(object_id) ON DELETE CASCADE,
            service text NOT NULL,
            source_tag text NOT NULL,
            PRIMARY KEY (facility_id,service)
        )
    """)


def downgrade() -> None:
    op.drop_table("medical_services")
    op.drop_table("medical_facilities")
    op.drop_table("medical_organizations")
    op.execute("DELETE FROM categories WHERE id LIKE 'medical-%'")
