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


def _validate_move_locations(
    from_location_id: Optional[int],
    to_location_id: Optional[int],
) -> None:
    if from_location_id is None and to_location_id is None:
        raise RepositoryError(
            "Install or remove location is required (at least one)."
        )
    if (
        from_location_id is not None
        and to_location_id is not None
        and from_location_id == to_location_id
    ):
        raise RepositoryError("Install and remove location cannot be the same.")


def apply_machine_on_order_complete(record: dict[str, Any]) -> None:
    """Update machine location when order is marked completed (SCR-IN-02)."""
    if record.get("order_status") != "Completed":
        return
    m = db_store.find_by_pk("machine", record["serial_number"])
    if not m:
        return
    updated = dict(m)
    to_loc = record.get("to_location_id")
    if to_loc is not None:
        updated["location_id"] = to_loc
        updated["machine_status"] = "Operating"
    elif record.get("from_location_id") is not None:
        wh = _warehouse_location_id()
        if wh is not None:
            updated["location_id"] = wh
        updated["machine_status"] = "Idle"
    db_store.upsert("machine", updated)


def _warehouse_location_id() -> Optional[int]:
    for loc in db_store.table_rows("business_location"):
        if loc.get("location_type") == "Warehouse":
            return loc["location_id"]
    return None


def save_order(record: dict[str, Any]) -> dict[str, Any]:
    validate_enum(record["order_type"], ORDER_TYPES, "order_type")
    validate_enum(record["order_status"], ORDER_STATUSES, "order_status")
    if not exists("machine", "serial_number", record["serial_number"]):
        raise RepositoryError(f"Invalid {col('serial_number')}.")
    _validate_move_locations(
        record.get("from_location_id"),
        record.get("to_location_id"),
    )
    to_loc = record.get("to_location_id")
    if to_loc is not None and not exists("business_location", "location_id", to_loc):
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
    saved = db_store.upsert("order", record)
    apply_machine_on_order_complete(saved)
    return saved


def save_move_order_batch(
    header: dict[str, Any], lines: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Save one order row per machine line (schema: one serial per order)."""
    if not lines:
        raise RepositoryError("At least one machine line is required.")
    serials = [ln["serial_number"] for ln in lines]
    if len(serials) != len(set(serials)):
        raise RepositoryError("Duplicate serial numbers are not allowed on one order.")
    saved: list[dict[str, Any]] = []
    for ln in lines:
        payload = {**header, **ln}
        payload["order_id"] = ln.get("order_id")
        saved.append(save_order(payload))
    return saved


def delete_order(order_id: int) -> None:
    db_store.delete_row("order", order_id)
