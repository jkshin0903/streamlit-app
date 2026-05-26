"""Order screen header matching legacy form layout."""

from __future__ import annotations

import streamlit as st

from lib.constants import ORDER_STATUS_COLORS
from lib.labels import col


def render_order_header(order_id: int | None, order_status: str | None) -> None:
    if order_id is None:
        st.subheader(f"New {col('order_id')}")
    else:
        st.subheader(f"{col('order_id')} {order_id}")

    if order_status:
        color = ORDER_STATUS_COLORS.get(order_status, "gray")
        st.markdown(f"**{col('order_status')}:** :{color}[{order_status}]")

    action_cols = st.columns(4)
    with action_cols[0]:
        st.button("Create Invoice", disabled=True, help="Planned for phase 2")
    with action_cols[1]:
        st.button("Ship Order", disabled=True, help="Planned for phase 2")
    with action_cols[2]:
        st.button("Complete Order", disabled=True, help="Planned for phase 2")
    with action_cols[3]:
        st.button("Delete Order", disabled=True, help="Use Delete button below")
