from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.report_actions import render_report_actions
from lib.constants import REPORT_MACHINE_STATUSES, REPORT_MACHINE_TYPES
from lib.labels import ALL_LOCATIONS, BTN_SEARCH, col
from lib.page_utils import begin_page
from lib.repository import reports

begin_page("installation_report", "📊")
st.caption("SCR-RPT-01 · Installed equipment by location")

locations = repository.list_locations()
loc_options = {ALL_LOCATIONS: None}
for loc in locations:
    loc_options[f"{loc['location_name']} ({loc['location_id']})"] = loc["location_id"]

with st.form("rpt01_filters"):
    c1, c2, c3 = st.columns(3)
    with c1:
        chosen_locs = st.multiselect(
            col("location_id"),
            list(loc_options.keys()),
            default=[ALL_LOCATIONS],
        )
    with c2:
        chosen_types = st.multiselect(
            "Machine Type",
            REPORT_MACHINE_TYPES,
            default=["All"],
        )
    with c3:
        statuses = st.multiselect(
            "Status",
            REPORT_MACHINE_STATUSES,
            default=["Active"],
        )
    c4, c5 = st.columns(2)
    with c4:
        install_from = st.date_input("Installation from", value=None)
    with c5:
        install_to = st.date_input("Installation to", value=None)
    search = st.form_submit_button(BTN_SEARCH, type="primary")

if search or "rpt01_rows" not in st.session_state:
    loc_ids = None
    if ALL_LOCATIONS not in chosen_locs:
        loc_ids = [loc_options[k] for k in chosen_locs if loc_options[k] is not None]
    rows = reports.build_installation_report(
        location_ids=loc_ids,
        machine_types=chosen_types,
        report_statuses=statuses,
        install_from=install_from if install_from else None,
        install_to=install_to if install_to else None,
    )
    st.session_state["rpt01_rows"] = rows

rows = st.session_state.get("rpt01_rows", [])
if not rows:
    st.info("No data for the selected filters.")
else:
    df = pd.DataFrame(rows)
    display = df.rename(
        columns={
            "business_location": "Business Location",
            "location_address": "Location Address",
            "machine_type": "Machine Type",
            "machine_name": "Machine Name",
            "serial_number": col("serial_number"),
            "manufacturer": "Manufacturer",
            "purchase_date": "Purchase Date",
            "purchase_price": "Purchase Price",
            "installation_date": "Installation Date",
            "current_status": "Current Status",
            "repair_count": "Repair Count",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)

    subtotals = df.groupby("business_location")["purchase_price"].sum()
    st.subheader("Location Sub-totals")
    for loc_name, amt in subtotals.items():
        st.write(f"**{loc_name}**: ${amt:,.2f}")
    st.metric("Grand Total (asset value)", f"${df['purchase_price'].sum():,.2f}")

    render_report_actions(display, file_prefix="installation_report")

    st.divider()
    st.subheader("Create move order")
    sn_pick = st.selectbox(
        "Machine for move order",
        options=df["serial_number"].tolist(),
        format_func=lambda s: f"{s} — {df[df['serial_number']==s]['machine_name'].iloc[0]}",
    )
    if st.button("Open Move Order with selected machine"):
        st.session_state["prefill_move_serial"] = int(sn_pick)
        st.switch_page("pages/04_Order.py")
