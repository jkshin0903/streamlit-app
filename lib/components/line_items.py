"""Dynamic line items for PR / PO / Invoice."""

from __future__ import annotations

from typing import Any

import streamlit as st

from lib import repository
from lib.labels import BTN_ADD_LINE, BTN_REMOVE, col


def init_lines(state_key: str, items: list[dict[str, Any]] | None = None) -> None:
    if state_key not in st.session_state:
        if items:
            st.session_state[state_key] = [
                {
                    "product_no": i["product_no"],
                    "quantity": int(i["quantity"]),
                    "unit_price": float(i.get("unit_price", 0)),
                }
                for i in items
            ]
        else:
            st.session_state[state_key] = [{"product_no": None, "quantity": 1, "unit_price": 0.0}]


def render_line_items(
    state_key: str,
    *,
    show_unit_price: bool = False,
    form_key_prefix: str = "line",
) -> list[dict[str, Any]]:
    init_lines(state_key)
    lines: list[dict[str, Any]] = st.session_state[state_key]

    st.markdown(f"**{col('product_no')} / line items**")
    if st.button(BTN_ADD_LINE, key=f"{form_key_prefix}_add"):
        lines.append({"product_no": None, "quantity": 1, "unit_price": 0.0})
        st.session_state[state_key] = lines
        st.experimental_rerun()

    products = repository.list_products()
    product_labels, product_map = repository.id_options(
        products, "product_no", repository.product_label
    )
    if not product_labels:
        st.warning(f"Register {col('product_no')} master data first.")
        return []

    to_remove: list[int] = []
    total = 0.0

    for idx, line in enumerate(lines):
        cols = st.columns([3, 1, 1, 1] if show_unit_price else [4, 1, 1])
        with cols[0]:
            default_pn = line.get("product_no")
            default_lbl = next(
                (l for l, p in product_map.items() if p == default_pn),
                product_labels[0],
            )
            p_idx = product_labels.index(default_lbl) if default_lbl in product_labels else 0
            chosen = st.selectbox(
                col("product_no"),
                product_labels,
                index=p_idx,
                key=f"{form_key_prefix}_prod_{idx}",
                label_visibility="collapsed",
            )
            line["product_no"] = product_map[chosen]
        with cols[1]:
            line["quantity"] = st.number_input(
                col("quantity"),
                min_value=1,
                value=int(line.get("quantity", 1)),
                key=f"{form_key_prefix}_qty_{idx}",
                label_visibility="collapsed",
            )
        if show_unit_price:
            with cols[2]:
                line["unit_price"] = st.number_input(
                    col("unit_price"),
                    min_value=0.0,
                    value=float(line.get("unit_price", 0)),
                    format="%.0f",
                    key=f"{form_key_prefix}_price_{idx}",
                    label_visibility="collapsed",
                )
            subtotal = line["quantity"] * line["unit_price"]
            total += subtotal
            with cols[3]:
                st.caption(f"Subtotal ₩{subtotal:,.0f}")
                if st.button(BTN_REMOVE, key=f"{form_key_prefix}_del_{idx}"):
                    to_remove.append(idx)
        else:
            with cols[2]:
                if st.button(BTN_REMOVE, key=f"{form_key_prefix}_del_{idx}"):
                    to_remove.append(idx)

    if to_remove:
        for i in sorted(to_remove, reverse=True):
            del lines[i]
        if not lines:
            lines.append({"product_no": None, "quantity": 1, "unit_price": 0.0})
        st.session_state[state_key] = lines
        st.experimental_rerun()

    if show_unit_price:
        st.metric("Total Amount", f"₩{total:,.0f}")

    return [dict(l) for l in lines if l.get("product_no") is not None]


def clear_lines(state_key: str) -> None:
    st.session_state.pop(state_key, None)
