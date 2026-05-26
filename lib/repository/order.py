"""order CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.constants import ORDER_STATUSES, ORDER_TYPES
from lib.labels import col

from lib.repository._common import (
    RepositoryError,
    exists,
    iso_date,
    optional_iso_date,
    validate_enum,
)


def list_orders() -> list[dict[str, Any]]:
    return db_store.table_rows("order")


def get_order(order_id: int) -> Optional[dict[str, Any]]:
    return db_store.find_by_pk("order", order_id)


def save_order(record: dict[str, Any]) -> dict[str, Any]:
    validate_enum(record["order_type"], ORDER_TYPES, "order_type")
    validate_enum(record["order_status"], ORDER_STATUSES, "order_status")
    if not exists("machine", "serial_number", record["serial_number"]):
        raise RepositoryError(f"Invalid {col('serial_number')}.")
    if not exists("business_location", "location_id", record["to_location_id"]):
        raise RepositoryError(f"Invalid {col('to_location_id')}.")
    tech = record.get("technician_id")
    if tech is not None and not exists("technician", "technician_id", tech):
        raise RepositoryError(f"Invalid {col('technician_id')}.")
    cust = record.get("location_id")
    if cust is not None and not exists("business_location", "location_id", cust):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    for fld in ("from_location_id",):
        val = record.get(fld)
        if val is not None and not exists("business_location", "location_id", val):
            raise RepositoryError(f"Invalid {col(fld)}.")
    record["request_date"] = iso_date(record["request_date"])
    record["completion_date"] = optional_iso_date(record.get("completion_date"))
    if record.get("order_id") is None:
        record["order_id"] = db_store.next_id("order")
    return db_store.upsert("order", record)


def delete_order(order_id: int) -> None:
    db_store.delete_row("order", order_id)
