"""product CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.labels import col

from lib.repository._common import RepositoryError, has_ref


def list_products() -> list[dict[str, Any]]:
    return db_store.table_rows("product")


def get_product(product_no: int) -> Optional[dict[str, Any]]:
    return db_store.find_by_pk("product", product_no)


def save_product(record: dict[str, Any]) -> dict[str, Any]:
    if not record.get("product_name"):
        raise RepositoryError(f"{col('product_name')} is required.")
    if record.get("product_no") is None:
        record["product_no"] = db_store.next_id("product")
    return db_store.upsert("product", record)


def delete_product(product_no: int) -> None:
    for table in ("purchase_request_item", "purchase_order_item", "invoice_item"):
        if has_ref(table, "product_no", product_no):
            raise RepositoryError(
                f"Cannot delete product no {product_no}: still referenced in line items."
            )
    db_store.delete_row("product", product_no)
