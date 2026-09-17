from app.noise.importer import run

if __name__ == "__main__":
    for kind, (run_id, stats) in zip(("railway", "road"), run()):
        print(
            f"{kind} run={run_id} found={stats.found} inserted={stats.inserted} "
            f"updated={stats.updated} skipped={stats.skipped} errors={stats.errors}"
        )
