"""business_location CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.constants import LOCATION_TYPES
from lib.labels import col

from lib.repository._common import RepositoryError, has_ref, validate_enum


def list_locations() -> list[dict[str, Any]]:
    return db_store.table_rows("business_location")


def get_location(location_id: int) -> Optional[dict[str, Any]]:
    return db_store.find_by_pk("business_location", location_id)


def save_location(record: dict[str, Any]) -> dict[str, Any]:
    validate_enum(record["location_type"], LOCATION_TYPES, "location_type")
    if not record.get("location_name"):
        raise RepositoryError(f"{col('location_name')} is required.")
    lid = record.get("location_id")
    if lid is None:
        record["location_id"] = db_store.next_id("business_location")
    return db_store.upsert("business_location", record)


def delete_location(location_id: int) -> None:
    refs = [
        ("contract", "location_id"),
        ("purchase_request", "location_id"),
        ("machine", "location_id"),
        ("order", "location_id"),
        ("order", "from_location_id"),
        ("order", "to_location_id"),
    ]
    for table, field in refs:
        if has_ref(table, field, location_id):
            raise RepositoryError(
                f"Cannot delete location id {location_id}: referenced by {table}."
            )
    db_store.delete_row("business_location", location_id)
