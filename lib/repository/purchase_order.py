"""purchase_order and purchase_order_item CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.constants import LEGACY_PURCHASE_ORDER_STATUSES, PURCHASE_ORDER_STATUSES
from lib.labels import col

from lib.repository._common import RepositoryError, exists, has_ref, iso_date, validate_enum


def list_purchase_orders() -> list[dict[str, Any]]:
    return db_store.table_rows("purchase_order")


def get_purchase_order(po_id: int) -> Optional[dict[str, Any]]:
    header = db_store.find_by_pk("purchase_order", po_id)
    if not header:
        return None
    header = dict(header)
    header["items"] = list_purchase_order_items(po_id)
    return header


def list_purchase_order_items(po_id: int) -> list[dict[str, Any]]:
    return db_store.filter_items("purchase_order_item", "purchase_order_id", po_id)


def _allowed_po_statuses() -> list[str]:
    return PURCHASE_ORDER_STATUSES + LEGACY_PURCHASE_ORDER_STATUSES


def save_purchase_order(
    header: dict[str, Any], items: list[dict[str, Any]]
) -> dict[str, Any]:
    validate_enum(
        header["purchase_order_status"],
        _allowed_po_statuses(),
        "purchase_order_status",
    )
    if not exists("vendor", "vendor_id", header["vendor_id"]):
        raise RepositoryError(f"Invalid {col('vendor_id')}.")
    if not items:
        raise RepositoryError("At least one purchase order item is required.")
    header["purchase_order_date"] = iso_date(header["purchase_order_date"])
    po_id = header.get("purchase_order_id")
    if po_id is None:
        po_id = db_store.next_id("purchase_order")
        header["purchase_order_id"] = po_id
    norm_items = []
    for item in items:
        if not exists("product", "product_no", item["product_no"]):
            raise RepositoryError(f"Invalid {col('product_no')}.")
        qty = int(item["quantity"])
        price = float(item["unit_price"])
        if qty < 1:
            raise RepositoryError(f"{col('quantity')} must be at least 1.")
        if price <= 0:
            raise RepositoryError(f"{col('unit_price')} must be greater than 0.")
        norm_items.append(
            {
                "product_no": item["product_no"],
                "quantity": qty,
                "unit_price": price,
            }
        )
    db_store.upsert("purchase_order", header)
    db_store.replace_items(
        "purchase_order_item",
        "purchase_order_id",
        po_id,
        norm_items,
    )
    return get_purchase_order(po_id)  # type: ignore[return-value]


def delete_purchase_order(po_id: int) -> None:
    if has_ref("invoice", "purchase_order_id", po_id):
        raise RepositoryError(
            "Cannot delete purchase order: linked invoice exists."
        )
    db_store.replace_items("purchase_order_item", "purchase_order_id", po_id, [])
    db_store.delete_row("purchase_order", po_id)


def get_po_vendor_id(po_id: int) -> Optional[int]:
    po = get_purchase_order(po_id)
    return po["vendor_id"] if po else None
