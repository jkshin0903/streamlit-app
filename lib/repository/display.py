"""FK labels and selectbox option helpers."""

from __future__ import annotations

from typing import Any, Callable, Optional

from . import business_location, product, technician, vendor


def location_label(location_id: Optional[int]) -> str:
    if location_id is None:
        return "(none)"
    loc = business_location.get_location(location_id)
    return f"{loc['location_name']} ({location_id})" if loc else f"#{location_id}"


def vendor_label(vendor_id: int) -> str:
    v = vendor.get_vendor(vendor_id)
    return f"{v['vendor_name']} ({vendor_id})" if v else f"#{vendor_id}"


def product_label(product_no: int) -> str:
    p = product.get_product(product_no)
    return f"{p['product_name']} ({product_no})" if p else f"#{product_no}"


def technician_label(technician_id: int) -> str:
    t = technician.get_technician(technician_id)
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
    rows = business_location.list_locations()
    labels = ["(none)"]
    mapping: dict[str, Optional[int]] = {"(none)": None}
    for row in rows:
        lid = row["location_id"]
        label = f"{row['location_name']} ({lid})"
        labels.append(label)
        mapping[label] = lid
    return labels, mapping
