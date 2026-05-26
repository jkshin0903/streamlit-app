"""technician CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.labels import col

from lib.repository._common import RepositoryError, has_ref


def list_technicians() -> list[dict[str, Any]]:
    return db_store.table_rows("technician")


def get_technician(technician_id: int) -> Optional[dict[str, Any]]:
    return db_store.find_by_pk("technician", technician_id)


def save_technician(record: dict[str, Any]) -> dict[str, Any]:
    if not record.get("technician_name"):
        raise RepositoryError(f"{col('technician_name')} is required.")
    if record.get("technician_id") is None:
        record["technician_id"] = db_store.next_id("technician")
    return db_store.upsert("technician", record)


def delete_technician(technician_id: int) -> None:
    if has_ref("order", "technician_id", technician_id):
        raise RepositoryError(
            "Cannot delete technician: referenced by order."
        )
    db_store.delete_row("technician", technician_id)
