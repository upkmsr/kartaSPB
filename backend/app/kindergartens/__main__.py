from app.kindergartens.importer import run

if __name__ == "__main__":
    run_id, stats = run()
    print(
        f"run={run_id} found={stats.found} inserted={stats.inserted} "
        f"updated={stats.updated} skipped={stats.skipped} errors={stats.errors}"
    )
