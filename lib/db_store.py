"""MariaDB-backed store with the same surface as mock_store."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text

from lib.db import get_engine, normalize_row, quote_table

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

TABLE_COLUMNS: dict[str, list[str]] = {
    "business_location": [
        "location_id",
        "location_name",
        "location_type",
        "address",
        "city",
        "state",
        "zipcode",
        "phone",
    ],
    "vendor": ["vendor_id", "vendor_name", "address", "phone", "fax"],
    "product": ["product_no", "product_name"],
    "technician": ["technician_id", "technician_name"],
    "purchase_request": [
        "purchase_request_id",
        "location_id",
        "request_date",
        "request_status",
    ],
    "purchase_request_item": ["purchase_request_id", "product_no", "quantity"],
    "purchase_order": [
        "purchase_order_id",
        "vendor_id",
        "purchase_order_date",
        "purchase_order_status",
    ],
    "purchase_order_item": [
        "purchase_order_id",
        "product_no",
        "quantity",
        "unit_price",
    ],
    "invoice": [
        "invoice_number",
        "purchase_order_id",
        "vendor_id",
        "invoice_date",
        "invoice_status",
        "terms",
    ],
    "invoice_item": ["invoice_number", "product_no", "quantity", "unit_price"],
    "contract": [
        "contract_id",
        "location_id",
        "contract_date",
        "start_date",
        "end_date",
        "contract_status",
        "pickup_date",
        "pickup_reason",
    ],
    "machine": [
        "serial_number",
        "invoice_number",
        "location_id",
        "machine_name",
        "model_name",
        "machine_status",
    ],
    "machine_contract_hst": [
        "machine_contract_no",
        "serial_number",
        "contract_id",
        "contract_start_date",
        "contract_end_date",
    ],
    "order": [
        "order_id",
        "serial_number",
        "technician_id",
        "from_location_id",
        "to_location_id",
        "location_id",
        "order_type",
        "order_status",
        "completion_date",
        "request_date",
    ],
}


def pick_columns(table: str, record: dict[str, Any]) -> dict[str, Any]:
    allowed = TABLE_COLUMNS[table]
    return {k: record[k] for k in allowed if k in record}


def table_rows(table: str) -> list[dict[str, Any]]:
    engine = get_engine()
    sql = text(f"SELECT * FROM {quote_table(table)}")
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
    return [normalize_row(dict(r)) for r in rows]


def find_by_pk(table: str, pk_value: Any) -> Optional[dict[str, Any]]:
    pk_field = PK_FIELDS[table]
    engine = get_engine()
    sql = text(
        f"SELECT * FROM {quote_table(table)} WHERE {pk_field} = :pk LIMIT 1"
    )
    with engine.connect() as conn:
        row = conn.execute(sql, {"pk": pk_value}).mappings().first()
    return normalize_row(dict(row)) if row else None


def count_where(table: str, field: str, value: Any) -> int:
    engine = get_engine()
    sql = text(f"SELECT COUNT(*) AS n FROM {quote_table(table)} WHERE {field} = :v")
    with engine.connect() as conn:
        n = conn.execute(sql, {"v": value}).scalar()
    return int(n or 0)


def next_id(table: str) -> int:
    pk_field = PK_FIELDS[table]
    engine = get_engine()
    sql = text(
        f"SELECT COALESCE(MAX({pk_field}), 0) + 1 AS next_id FROM {quote_table(table)}"
    )
    with engine.connect() as conn:
        val = conn.execute(sql).scalar()
    return int(val)


def upsert(table: str, record: dict[str, Any]) -> dict[str, Any]:
    row = pick_columns(table, record)
    pk_field = PK_FIELDS[table]
    pk_value = row[pk_field]
    existing = find_by_pk(table, pk_value)
    engine = get_engine()
    if existing:
        sets = ", ".join(f"{k} = :{k}" for k in row if k != pk_field)
        sql = text(
            f"UPDATE {quote_table(table)} SET {sets} WHERE {pk_field} = :{pk_field}"
        )
    else:
        cols = ", ".join(row.keys())
        params = ", ".join(f":{k}" for k in row.keys())
        sql = text(
            f"INSERT INTO {quote_table(table)} ({cols}) VALUES ({params})"
        )
    with engine.begin() as conn:
        conn.execute(sql, row)
    saved = find_by_pk(table, pk_value)
    return saved if saved is not None else normalize_row(row)


def delete_row(table: str, pk_value: Any) -> bool:
    pk_field = PK_FIELDS[table]
    engine = get_engine()
    sql = text(f"DELETE FROM {quote_table(table)} WHERE {pk_field} = :pk")
    with engine.begin() as conn:
        result = conn.execute(sql, {"pk": pk_value})
    return result.rowcount > 0


def filter_items(
    parent_table: str, parent_id_field: str, parent_id: Any
) -> list[dict[str, Any]]:
    engine = get_engine()
    sql = text(
        f"SELECT * FROM {quote_table(parent_table)} "
        f"WHERE {parent_id_field} = :pid"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql, {"pid": parent_id}).mappings().all()
    return [normalize_row(dict(r)) for r in rows]


def replace_items(
    item_table: str,
    parent_id_field: str,
    parent_id: Any,
    items: list[dict[str, Any]],
) -> None:
    engine = get_engine()
    delete_sql = text(
        f"DELETE FROM {quote_table(item_table)} WHERE {parent_id_field} = :pid"
    )
    with engine.begin() as conn:
        conn.execute(delete_sql, {"pid": parent_id})
        for item in items:
            row = pick_columns(item_table, {**item, parent_id_field: parent_id})
            row[parent_id_field] = parent_id
            cols = ", ".join(row.keys())
            params = ", ".join(f":{k}" for k in row.keys())
            insert_sql = text(
                f"INSERT INTO {quote_table(item_table)} ({cols}) VALUES ({params})"
            )
            conn.execute(insert_sql, row)


def delete_machine_contract_hst_by_serial(serial_number: int) -> None:
    engine = get_engine()
    sql = text(
        f"DELETE FROM {quote_table('machine_contract_hst')} "
        "WHERE serial_number = :sn"
    )
    with engine.begin() as conn:
        conn.execute(sql, {"sn": serial_number})
