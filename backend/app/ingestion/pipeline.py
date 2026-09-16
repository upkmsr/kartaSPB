import json
import logging
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Connection, text

from app.database import get_engine
from app.ingestion.models import ImportRecord, ImportStats, SourceDefinition
from app.ingestion.normalize import normalize_identifier, normalize_text, remove_empty
from app.ingestion.validate import validate_record

logger = logging.getLogger(__name__)


def register_source(connection: Connection, source: SourceDefinition) -> None:
    connection.execute(
        text("""
        INSERT INTO data_sources (id,name,type,url,license,attribution,priority,enabled,notes)
        VALUES (:id,:name,:type,:url,:license,:attribution,:priority,true,:notes)
        ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name,type=EXCLUDED.type,url=EXCLUDED.url,
          license=EXCLUDED.license,attribution=EXCLUDED.attribution,priority=EXCLUDED.priority,
          notes=EXCLUDED.notes,last_checked_at=now()
    """),
        source.__dict__,
    )


def canonical_id(source_id: str, record_id: str) -> str:
    source = normalize_identifier(source_id)
    record = normalize_identifier(record_id)
    if not source or not record:
        raise ValueError("source and record identifiers are required")
    return f"{source}-{record}"


def _stage(connection: Connection, run_id: int, source_record_id: str, raw: dict[str, Any]) -> int:
    return int(
        connection.execute(
            text("""
        INSERT INTO ingestion_staging(run_id,source_record_id,raw_payload)
        VALUES (:run,:record,CAST(:raw AS jsonb)) RETURNING id
    """),
            {"run": run_id, "record": source_record_id, "raw": json.dumps(raw)},
        ).scalar_one()
    )


def _record_error(
    connection: Connection, run_id: int, staging_id: int, record_id: str, message: str
) -> None:
    connection.execute(
        text("""
        INSERT INTO ingestion_errors(run_id,staging_id,source_record_id,stage,message)
        VALUES (:run,:staging,:record,'validation',:message)
    """),
        {"run": run_id, "staging": staging_id, "record": record_id, "message": message},
    )


def import_records(
    source: SourceDefinition,
    module: str,
    records: Iterable[tuple[str, dict[str, Any], ImportRecord]],
) -> tuple[int, ImportStats]:
    stats = ImportStats()
    with get_engine().begin() as connection:
        register_source(connection, source)
        run_id = int(
            connection.execute(
                text("""
            INSERT INTO ingestion_runs(status,source_id,module) VALUES ('running',:source,:module)
            RETURNING id
        """),
                {"source": source.id, "module": module},
            ).scalar_one()
        )
        try:
            for record_id, raw, record in records:
                stats.found += 1
                staging_id = _stage(connection, run_id, record_id, raw)
                validation = validate_record(record)
                normalized = remove_empty(
                    {
                        "sourceId": record_id,
                        "name": normalize_text(record.name),
                        "categoryId": record.category_id,
                        "description": normalize_text(record.description),
                        "address": normalize_text(record.address),
                        "aliases": list(record.aliases),
                        "geometry": record.geometry,
                        "properties": record.properties,
                    }
                )
                if not validation.valid:
                    stats.skipped += 1
                    stats.errors += 1
                    message = "; ".join(validation.errors)
                    connection.execute(
                        text("""
                        UPDATE ingestion_staging SET normalized_payload=CAST(:payload AS jsonb),
                          validation_status='invalid' WHERE id=:id
                    """),
                        {"payload": json.dumps(normalized), "id": staging_id},
                    )
                    _record_error(connection, run_id, staging_id, record_id, message)
                    continue
                object_id = canonical_id(source.id, record_id)
                existing = connection.execute(
                    text("SELECT 1 FROM project_objects WHERE id=:id"), {"id": object_id}
                ).scalar_one_or_none()
                connection.execute(
                    text("""
                    INSERT INTO project_objects(
                      id,name,category_id,description,geometry,properties,source,source_id
                    )
                    VALUES (:id,:name,:category,:description,
                      ST_SetSRID(ST_GeomFromGeoJSON(:geometry),4326),
                      CAST(:properties AS jsonb),:source,:source_record)
                    ON CONFLICT (id) DO UPDATE SET
                      name=EXCLUDED.name,category_id=EXCLUDED.category_id,
                      description=EXCLUDED.description,geometry=EXCLUDED.geometry,
                      properties=EXCLUDED.properties,
                      source=EXCLUDED.source,source_id=EXCLUDED.source_id,updated_at=now()
                """),
                    {
                        "id": object_id,
                        "name": record.name,
                        "category": record.category_id,
                        "description": record.description,
                        "geometry": json.dumps(record.geometry),
                        "properties": json.dumps(record.properties),
                        "source": source.id,
                        "source_record": record_id,
                    },
                )
                stats.updated += int(existing is not None)
                stats.inserted += int(existing is None)
                stats.duplicates += int(existing is not None)
                collected = datetime.now(timezone.utc)
                connection.execute(
                    text("""
                    INSERT INTO object_provenance(
                      object_id,source_id,source_record_id,run_id,collected_at,confidence
                    )
                    VALUES (:object,:source,:record,:run,:collected,:confidence)
                    ON CONFLICT (object_id,source_id,source_record_id) DO UPDATE SET
                      run_id=EXCLUDED.run_id,collected_at=EXCLUDED.collected_at,checked_at=now(),
                      confidence=EXCLUDED.confidence
                """),
                    {
                        "object": object_id,
                        "source": source.id,
                        "record": record_id,
                        "run": run_id,
                        "collected": collected,
                        "confidence": record.confidence,
                    },
                )
                connection.execute(
                    text("""
                    UPDATE ingestion_staging SET normalized_payload=CAST(:payload AS jsonb),
                      validation_status='imported',canonical_object_id=:object WHERE id=:id
                """),
                    {"payload": json.dumps(normalized), "object": object_id, "id": staging_id},
                )
            connection.execute(
                text("""
                UPDATE ingestion_runs SET finished_at=now(),status='completed',objects_found=:found,
                  objects_inserted=:inserted,objects_updated=:updated,objects_skipped=:skipped,
                  duplicates=:duplicates,warnings=:warnings,errors=:errors WHERE id=:run
            """),
                {**stats.__dict__, "run": run_id},
            )
        except Exception:
            logger.exception(
                "Ingestion run failed", extra={"source_id": source.id, "module": module}
            )
            raise
    return run_id, stats
