from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import location_select
from lib.components.line_items import clear_lines, init_lines, render_line_items
from lib.constants import REQUEST_STATUSES
from lib.labels import (
    BTN_CONFIRM,
    BTN_DELETE,
    BTN_NEW,
    BTN_OPEN,
    BTN_SAVE,
    MSG_DELETED,
    MSG_SAVED,
    TAB_FORM,
    TAB_LIST,
    col,
    req,
)
from lib.models import parse_date
from lib.page_utils import begin_page, handle_repo_error

begin_page("purchase_request", "🛒")

LINES_KEY = "pr_lines"
edit_key = "edit_purchase_request_id"

prs = repository.list_purchase_requests()
tab_list, tab_form = st.tabs([TAB_LIST, TAB_FORM])

with tab_list:
    if prs:
        st.dataframe(
            pd.DataFrame(prs).rename(columns={c: col(c) for c in prs[0].keys()}),
            use_container_width=True,
            hide_index=True,
        )
        ids = [p["purchase_request_id"] for p in prs]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox(col("purchase_request_id"), labels, index=idx)
        if st.button(BTN_OPEN):
            st.session_state[edit_key] = int(pick)
            rec = repository.get_purchase_request(int(pick))
            init_lines(LINES_KEY, rec["items"] if rec else None)
            st.rerun()
    else:
        st.info(f"No {col('purchase_request')} records.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_purchase_request(edit_id) if edit_id else None

    if st.button(BTN_NEW):
        st.session_state.pop(edit_key, None)
        clear_lines(LINES_KEY)
        init_lines(LINES_KEY, None)
        st.rerun()

    if record:
        init_lines(LINES_KEY, record.get("items"))

    with st.form("pr_header"):
        if record:
            st.number_input(
                col("purchase_request_id"),
                value=record["purchase_request_id"],
                disabled=True,
            )
        loc_id = location_select(
            key="pr_loc",
            default_id=(record or {}).get("location_id"),
            required=True,
        )
        req_date = st.date_input(
            req("request_date"),
            value=parse_date((record or {}).get("request_date")) or date.today(),
        )
        statuses = REQUEST_STATUSES
        rsidx = (
            statuses.index(record["request_status"])
            if record and record["request_status"] in statuses
            else 0
        )
        req_status = st.selectbox(req("request_status"), statuses, index=rsidx)
        st.form_submit_button(BTN_CONFIRM)

    lines = render_line_items(LINES_KEY, show_unit_price=False, form_key_prefix="pr")

    if st.button(BTN_SAVE, type="primary"):
        header = {
            "purchase_request_id": edit_id,
            "location_id": loc_id,
            "request_date": req_date,
            "request_status": req_status,
        }
        result = handle_repo_error(
            lambda: repository.save_purchase_request(header, lines)
        )
        if result:
            st.session_state[edit_key] = result["purchase_request_id"]
            st.success(MSG_SAVED)
            st.rerun()

    if edit_id and st.button(BTN_DELETE):
        if handle_repo_error(lambda: repository.delete_purchase_request(edit_id)):
            st.session_state.pop(edit_key, None)
            clear_lines(LINES_KEY)
            st.success(MSG_DELETED)
            st.rerun()
