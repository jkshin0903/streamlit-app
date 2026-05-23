from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import vendor_select
from lib.components.line_items import clear_lines, init_lines, render_line_items
from lib.constants import PURCHASE_ORDER_STATUSES
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

begin_page("purchase_order", "📄")

LINES_KEY = "po_lines"
edit_key = "edit_purchase_order_id"

pos = repository.list_purchase_orders()
tab_list, tab_form = st.tabs([TAB_LIST, TAB_FORM])

with tab_list:
    if pos:
        st.dataframe(
            pd.DataFrame(pos).rename(columns={c: col(c) for c in pos[0].keys()}),
            use_container_width=True,
            hide_index=True,
        )
        ids = [p["purchase_order_id"] for p in pos]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox(col("purchase_order_id"), labels, index=idx)
        if st.button(BTN_OPEN):
            st.session_state[edit_key] = int(pick)
            rec = repository.get_purchase_order(int(pick))
            init_lines(LINES_KEY, rec["items"] if rec else None)
            st.experimental_rerun()
    else:
        st.info(f"No {col('purchase_order')} records.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_purchase_order(edit_id) if edit_id else None

    if st.button(BTN_NEW):
        st.session_state.pop(edit_key, None)
        clear_lines(LINES_KEY)
        init_lines(LINES_KEY, None)
        st.experimental_rerun()

    if record:
        init_lines(LINES_KEY, record.get("items"))

    with st.form("po_header"):
        if record:
            st.number_input(
                col("purchase_order_id"),
                value=record["purchase_order_id"],
                disabled=True,
            )
        vendor_id = vendor_select(
            key="po_vendor",
            default_id=(record or {}).get("vendor_id"),
        )
        po_date = st.date_input(
            req("purchase_order_date"),
            value=parse_date((record or {}).get("purchase_order_date")) or date.today(),
        )
        statuses = PURCHASE_ORDER_STATUSES
        psidx = (
            statuses.index(record["purchase_order_status"])
            if record and record["purchase_order_status"] in statuses
            else 0
        )
        po_status = st.selectbox(req("purchase_order_status"), statuses, index=psidx)
        st.form_submit_button(BTN_CONFIRM)

    lines = render_line_items(LINES_KEY, show_unit_price=True, form_key_prefix="po")

    if st.button(BTN_SAVE, type="primary"):
        header = {
            "purchase_order_id": edit_id,
            "vendor_id": vendor_id,
            "purchase_order_date": po_date,
            "purchase_order_status": po_status,
        }
        result = handle_repo_error(
            lambda: repository.save_purchase_order(header, lines)
        )
        if result:
            st.session_state[edit_key] = result["purchase_order_id"]
            st.success(MSG_SAVED)
            st.experimental_rerun()

    if edit_id and st.button(BTN_DELETE):
        if handle_repo_error(lambda: repository.delete_purchase_order(edit_id)):
            st.session_state.pop(edit_key, None)
            clear_lines(LINES_KEY)
            st.success(MSG_DELETED)
            st.experimental_rerun()
