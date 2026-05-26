"""CRUD facade over mock store with FK validation."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Optional

from lib import mock_store
from lib.constants import (
    CONTRACT_STATUSES,
    INVOICE_STATUSES,
    LOCATION_TYPES,
    MACHINE_STATUSES,
    ORDER_STATUSES,
    ORDER_TYPES,
    PURCHASE_ORDER_STATUSES,
    REQUEST_STATUSES,
)
from lib.labels import col
from lib.models import parse_date, to_date_str


class RepositoryError(Exception):
    pass


def init_if_needed() -> None:
    mock_store.get_store()


def reset_demo_data() -> None:
    mock_store.reset_store()


# --- helpers ---


def _exists(table: str, pk_field: str, pk_value: Any) -> bool:
    if pk_value is None:
        return False
    return any(r.get(pk_field) == pk_value for r in mock_store.table_rows(table))


def _validate_enum(value: str, allowed: list[str], field: str) -> None:
    if value not in allowed:
        raise RepositoryError(
            f"{col(field)} must be one of: {', '.join(allowed)}"
        )


def _iso_date(value: Any) -> str:
    d = parse_date(value)
    if d is None:
        raise RepositoryError("Invalid date value.")
    return d.isoformat()


def _optional_iso_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    return _iso_date(value)


# --- business_location ---


def list_locations() -> list[dict[str, Any]]:
    return mock_store.table_rows("business_location")


def get_location(location_id: int) -> Optional[dict[str, Any]]:
    return mock_store.find_by_pk("business_location", location_id)


def save_location(record: dict[str, Any]) -> dict[str, Any]:
    _validate_enum(record["location_type"], LOCATION_TYPES, "location_type")
    if not record.get("location_name"):
        raise RepositoryError(f"{col('location_name')} is required.")
    lid = record.get("location_id")
    if lid is None:
        record["location_id"] = mock_store.next_id("business_location")
    return mock_store.upsert("business_location", record)


def delete_location(location_id: int) -> None:
    refs = [
        ("contract", "location_id"),
        ("purchase_request", "location_id"),
        ("machine", "location_id"),
        ("order", "location_id"),
        ("order", "from_location_id"),
        ("order", "to_location_id"),
    ]
    for table, field in refs:
        if any(r.get(field) == location_id for r in mock_store.table_rows(table)):
            raise RepositoryError(
                f"Cannot delete location id {location_id}: referenced by {table}."
            )
    mock_store.delete_row("business_location", location_id)


# --- vendor ---


def list_vendors() -> list[dict[str, Any]]:
    return mock_store.table_rows("vendor")


def get_vendor(vendor_id: int) -> Optional[dict[str, Any]]:
    return mock_store.find_by_pk("vendor", vendor_id)


def save_vendor(record: dict[str, Any]) -> dict[str, Any]:
    if not record.get("vendor_name"):
        raise RepositoryError(f"{col('vendor_name')} is required.")
    if not record.get("address"):
        raise RepositoryError(f"{col('address')} is required.")
    if record.get("vendor_id") is None:
        record["vendor_id"] = mock_store.next_id("vendor")
    return mock_store.upsert("vendor", record)


def delete_vendor(vendor_id: int) -> None:
    for table, field in [("purchase_order", "vendor_id"), ("invoice", "vendor_id")]:
        if any(r.get(field) == vendor_id for r in mock_store.table_rows(table)):
            raise RepositoryError(
                f"Cannot delete vendor id {vendor_id}: still referenced."
            )
    mock_store.delete_row("vendor", vendor_id)


# --- product ---


def list_products() -> list[dict[str, Any]]:
    return mock_store.table_rows("product")


def get_product(product_no: int) -> Optional[dict[str, Any]]:
    return mock_store.find_by_pk("product", product_no)


def save_product(record: dict[str, Any]) -> dict[str, Any]:
    if not record.get("product_name"):
        raise RepositoryError(f"{col('product_name')} is required.")
    if record.get("product_no") is None:
        record["product_no"] = mock_store.next_id("product")
    return mock_store.upsert("product", record)


def delete_product(product_no: int) -> None:
    for table in ("purchase_request_item", "purchase_order_item", "invoice_item"):
        if any(r.get("product_no") == product_no for r in mock_store.table_rows(table)):
            raise RepositoryError(
                f"Cannot delete product no {product_no}: still referenced in line items."
            )
    mock_store.delete_row("product", product_no)


# --- technician ---


def list_technicians() -> list[dict[str, Any]]:
    return mock_store.table_rows("technician")


def get_technician(technician_id: int) -> Optional[dict[str, Any]]:
    return mock_store.find_by_pk("technician", technician_id)


def save_technician(record: dict[str, Any]) -> dict[str, Any]:
    if not record.get("technician_name"):
        raise RepositoryError(f"{col('technician_name')} is required.")
    if record.get("technician_id") is None:
        record["technician_id"] = mock_store.next_id("technician")
    return mock_store.upsert("technician", record)


def delete_technician(technician_id: int) -> None:
    if any(r.get("technician_id") == technician_id for r in mock_store.table_rows("order")):
        raise RepositoryError(
            "Cannot delete technician: referenced by order."
        )
    mock_store.delete_row("technician", technician_id)


# --- contract ---


def list_contracts() -> list[dict[str, Any]]:
    return mock_store.table_rows("contract")


def get_contract(contract_id: int) -> Optional[dict[str, Any]]:
    return mock_store.find_by_pk("contract", contract_id)


def save_contract(record: dict[str, Any]) -> dict[str, Any]:
    _validate_enum(record["contract_status"], CONTRACT_STATUSES, "contract_status")
    if not _exists("business_location", "location_id", record["location_id"]):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    record["contract_date"] = _iso_date(record["contract_date"])
    record["start_date"] = _iso_date(record["start_date"])
    record["end_date"] = _iso_date(record["end_date"])
    record["pickup_date"] = _optional_iso_date(record.get("pickup_date"))
    if record.get("contract_id") is None:
        record["contract_id"] = mock_store.next_id("contract")
    return mock_store.upsert("contract", record)


def delete_contract(contract_id: int) -> None:
    if any(
        r.get("contract_id") == contract_id
        for r in mock_store.table_rows("machine_contract_hst")
    ):
        raise RepositoryError(
            "Cannot delete contract: machine contract history exists."
        )
    mock_store.delete_row("contract", contract_id)


# --- machine ---


def list_machines() -> list[dict[str, Any]]:
    return mock_store.table_rows("machine")


def get_machine(serial_number: int) -> Optional[dict[str, Any]]:
    return mock_store.find_by_pk("machine", serial_number)


def save_machine(record: dict[str, Any]) -> dict[str, Any]:
    _validate_enum(record["machine_status"], MACHINE_STATUSES, "machine_status")
    if not _exists("invoice", "invoice_number", record["invoice_number"]):
        raise RepositoryError(f"Invalid {col('invoice_number')}.")
    loc = record.get("location_id")
    if loc is not None and not _exists("business_location", "location_id", loc):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    if record.get("serial_number") is None:
        record["serial_number"] = mock_store.next_id("machine")
    return mock_store.upsert("machine", record)


def delete_machine(serial_number: int) -> None:
    if any(r.get("serial_number") == serial_number for r in mock_store.table_rows("order")):
        raise RepositoryError("Cannot delete machine: referenced by order.")
    store = mock_store.get_store()
    store["machine_contract_hst"] = [
        r
        for r in store["machine_contract_hst"]
        if r.get("serial_number") != serial_number
    ]
    mock_store.delete_row("machine", serial_number)


# --- machine_contract_hst ---


def list_machine_contract_hst(serial_number: int) -> list[dict[str, Any]]:
    return mock_store.filter_items("machine_contract_hst", "serial_number", serial_number)


def save_machine_contract_hst(record: dict[str, Any]) -> dict[str, Any]:
    if not _exists("machine", "serial_number", record["serial_number"]):
        raise RepositoryError(f"Invalid {col('serial_number')}.")
    if not _exists("contract", "contract_id", record["contract_id"]):
        raise RepositoryError(f"Invalid {col('contract_id')}.")
    record["contract_start_date"] = _iso_date(record["contract_start_date"])
    record["contract_end_date"] = _iso_date(record["contract_end_date"])
    if record.get("machine_contract_no") is None:
        record["machine_contract_no"] = mock_store.next_id("machine_contract_hst")
    return mock_store.upsert("machine_contract_hst", record)


# --- order ---


def list_orders() -> list[dict[str, Any]]:
    return mock_store.table_rows("order")


def get_order(order_id: int) -> Optional[dict[str, Any]]:
    return mock_store.find_by_pk("order", order_id)


def save_order(record: dict[str, Any]) -> dict[str, Any]:
    _validate_enum(record["order_type"], ORDER_TYPES, "order_type")
    _validate_enum(record["order_status"], ORDER_STATUSES, "order_status")
    if not _exists("machine", "serial_number", record["serial_number"]):
        raise RepositoryError(f"Invalid {col('serial_number')}.")
    if not _exists("business_location", "location_id", record["to_location_id"]):
        raise RepositoryError(f"Invalid {col('to_location_id')}.")
    tech = record.get("technician_id")
    if tech is not None and not _exists("technician", "technician_id", tech):
        raise RepositoryError(f"Invalid {col('technician_id')}.")
    cust = record.get("location_id")
    if cust is not None and not _exists("business_location", "location_id", cust):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    for fld in ("from_location_id",):
        val = record.get(fld)
        if val is not None and not _exists("business_location", "location_id", val):
            raise RepositoryError(f"Invalid {col(fld)}.")
    record["request_date"] = _iso_date(record["request_date"])
    record["completion_date"] = _optional_iso_date(record.get("completion_date"))
    if record.get("order_id") is None:
        record["order_id"] = mock_store.next_id("order")
    return mock_store.upsert("order", record)


def delete_order(order_id: int) -> None:
    mock_store.delete_row("order", order_id)


# --- purchase_request ---


def list_purchase_requests() -> list[dict[str, Any]]:
    return mock_store.table_rows("purchase_request")


def get_purchase_request(pr_id: int) -> Optional[dict[str, Any]]:
    header = mock_store.find_by_pk("purchase_request", pr_id)
    if not header:
        return None
    header = dict(header)
    header["items"] = list_purchase_request_items(pr_id)
    return header


def list_purchase_request_items(pr_id: int) -> list[dict[str, Any]]:
    return mock_store.filter_items("purchase_request_item", "purchase_request_id", pr_id)


def save_purchase_request(header: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_enum(header["request_status"], REQUEST_STATUSES, "request_status")
    if not _exists("business_location", "location_id", header["location_id"]):
        raise RepositoryError(f"Invalid {col('location_id')}.")
    if not items:
        raise RepositoryError("At least one purchase request item is required.")
    header["request_date"] = _iso_date(header["request_date"])
    pr_id = header.get("purchase_request_id")
    if pr_id is None:
        pr_id = mock_store.next_id("purchase_request")
        header["purchase_request_id"] = pr_id
    for item in items:
        if not _exists("product", "product_no", item["product_no"]):
            raise RepositoryError(f"Invalid {col('product_no')}.")
        if int(item["quantity"]) < 1:
            raise RepositoryError(f"{col('quantity')} must be at least 1.")
    mock_store.upsert("purchase_request", header)
    mock_store.replace_items(
        "purchase_request_item",
        "purchase_request_id",
        pr_id,
        [{"product_no": i["product_no"], "quantity": int(i["quantity"])} for i in items],
    )
    return get_purchase_request(pr_id)  # type: ignore


def delete_purchase_request(pr_id: int) -> None:
    mock_store.replace_items("purchase_request_item", "purchase_request_id", pr_id, [])
    mock_store.delete_row("purchase_request", pr_id)


# --- purchase_order ---


def list_purchase_orders() -> list[dict[str, Any]]:
    return mock_store.table_rows("purchase_order")


def get_purchase_order(po_id: int) -> Optional[dict[str, Any]]:
    header = mock_store.find_by_pk("purchase_order", po_id)
    if not header:
        return None
    header = dict(header)
    header["items"] = list_purchase_order_items(po_id)
    return header


def list_purchase_order_items(po_id: int) -> list[dict[str, Any]]:
    return mock_store.filter_items("purchase_order_item", "purchase_order_id", po_id)


def save_purchase_order(header: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_enum(
        header["purchase_order_status"], PURCHASE_ORDER_STATUSES, "purchase_order_status"
    )
    if not _exists("vendor", "vendor_id", header["vendor_id"]):
        raise RepositoryError(f"Invalid {col('vendor_id')}.")
    if not items:
        raise RepositoryError("At least one purchase order item is required.")
    header["purchase_order_date"] = _iso_date(header["purchase_order_date"])
    po_id = header.get("purchase_order_id")
    if po_id is None:
        po_id = mock_store.next_id("purchase_order")
        header["purchase_order_id"] = po_id
    norm_items = []
    for item in items:
        if not _exists("product", "product_no", item["product_no"]):
            raise RepositoryError(f"Invalid {col('product_no')}.")
        qty = int(item["quantity"])
        price = float(item["unit_price"])
        if qty < 1:
            raise RepositoryError(f"{col('quantity')} must be at least 1.")
        if price < 0:
            raise RepositoryError(f"{col('unit_price')} must be 0 or greater.")
        norm_items.append(
            {
                "product_no": item["product_no"],
                "quantity": qty,
                "unit_price": price,
            }
        )
    mock_store.upsert("purchase_order", header)
    mock_store.replace_items(
        "purchase_order_item",
        "purchase_order_id",
        po_id,
        norm_items,
    )
    return get_purchase_order(po_id)  # type: ignore


def delete_purchase_order(po_id: int) -> None:
    if any(r.get("purchase_order_id") == po_id for r in mock_store.table_rows("invoice")):
        raise RepositoryError(
            "Cannot delete purchase order: linked invoice exists."
        )
    mock_store.replace_items("purchase_order_item", "purchase_order_id", po_id, [])
    mock_store.delete_row("purchase_order", po_id)


def get_po_vendor_id(po_id: int) -> Optional[int]:
    po = get_purchase_order(po_id)
    return po["vendor_id"] if po else None


# --- invoice ---


def list_invoices() -> list[dict[str, Any]]:
    return mock_store.table_rows("invoice")


def get_invoice(invoice_number: int) -> Optional[dict[str, Any]]:
    header = mock_store.find_by_pk("invoice", invoice_number)
    if not header:
        return None
    header = dict(header)
    header["items"] = list_invoice_items(invoice_number)
    return header


def list_invoice_items(invoice_number: int) -> list[dict[str, Any]]:
    return mock_store.filter_items("invoice_item", "invoice_number", invoice_number)


def save_invoice(header: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    _validate_enum(header["invoice_status"], INVOICE_STATUSES, "invoice_status")
    po_id = header["purchase_order_id"]
    if not _exists("purchase_order", "purchase_order_id", po_id):
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
    header["invoice_date"] = _iso_date(header["invoice_date"])
    inv_no = header.get("invoice_number")
    if inv_no is None:
        inv_no = mock_store.next_id("invoice")
        header["invoice_number"] = inv_no
    norm_items = []
    for item in items:
        if not _exists("product", "product_no", item["product_no"]):
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
    mock_store.upsert("invoice", header)
    mock_store.replace_items(
        "invoice_item",
        "invoice_number",
        inv_no,
        norm_items,
    )
    return get_invoice(inv_no)  # type: ignore


def delete_invoice(invoice_number: int) -> None:
    if any(
        r.get("invoice_number") == invoice_number
        for r in mock_store.table_rows("machine")
    ):
        raise RepositoryError(
            "Cannot delete invoice: linked machine exists."
        )
    mock_store.replace_items("invoice_item", "invoice_number", invoice_number, [])
    mock_store.delete_row("invoice", invoice_number)


# --- display helpers ---


def location_label(location_id: Optional[int]) -> str:
    if location_id is None:
        return "(none)"
    loc = get_location(location_id)
    return f"{loc['location_name']} ({location_id})" if loc else f"#{location_id}"


def vendor_label(vendor_id: int) -> str:
    v = get_vendor(vendor_id)
    return f"{v['vendor_name']} ({vendor_id})" if v else f"#{vendor_id}"


def product_label(product_no: int) -> str:
    p = get_product(product_no)
    return f"{p['product_name']} ({product_no})" if p else f"#{product_no}"


def technician_label(technician_id: int) -> str:
    t = get_technician(technician_id)
    return f"{t['technician_name']} ({technician_id})" if t else f"#{technician_id}"


def id_options(
    rows: list[dict[str, Any]],
    id_field: str,
    label_fn: Callable[[Any], str],
) -> tuple[list[str], dict[str, Any]]:
    """Return display labels and label->id map."""
    mapping: dict[str, Any] = {}
    labels: list[str] = []
    for row in rows:
        pk = row[id_field]
        label = label_fn(pk)
        mapping[label] = pk
        labels.append(label)
    return labels, mapping


def optional_location_options() -> tuple[list[str], dict[str, Optional[int]]]:
    rows = list_locations()
    labels = ["(none)"]
    mapping: dict[str, Optional[int]] = {"(none)": None}
    for row in rows:
        lid = row["location_id"]
        label = f"{row['location_name']} ({lid})"
        labels.append(label)
        mapping[label] = lid
    return labels, mapping
