"""invoice and invoice_item CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.constants import INVOICE_STATUSES
from lib.labels import col

from lib.repository._common import RepositoryError, exists, has_ref, iso_date, validate_enum
from lib.repository.purchase_order import get_po_vendor_id


def list_invoices() -> list[dict[str, Any]]:
    return db_store.table_rows("invoice")


def get_invoice(invoice_number: int) -> Optional[dict[str, Any]]:
    header = db_store.find_by_pk("invoice", invoice_number)
    if not header:
        return None
    header = dict(header)
    header["items"] = list_invoice_items(invoice_number)
    return header


def list_invoice_items(invoice_number: int) -> list[dict[str, Any]]:
    return db_store.filter_items("invoice_item", "invoice_number", invoice_number)


def save_invoice(header: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    validate_enum(header["invoice_status"], INVOICE_STATUSES, "invoice_status")
    po_id = header["purchase_order_id"]
    if not exists("purchase_order", "purchase_order_id", po_id):
        raise RepositoryError(f"Invalid {col('purchase_order_id')}.")
    expected_vendor = get_po_vendor_id(po_id)
    if header["vendor_id"] != expected_vendor:
        raise RepositoryError(
            f"{col('vendor_id')} must match the purchase order vendor."
        )
    if not header.get("terms"):
        raise RepositoryError(f"{col('terms')} is required.")
    if not items:
        raise RepositoryError("At least one invoice item is required.")
    header["invoice_date"] = iso_date(header["invoice_date"])
    inv_no = header.get("invoice_number")
    if inv_no is None:
        inv_no = db_store.next_id("invoice")
        header["invoice_number"] = inv_no
    norm_items = []
    for item in items:
        if not exists("product", "product_no", item["product_no"]):
            raise RepositoryError(f"Invalid {col('product_no')}.")
        qty = int(item["quantity"])
        price = float(item["unit_price"])
        if qty < 1 or price < 0:
            raise RepositoryError(
                f"Check {col('quantity')} and {col('unit_price')}."
            )
        norm_items.append(
            {
                "product_no": item["product_no"],
                "quantity": qty,
                "unit_price": price,
            }
        )
    db_store.upsert("invoice", header)
    db_store.replace_items(
        "invoice_item",
        "invoice_number",
        inv_no,
        norm_items,
    )
    return get_invoice(inv_no)  # type: ignore[return-value]


def delete_invoice(invoice_number: int) -> None:
    if has_ref("machine", "invoice_number", invoice_number):
        raise RepositoryError(
            "Cannot delete invoice: linked machine exists."
        )
    db_store.replace_items("invoice_item", "invoice_number", invoice_number, [])
    db_store.delete_row("invoice", invoice_number)
