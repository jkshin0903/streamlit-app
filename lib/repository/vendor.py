"""vendor CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.labels import col

from lib.repository._common import RepositoryError, has_ref


def list_vendors() -> list[dict[str, Any]]:
    return db_store.table_rows("vendor")


def get_vendor(vendor_id: int) -> Optional[dict[str, Any]]:
    return db_store.find_by_pk("vendor", vendor_id)


def save_vendor(record: dict[str, Any]) -> dict[str, Any]:
    if not record.get("vendor_name"):
        raise RepositoryError(f"{col('vendor_name')} is required.")
    if not record.get("address"):
        raise RepositoryError(f"{col('address')} is required.")
    if record.get("vendor_id") is None:
        record["vendor_id"] = db_store.next_id("vendor")
    return db_store.upsert("vendor", record)


def delete_vendor(vendor_id: int) -> None:
    for table, field in [("purchase_order", "vendor_id"), ("invoice", "vendor_id")]:
        if has_ref(table, field, vendor_id):
            raise RepositoryError(
                f"Cannot delete vendor id {vendor_id}: still referenced."
            )
    db_store.delete_row("vendor", vendor_id)
