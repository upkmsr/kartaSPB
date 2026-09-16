"""Data ingestion registry, staging, runs, errors and provenance."""

from alembic import op

revision = "0003_ingestion"
down_revision = "0002_objects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE data_sources (
            id text PRIMARY KEY,
            name text NOT NULL,
            type text NOT NULL,
            url text NOT NULL,
            license text NOT NULL,
            attribution text NOT NULL,
            priority integer NOT NULL DEFAULT 100,
            enabled boolean NOT NULL DEFAULT true,
            last_checked_at timestamptz,
            notes text NOT NULL DEFAULT ''
        )
    """)
    op.execute("""
        CREATE TABLE ingestion_runs (
            id bigserial PRIMARY KEY,
            started_at timestamptz NOT NULL DEFAULT now(),
            finished_at timestamptz,
            status text NOT NULL CHECK (status IN ('running','completed','failed')),
            source_id text NOT NULL REFERENCES data_sources(id),
            module text NOT NULL,
            objects_found integer NOT NULL DEFAULT 0,
            objects_inserted integer NOT NULL DEFAULT 0,
            objects_updated integer NOT NULL DEFAULT 0,
            objects_skipped integer NOT NULL DEFAULT 0,
            duplicates integer NOT NULL DEFAULT 0,
            warnings integer NOT NULL DEFAULT 0,
            errors integer NOT NULL DEFAULT 0
        )
    """)
    op.execute("CREATE INDEX ix_ingestion_runs_source ON ingestion_runs(source_id, started_at DESC)")
    op.execute("""
        CREATE TABLE ingestion_staging (
            id bigserial PRIMARY KEY,
            run_id bigint NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
            source_record_id text,
            raw_payload jsonb NOT NULL,
            normalized_payload jsonb,
            validation_status text NOT NULL DEFAULT 'pending'
                CHECK (validation_status IN ('pending','valid','invalid','imported','duplicate')),
            canonical_object_id text REFERENCES project_objects(id),
            created_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (run_id, source_record_id)
        )
    """)
    op.execute("""
        CREATE TABLE ingestion_errors (
            id bigserial PRIMARY KEY,
            run_id bigint NOT NULL REFERENCES ingestion_runs(id) ON DELETE CASCADE,
            staging_id bigint REFERENCES ingestion_staging(id) ON DELETE SET NULL,
            source_record_id text,
            stage text NOT NULL,
            message text NOT NULL,
            details jsonb NOT NULL DEFAULT '{}'::jsonb,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE object_provenance (
            object_id text NOT NULL REFERENCES project_objects(id) ON DELETE CASCADE,
            source_id text NOT NULL REFERENCES data_sources(id),
            source_record_id text NOT NULL,
            run_id bigint NOT NULL REFERENCES ingestion_runs(id),
            collected_at timestamptz NOT NULL,
            checked_at timestamptz NOT NULL DEFAULT now(),
            confidence double precision NOT NULL DEFAULT 1.0 CHECK (confidence BETWEEN 0 AND 1),
            PRIMARY KEY (object_id, source_id, source_record_id)
        )
    """)
    op.execute("CREATE INDEX ix_provenance_source_record ON object_provenance(source_id, source_record_id)")


def downgrade() -> None:
    op.drop_table("object_provenance")
    op.drop_table("ingestion_errors")
    op.drop_table("ingestion_staging")
    op.drop_table("ingestion_runs")
    op.drop_table("data_sources")
