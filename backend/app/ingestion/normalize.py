import re
import unicodedata
from typing import Any


def normalize_text(value: object) -> str | None:
    if value is None:
        return None
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def normalize_name(value: object) -> str | None:
    text = normalize_text(value)
    return text.casefold() if text else None


def normalize_identifier(value: object) -> str | None:
    text = normalize_text(value)
    return re.sub(r"[^a-z0-9:._-]+", "-", text.casefold()).strip("-") if text else None


def normalize_coordinates(value: object) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        return None
    try:
        lon, lat = float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None
    return (lon, lat) if -180 <= lon <= 180 and -90 <= lat <= 90 else None


def remove_empty(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: cleaned
            for key, item in value.items()
            if (cleaned := remove_empty(item)) is not None
        }
    if isinstance(value, list):
        return [cleaned for item in value if (cleaned := remove_empty(item)) is not None]
    if isinstance(value, str):
        return normalize_text(value)
    return value
