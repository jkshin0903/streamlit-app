from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.report_actions import render_report_actions
from lib.constants import PURCHASE_ORDER_STATUSES, REPORT_MACHINE_TYPES
from lib.labels import ALL_VENDORS, BTN_SEARCH, col
from lib.page_utils import begin_page
from lib.repository import reports

begin_page("annual_purchase_report", "📈")
st.caption("SCR-RPT-02 · Annual purchase and disposal listing")

vendors = repository.list_vendors()
vendor_opts = {ALL_VENDORS: None}
for v in vendors:
    vendor_opts[f"{v['vendor_name']} ({v['vendor_id']})"] = v["vendor_id"]

year_now = date.today().year
years = list(range(year_now, year_now - 6, -1))

with st.form("rpt02_filters"):
    c1, c2, c3 = st.columns(3)
    with c1:
        year = st.selectbox("Year", years, index=0)
    with c2:
        vendor_label = st.selectbox(col("vendor_id"), list(vendor_opts.keys()))
    with c3:
        machine_type = st.selectbox("Machine Type", REPORT_MACHINE_TYPES, index=0)
    c4, c5 = st.columns(2)
    with c4:
        date_from = st.date_input("Date from (optional)", value=None)
    with c5:
        date_to = st.date_input("Date to (optional)", value=None)
    status_options = ["All"] + PURCHASE_ORDER_STATUSES
    default_status_idx = (
        status_options.index("Received")
        if "Received" in status_options
        else 0
    )
    po_status = st.radio(
        col("purchase_order_status"),
        status_options,
        index=default_status_idx,
        horizontal=True,
    )
    search = st.form_submit_button(BTN_SEARCH, type="primary")

if search or "rpt02_rows" not in st.session_state:
    rows = reports.build_annual_purchase_report(
        year=year,
        date_from=date_from,
        date_to=date_to,
        vendor_id=vendor_opts[vendor_label],
        machine_type=machine_type,
        po_status=None if po_status == "All" else po_status,
    )
    st.session_state["rpt02_rows"] = rows

rows = st.session_state.get("rpt02_rows", [])
if not rows:
    st.info("No purchase data for the selected filters.")
else:
    df = pd.DataFrame(rows)
    display = df[
        [
            "po_number",
            "po_date",
            "vendor_name",
            "product_no",
            "product_name",
            "machine_type",
            "quantity",
            "unit_price",
            "total_price",
            "serial_numbers",
            "receive_date",
            "po_status",
            "disposal_date",
            "disposal_reason",
        ]
    ].rename(
        columns={
            "po_number": "PO Number",
            "po_date": "PO Date",
            "vendor_name": col("vendor_name"),
            "product_no": col("product_no"),
            "product_name": col("product_name"),
            "machine_type": "Machine Type",
            "quantity": col("quantity"),
            "unit_price": col("unit_price"),
            "total_price": "Total Price",
            "serial_numbers": "Serial Numbers",
            "receive_date": "Receive Date",
            "po_status": col("purchase_order_status"),
            "disposal_date": "Disposal Date",
            "disposal_reason": "Disposal Reason",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)

    for vname, grp in df.groupby("vendor_name"):
        st.write(
            f"**{vname}** — {len(grp)} line(s), "
            f"${grp['total_price'].sum():,.2f}"
        )
    st.metric("Grand Total", f"${df['total_price'].sum():,.2f}")
    disposed = df[df["disposal_reason"].astype(bool)]
    if not disposed.empty:
        st.metric("Disposal total (cancelled PO)", f"${disposed['total_price'].sum():,.2f}")

    render_report_actions(display, file_prefix=f"annual_purchase_{year}")

    po_pick = st.selectbox("Open PO detail", df["purchase_order_id"].unique())
    if st.button("Open Purchase Order"):
        st.session_state["edit_purchase_order_id"] = int(po_pick)
        st.switch_page("pages/06_Purchase_Order.py")
