from datetime import date, timedelta

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.report_actions import render_report_actions
from lib.constants import REPORT_MACHINE_TYPES
from lib.labels import ALL_LOCATIONS, BTN_SEARCH, col
from lib.page_utils import begin_page
from lib.repository import reports

begin_page("machine_performance_report", "📉")
st.caption("SCR-RPT-03 · Revenue, repair, and relocation recommendations")
st.caption(
    "Revenue and R&S share are estimated from asset value when meter data is unavailable."
)

locations = repository.list_locations()
loc_options = {ALL_LOCATIONS: None}
for loc in locations:
    loc_options[f"{loc['location_name']} ({loc['location_id']})"] = loc["location_id"]

periods = {
    "This month": 30,
    "Quarter": 90,
    "Half year": 182,
    "Year": 365,
    "Custom": 0,
}

with st.form("rpt03_filters"):
    period_label = st.selectbox("Analysis Period", list(periods.keys()))
    c1, c2 = st.columns(2)
    default_days = periods.get(period_label, 90) or 90
    with c1:
        period_from = st.date_input(
            "From",
            value=date.today() - timedelta(days=default_days),
        )
    with c2:
        period_to = st.date_input("To", value=date.today())
    chosen_locs = st.multiselect(
        col("location_id"), list(loc_options.keys()), default=[ALL_LOCATIONS]
    )
    machine_type = st.selectbox("Machine Type", REPORT_MACHINE_TYPES, index=0)
    threshold = st.number_input("Performance Threshold ($)", min_value=0.0, value=100.0)
    search = st.form_submit_button(BTN_SEARCH, type="primary")

if search or "rpt03_rows" not in st.session_state:
    loc_ids = None
    if ALL_LOCATIONS not in chosen_locs:
        loc_ids = [loc_options[k] for k in chosen_locs if loc_options[k] is not None]
    rows, warning = reports.build_performance_report(
        period_from=period_from,
        period_to=period_to,
        location_ids=loc_ids,
        machine_type=machine_type,
        threshold=threshold,
    )
    st.session_state["rpt03_rows"] = rows
    st.session_state["rpt03_warning"] = warning

if st.session_state.get("rpt03_warning"):
    st.warning(st.session_state["rpt03_warning"])

rows = st.session_state.get("rpt03_rows", [])
if not rows:
    st.info("No machines match the filters.")
else:
    df = pd.DataFrame(rows)
    low = df[df["highlight"]]
    if not low.empty:
        st.error(f"{len(low)} machine(s) below performance threshold.")

    display = df.drop(columns=["highlight"], errors="ignore").rename(
        columns={
            "business_location": "Business Location",
            "machine_name": "Machine Name",
            "machine_type": "Machine Type",
            "serial_number": col("serial_number"),
            "installation_date": "Installation Date",
            "total_revenue": "Total Revenue",
            "rs_revenue_share": "R&S Revenue Share",
            "revenue_per_day": "Revenue / Day",
            "repair_count": "Repair Count",
            "total_repair_cost": "Total Repair Cost",
            "location_history": "Location History",
            "performance_status": "Performance Status",
            "recommendation": "Recommendation",
        }
    )
    st.dataframe(display, width="stretch", hide_index=True)

    render_report_actions(display, file_prefix="machine_performance")

    relocate = df[df["recommendation"].isin(["Relocate", "Junk", "Replace"])]
    if not relocate.empty:
        st.subheader("Suggested actions")
        pick = st.selectbox(
            "Machine",
            relocate["serial_number"].tolist(),
            format_func=lambda s: (
                f"{s} — "
                f"{relocate.loc[relocate['serial_number'] == s, 'recommendation'].iloc[0]}"
            ),
        )
        rec = relocate.loc[
            relocate["serial_number"] == pick, "recommendation"
        ].iloc[0]
        if rec in ("Relocate", "Junk"):
            if st.button("Open Move Order"):
                st.session_state["prefill_move_serial"] = int(pick)
                st.switch_page("pages/04_Order.py")
        if rec == "Replace":
            if st.button("Open Purchase Order"):
                st.switch_page("pages/06_Purchase_Order.py")
