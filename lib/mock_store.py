"""In-memory store backed by session_state."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Optional

import streamlit as st

SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "seed.json"

TABLES = [
    "business_location",
    "vendor",
    "product",
    "technician",
    "purchase_request",
    "purchase_request_item",
    "purchase_order",
    "purchase_order_item",
    "invoice",
    "invoice_item",
    "contract",
    "machine",
    "machine_contract_hst",
    "order",
]

PK_FIELDS = {
    "business_location": "location_id",
    "vendor": "vendor_id",
    "product": "product_no",
    "technician": "technician_id",
    "purchase_request": "purchase_request_id",
    "purchase_order": "purchase_order_id",
    "invoice": "invoice_number",
    "contract": "contract_id",
    "machine": "serial_number",
    "machine_contract_hst": "machine_contract_no",
    "order": "order_id",
}


def _empty_store() -> dict[str, list[dict[str, Any]]]:
    return {name: [] for name in TABLES}


def load_seed() -> dict[str, list[dict[str, Any]]]:
    with open(SEED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    store = _empty_store()
    for table in TABLES:
        store[table] = data.get(table, [])
    return store


def get_store() -> dict[str, list[dict[str, Any]]]:
    if "store" not in st.session_state:
        st.session_state.store = load_seed()
    return st.session_state.store


def reset_store() -> None:
    st.session_state.store = load_seed()


def table_rows(table: str) -> list[dict[str, Any]]:
    return get_store()[table]


def find_by_pk(table: str, pk_value: Any) -> Optional[dict[str, Any]]:
    pk_field = PK_FIELDS[table]
    for row in table_rows(table):
        if row.get(pk_field) == pk_value:
            return copy.deepcopy(row)
    return None


def next_id(table: str) -> int:
    pk_field = PK_FIELDS[table]
    rows = table_rows(table)
    if not rows:
        return 1
    return max(int(r[pk_field]) for r in rows) + 1


def upsert(table: str, record: dict[str, Any]) -> dict[str, Any]:
    store = get_store()
    pk_field = PK_FIELDS[table]
    pk_value = record[pk_field]
    rows = store[table]
    for i, row in enumerate(rows):
        if row[pk_field] == pk_value:
            rows[i] = copy.deepcopy(record)
            return record
    rows.append(copy.deepcopy(record))
    return record


def delete_row(table: str, pk_value: Any) -> bool:
    store = get_store()
    pk_field = PK_FIELDS[table]
    rows = store[table]
    for i, row in enumerate(rows):
        if row[pk_field] == pk_value:
            del rows[i]
            return True
    return False


def filter_items(parent_table: str, parent_id_field: str, parent_id: Any) -> list[dict[str, Any]]:
    return [r for r in table_rows(parent_table) if r.get(parent_id_field) == parent_id]


def replace_items(
    item_table: str,
    parent_id_field: str,
    parent_id: Any,
    items: list[dict[str, Any]],
) -> None:
    store = get_store()
    store[item_table] = [
        r for r in store[item_table] if r.get(parent_id_field) != parent_id
    ]
    for item in items:
        row = copy.deepcopy(item)
        row[parent_id_field] = parent_id
        store[item_table].append(row)
