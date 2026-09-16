"""Specialized schools and source-aware catchment strategy."""

from alembic import op

revision = "0008_schools"
down_revision = "0007_transport"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible)
        VALUES ('school','Школы','Школы, лицеи и гимназии','#e2b45e',true)
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        CREATE TABLE schools (
            object_id text PRIMARY KEY REFERENCES project_objects(id) ON DELETE CASCADE,
            school_type text NOT NULL,
            operator_type text NOT NULL CHECK (operator_type IN ('public','private','unknown')),
            address text,
            official_id text,
            website text,
            phone text,
            source_checked_at timestamptz NOT NULL,
            source_data_at timestamptz,
            object_check_date date,
            confidence double precision NOT NULL CHECK (confidence BETWEEN 0 AND 1),
            construction_year integer,
            capital_repair text,
            capacity integer,
            load integer,
            admission_rules text,
            entrance_exams text,
            private_tuition numeric,
            ege_results jsonb,
            achievements jsonb,
            rating numeric,
            review_count integer
        )
    """)
    op.execute("CREATE INDEX ix_schools_operator ON schools(operator_type)")
    op.execute("CREATE INDEX ix_schools_official_id ON schools(official_id) WHERE official_id IS NOT NULL")
    op.execute("""
        CREATE TABLE school_catchments (
            id bigserial PRIMARY KEY,
            school_object_id text REFERENCES schools(object_id) ON DELETE CASCADE,
            representation text NOT NULL CHECK (representation IN
              ('official_polygon','address_list','text_rule','unknown')),
            geometry geometry(MultiPolygon,4326),
            source_url text NOT NULL,
            source_date date,
            source_text text,
            CHECK (representation != 'official_polygon' OR geometry IS NOT NULL),
            CHECK (geometry IS NULL OR ST_IsValid(geometry))
        )
    """)
    op.execute("CREATE INDEX ix_school_catchments_geometry ON school_catchments USING gist(geometry)")
    op.execute("""
        INSERT INTO school_catchments(representation,source_url,source_date,source_text)
        VALUES ('address_list',
          'https://www.gov.spb.ru/gov/terr/reg_center/obrazovanie/poryadok-priema-v-obrazovatelnye-uchrezhdeniya/',
          NULL,
          'Официальные документы о закреплении территорий содержат адресные списки; полигон отсутствует')
    """)


def downgrade() -> None:
    op.drop_table("school_catchments")
    op.drop_table("schools")
    op.execute("DELETE FROM categories WHERE id='school'")
