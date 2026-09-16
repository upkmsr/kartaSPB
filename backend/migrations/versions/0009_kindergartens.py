"""Specialized kindergarten data and admissions provenance."""

from alembic import op

revision = "0009_kindergartens"
down_revision = "0008_schools"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO categories(id,name,description,color,default_visible) VALUES
          ('kindergarten-public','Государственные детские сады','Детские сады с подтверждённым public operator','#b178dc',true),
          ('kindergarten-private','Частные детские сады','Детские сады с подтверждённым private operator','#d76caa',true),
          ('kindergarten-unknown','Детские сады: тип неизвестен','Тип оператора не указан в источнике','#a8a3b6',true)
        ON CONFLICT (id) DO NOTHING
    """)
    op.execute("""
        CREATE TABLE kindergartens (
            object_id text PRIMARY KEY REFERENCES project_objects(id) ON DELETE CASCADE,
            operator_type text NOT NULL CHECK (operator_type IN ('public','private','unknown')),
            address text,
            official_id text,
            website text,
            source_checked_at timestamptz NOT NULL,
            source_data_at timestamptz,
            object_check_date date,
            confidence double precision NOT NULL CHECK (confidence BETWEEN 0 AND 1),
            capacity integer,
            groups integer,
            load integer,
            construction_year integer,
            capital_repair text,
            admission_rules text,
            private_price numeric,
            rating numeric,
            review_count integer
        )
    """)
    op.execute("CREATE INDEX ix_kindergartens_operator ON kindergartens(operator_type)")
    op.execute("""
        CREATE INDEX ix_kindergartens_official_id ON kindergartens(official_id)
          WHERE official_id IS NOT NULL
    """)
    op.execute("""
        CREATE TABLE kindergarten_admission_sources (
            id bigserial PRIMARY KEY,
            source_url text NOT NULL,
            source_date date,
            representation text NOT NULL CHECK (representation IN ('text_rule','address_list','unknown')),
            summary text NOT NULL
        )
    """)
    op.execute("""
        INSERT INTO kindergarten_admission_sources(source_url,source_date,representation,summary)
        VALUES (
          'https://www.gov.spb.ru/gov/terr/reg_center/obrazovanie/poryadok-priema-v-obrazovatelnye-uchrezhdeniya/',
          NULL,'text_rule',
          'Официальная страница описывает очередность и периоды комплектования; пространственные границы не предоставлены'
        )
    """)


def downgrade() -> None:
    op.drop_table("kindergarten_admission_sources")
    op.drop_table("kindergartens")
    op.execute("""
        DELETE FROM categories WHERE id IN (
          'kindergarten-public','kindergarten-private','kindergarten-unknown'
        )
    """)
