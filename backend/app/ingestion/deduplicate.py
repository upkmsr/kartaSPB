from dataclasses import dataclass

from app.ingestion.models import ImportRecord
from app.ingestion.normalize import normalize_name


@dataclass(frozen=True)
class MatchKey:
    source_id: str
    normalized_name: str
    longitude: float | None
    latitude: float | None
    address: str | None
    aliases: tuple[str, ...]


def match_key(record: ImportRecord) -> MatchKey:
    coordinates = record.geometry.get("coordinates")
    lon = lat = None
    if (
        record.geometry.get("type") == "Point"
        and isinstance(coordinates, list)
        and len(coordinates) >= 2
    ):
        lon, lat = round(float(coordinates[0]), 6), round(float(coordinates[1]), 6)
    return MatchKey(
        source_id=record.source_id,
        normalized_name=normalize_name(record.name) or "",
        longitude=lon,
        latitude=lat,
        address=normalize_name(record.address),
        aliases=tuple(filter(None, (normalize_name(alias) for alias in record.aliases))),
    )
