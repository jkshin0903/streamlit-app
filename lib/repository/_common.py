"""Shared repository utilities and DB bootstrap."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.db import DbConfigError, get_engine
from lib.labels import col
from lib.models import parse_date


class RepositoryError(Exception):
    pass


def init_if_needed() -> None:
    try:
        get_engine()
    except DbConfigError:
        raise


def reset_demo_data() -> None:
    raise RepositoryError(
        "Demo reset is disabled when using the live database."
    )


def exists(table: str, pk_field: str, pk_value: Any) -> bool:
    if pk_value is None:
        return False
    return db_store.count_where(table, pk_field, pk_value) > 0


def has_ref(table: str, field: str, value: Any) -> bool:
    return db_store.count_where(table, field, value) > 0


def validate_enum(value: str, allowed: list[str], field: str) -> None:
    if value not in allowed:
        raise RepositoryError(
            f"{col(field)} must be one of: {', '.join(allowed)}"
        )


def iso_date(value: Any) -> str:
    d = parse_date(value)
    if d is None:
        raise RepositoryError("Invalid date value.")
    return d.isoformat()


def optional_iso_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    return iso_date(value)
