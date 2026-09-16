"""Shared source-field normalization for education modules."""

from datetime import datetime
from typing import Any


def operator_type(tags: dict[str, Any]) -> str:
    value = tags.get("operator:type")
    return value if value in {"public", "private"} else "unknown"


def address(tags: dict[str, Any]) -> str | None:
    return (
        tags.get("addr:full")
        or ", ".join(filter(None, [tags.get("addr:street"), tags.get("addr:housenumber")]))
        or None
    )


def confidence(tags: dict[str, Any]) -> float:
    return round(
        0.5
        + sum(
            (
                0.1 if address(tags) else 0,
                0.1 if tags.get("website") or tags.get("contact:website") else 0,
                0.1 if tags.get("ref") else 0,
                0.1 if operator_type(tags) != "unknown" else 0,
            )
        ),
        2,
    )


def valid_check_date(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        return None
