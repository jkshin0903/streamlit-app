"""contract CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.constants import CONTRACT_STATUSES
from lib.labels import col

from lib.repository._common import (
    RepositoryError,
    exists,
    has_ref,
    iso_date,
    optional_iso_date,
    validate_enum,
)


def list_contracts() -> list[dict[str, Any]]:
    return db_store.table_rows("contract")


def get_contract(contract_id: int) -> Optional[dict[str, Any]]:
    return db_store.find_by_pk("contract", contract_id)


def save_contract(record: dict[str, Any]) -> dict[str, Any]:
    validate_enum(record["contract_status"], CONTRACT_STATUSES, "contract_status")
    if not exists("business_location", "location_id", record["location_id"]):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    record["contract_date"] = iso_date(record["contract_date"])
    record["start_date"] = iso_date(record["start_date"])
    record["end_date"] = iso_date(record["end_date"])
    record["pickup_date"] = optional_iso_date(record.get("pickup_date"))
    if record.get("contract_id") is None:
        record["contract_id"] = db_store.next_id("contract")
    return db_store.upsert("contract", record)


def delete_contract(contract_id: int) -> None:
    if has_ref("machine_contract_hst", "contract_id", contract_id):
        raise RepositoryError(
            "Cannot delete contract: machine contract history exists."
        )
    db_store.delete_row("contract", contract_id)
