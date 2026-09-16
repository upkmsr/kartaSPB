import argparse

from app.open_data.overpass import run

parser = argparse.ArgumentParser(description="Import bounded OpenStreetMap base snapshot")
parser.add_argument("--refresh", action="store_true", help="Fetch a current bounded snapshot")

if __name__ == "__main__":
    args = parser.parse_args()
    run_id, stats = run(args.refresh)
    print(
        f"run={run_id} found={stats.found} inserted={stats.inserted} "
        f"updated={stats.updated} skipped={stats.skipped} errors={stats.errors}"
    )
