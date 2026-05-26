"""Foreign-key selectbox helpers."""

from __future__ import annotations

from typing import Any, Callable, Optional

import streamlit as st

from lib import repository
from lib.labels import NONE_OPTION, col, req


def fk_selectbox(
    label: str,
    rows: list[dict[str, Any]],
    id_field: str,
    label_fn: Callable[[Any], str],
    *,
    key: str,
    default_id: Optional[Any] = None,
    allow_none: bool = False,
    none_label: str = NONE_OPTION,
    required: bool = False,
) -> Optional[Any]:
    display = f"{label} *" if required and not label.endswith("*") else label
    if allow_none:
        labels = [none_label]
        mapping: dict[str, Optional[Any]] = {none_label: None}
        for row in rows:
            pk = row[id_field]
            text = label_fn(pk)
            labels.append(text)
            mapping[text] = pk
    else:
        labels, mapping = repository.id_options(rows, id_field, label_fn)
        if not labels:
            st.warning(f"{display}: no options available.")
            return None

    default_label = None
    if default_id is not None:
        for lbl, pk in mapping.items():
            if pk == default_id:
                default_label = lbl
                break
    idx = labels.index(default_label) if default_label in labels else 0
    chosen = st.selectbox(display, labels, index=idx, key=key)
    return mapping[chosen]


def location_select(
    *,
    key: str,
    default_id: Optional[int] = None,
    allow_none: bool = False,
    required: bool = False,
    field: str = "location_id",
) -> Optional[int]:
    return fk_selectbox(
        req(field) if required else col(field),
        repository.list_locations(),
        "location_id",
        repository.location_label,
        key=key,
        default_id=default_id,
        allow_none=allow_none,
        required=False,
    )


def vendor_select(
    *,
    key: str,
    default_id: Optional[int] = None,
    required: bool = True,
) -> Optional[int]:
    return fk_selectbox(
        req("vendor_id") if required else col("vendor_id"),
        repository.list_vendors(),
        "vendor_id",
        repository.vendor_label,
        key=key,
        default_id=default_id,
        required=False,
    )


def product_select(
    *,
    key: str,
    default_id: Optional[int] = None,
) -> Optional[int]:
    return fk_selectbox(
        col("product_no"),
        repository.list_products(),
        "product_no",
        repository.product_label,
        key=key,
        default_id=default_id,
    )


def technician_select(
    *,
    key: str,
    default_id: Optional[int] = None,
    allow_none: bool = True,
) -> Optional[int]:
    return fk_selectbox(
        col("technician_id"),
        repository.list_technicians(),
        "technician_id",
        repository.technician_label,
        key=key,
        default_id=default_id,
        allow_none=allow_none,
    )
