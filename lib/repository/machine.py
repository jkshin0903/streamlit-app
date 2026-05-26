"""machine and machine_contract_hst CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.constants import MACHINE_STATUSES
from lib.labels import col

from lib.repository._common import (
    RepositoryError,
    exists,
    has_ref,
    iso_date,
    validate_enum,
)


def list_machines() -> list[dict[str, Any]]:
    return db_store.table_rows("machine")


def get_machine(serial_number: int) -> Optional[dict[str, Any]]:
    return db_store.find_by_pk("machine", serial_number)


def save_machine(record: dict[str, Any]) -> dict[str, Any]:
    validate_enum(record["machine_status"], MACHINE_STATUSES, "machine_status")
    if not exists("invoice", "invoice_number", record["invoice_number"]):
        raise RepositoryError(f"Invalid {col('invoice_number')}.")
    loc = record.get("location_id")
    if loc is not None and not exists("business_location", "location_id", loc):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    if record.get("serial_number") is None:
        record["serial_number"] = db_store.next_id("machine")
    return db_store.upsert("machine", record)


def delete_machine(serial_number: int) -> None:
    if has_ref("order", "serial_number", serial_number):
        raise RepositoryError("Cannot delete machine: referenced by order.")
    db_store.delete_machine_contract_hst_by_serial(serial_number)
    db_store.delete_row("machine", serial_number)


def list_machine_contract_hst(serial_number: int) -> list[dict[str, Any]]:
    return db_store.filter_items("machine_contract_hst", "serial_number", serial_number)


def save_machine_contract_hst(record: dict[str, Any]) -> dict[str, Any]:
    if not exists("machine", "serial_number", record["serial_number"]):
        raise RepositoryError(f"Invalid {col('serial_number')}.")
    if not exists("contract", "contract_id", record["contract_id"]):
        raise RepositoryError(f"Invalid {col('contract_id')}.")
    record["contract_start_date"] = iso_date(record["contract_start_date"])
    record["contract_end_date"] = iso_date(record["contract_end_date"])
    if record.get("machine_contract_no") is None:
        record["machine_contract_no"] = db_store.next_id("machine_contract_hst")
    return db_store.upsert("machine_contract_hst", record)
