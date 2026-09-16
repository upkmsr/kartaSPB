from dataclasses import dataclass
from typing import Any

from app.ingestion.models import ImportRecord

EXPECTED_BOUNDS = (27.0, 58.0, 32.5, 61.5)
GEOMETRY_TYPES = {"Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"}


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]


def _coordinates(value: Any) -> list[tuple[float, float]]:
    if isinstance(value, (list, tuple)):
        if len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            return [(float(value[0]), float(value[1]))]
        return [coordinate for item in value for coordinate in _coordinates(item)]
    return []


def validate_record(record: ImportRecord) -> ValidationResult:
    errors: list[str] = []
    if not record.source_id.strip():
        errors.append("source is required")
    if not record.name.strip():
        errors.append("name is required")
    geometry_type = record.geometry.get("type")
    coordinates = _coordinates(record.geometry.get("coordinates"))
    if geometry_type not in GEOMETRY_TYPES:
        errors.append("unsupported geometry type")
    if not coordinates:
        errors.append("geometry has no coordinates")
    west, south, east, north = EXPECTED_BOUNDS
    if any(not (-180 <= x <= 180 and -90 <= y <= 90) for x, y in coordinates):
        errors.append("coordinates are invalid")
    elif any(not (west <= x <= east and south <= y <= north) for x, y in coordinates):
        errors.append("geometry is outside expected geography")
    if not 0 <= record.confidence <= 1:
        errors.append("confidence must be between 0 and 1")
    return ValidationResult(not errors, tuple(errors))
