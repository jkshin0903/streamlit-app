"""purchase_request and purchase_request_item CRUD."""

from __future__ import annotations

from typing import Any, Optional

from lib import db_store
from lib.constants import REQUEST_STATUSES
from lib.labels import col

from lib.repository._common import RepositoryError, exists, iso_date, validate_enum


def list_purchase_requests() -> list[dict[str, Any]]:
    return db_store.table_rows("purchase_request")


def get_purchase_request(pr_id: int) -> Optional[dict[str, Any]]:
    header = db_store.find_by_pk("purchase_request", pr_id)
    if not header:
        return None
    header = dict(header)
    header["items"] = list_purchase_request_items(pr_id)
    return header


def list_purchase_request_items(pr_id: int) -> list[dict[str, Any]]:
    return db_store.filter_items("purchase_request_item", "purchase_request_id", pr_id)


def save_purchase_request(
    header: dict[str, Any], items: list[dict[str, Any]]
) -> dict[str, Any]:
    validate_enum(header["request_status"], REQUEST_STATUSES, "request_status")
    if not exists("business_location", "location_id", header["location_id"]):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    if not items:
        raise RepositoryError("At least one purchase request item is required.")
    header["request_date"] = iso_date(header["request_date"])
    pr_id = header.get("purchase_request_id")
    if pr_id is None:
        pr_id = db_store.next_id("purchase_request")
        header["purchase_request_id"] = pr_id
    for item in items:
        if not exists("product", "product_no", item["product_no"]):
            raise RepositoryError(f"Invalid {col('product_no')}.")
        if int(item["quantity"]) < 1:
            raise RepositoryError(f"{col('quantity')} must be at least 1.")
    db_store.upsert("purchase_request", header)
    db_store.replace_items(
        "purchase_request_item",
        "purchase_request_id",
        pr_id,
        [{"product_no": i["product_no"], "quantity": int(i["quantity"])} for i in items],
    )
    return get_purchase_request(pr_id)  # type: ignore[return-value]


def delete_purchase_request(pr_id: int) -> None:
    db_store.replace_items("purchase_request_item", "purchase_request_id", pr_id, [])
    db_store.delete_row("purchase_request", pr_id)
