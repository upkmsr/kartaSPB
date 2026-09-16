from app.ingestion.models import ImportRecord, SourceDefinition
from app.ingestion.pipeline import import_records

SOURCE = SourceDefinition(
    id="test-fixture", name="Explicit ingestion test fixture", type="fixture",
    url="local://backend/app/ingestion/test_importer.py", license="project fixture",
    attribution="KARTASPB test fixture", notes="Non-production synthetic acceptance record",
)


def run() -> None:
    records = [("point-1", {"fixture": True}, ImportRecord(
        source_id="test-fixture", name="Тестовый объект ingestion",
        category_id="demo", geometry={"type": "Point", "coordinates": [30.3158, 59.9391]},
        properties={"fixture": True},
    ))]
    run_id, stats = import_records(SOURCE, "test", records)
    print(
        f"run={run_id} found={stats.found} inserted={stats.inserted} "
        f"updated={stats.updated} errors={stats.errors}"
    )


if __name__ == "__main__":
    run()
