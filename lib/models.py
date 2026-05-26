"""Table-shaped record helpers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional


def to_date_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value[:10] if value else None
    return str(value)


def parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value:
        return date.fromisoformat(value[:10])
    return None


def record_to_dict(record: dict[str, Any]) -> dict[str, Any]:
    return dict(record)
