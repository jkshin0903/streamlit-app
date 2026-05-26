from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.line_items import clear_lines, init_lines, render_line_items
from lib.constants import INVOICE_STATUSES
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

begin_page("invoice", "🧾")

LINES_KEY = "inv_lines"
edit_key = "edit_invoice_number"

invoices = repository.list_invoices()
tab_list, tab_form = st.tabs([TAB_LIST, TAB_FORM])

with tab_list:
    if invoices:
        st.dataframe(
            pd.DataFrame(invoices).rename(columns={c: col(c) for c in invoices[0].keys()}),
            use_container_width=True,
            hide_index=True,
        )
        ids = [i["invoice_number"] for i in invoices]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox(col("invoice_number"), labels, index=idx)
        if st.button(BTN_OPEN):
            st.session_state[edit_key] = int(pick)
            rec = repository.get_invoice(int(pick))
            init_lines(LINES_KEY, rec["items"] if rec else None)
            st.rerun()
    else:
        st.info(f"No {col('invoice')} records.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_invoice(edit_id) if edit_id else None

    if st.button(BTN_NEW):
        st.session_state.pop(edit_key, None)
        clear_lines(LINES_KEY)
        init_lines(LINES_KEY, None)
        st.rerun()

    if record:
        init_lines(LINES_KEY, record.get("items"))

    pos = repository.list_purchase_orders()
    po_labels, po_map = repository.id_options(
        pos, "purchase_order_id", lambda x: f"{col('purchase_order_id')} {x}"
    )

    with st.form("inv_header"):
        if record:
            st.number_input(
                col("invoice_number"),
                value=record["invoice_number"],
                disabled=True,
            )
        if po_labels:
            default_po = (record or {}).get("purchase_order_id")
            default_lbl = next(
                (l for l, p in po_map.items() if p == default_po), po_labels[0]
            )
            po_idx = po_labels.index(default_lbl) if default_lbl in po_labels else 0
            po_lbl = st.selectbox(
                req("purchase_order_id"), po_labels, index=po_idx, key="inv_po_sel"
            )
            po_id = po_map[po_lbl]
        else:
            st.warning(f"Create a {col('purchase_order')} first.")
            po_id = None

        vendor_id = repository.get_po_vendor_id(po_id) if po_id else None
        if vendor_id:
            st.text_input(
                f"{col('vendor_id')} (from {col('purchase_order')})",
                value=repository.vendor_label(vendor_id),
                disabled=True,
            )
        inv_date = st.date_input(
            req("invoice_date"),
            value=parse_date((record or {}).get("invoice_date")) or date.today(),
        )
        statuses = INVOICE_STATUSES
        isidx = (
            statuses.index(record["invoice_status"])
            if record and record["invoice_status"] in statuses
            else 0
        )
        inv_status = st.selectbox(req("invoice_status"), statuses, index=isidx)
        terms = st.text_area(req("terms"), value=(record or {}).get("terms") or "")
        st.form_submit_button(BTN_CONFIRM)

    lines = render_line_items(LINES_KEY, show_unit_price=True, form_key_prefix="inv")

    if st.button(BTN_SAVE, type="primary"):
        if po_id is None or vendor_id is None:
            st.error(f"Check {col('purchase_order_id')} and {col('vendor_id')}.")
        else:
            header = {
                "invoice_number": edit_id,
                "purchase_order_id": po_id,
                "vendor_id": vendor_id,
                "invoice_date": inv_date,
                "invoice_status": inv_status,
                "terms": terms,
            }
            result = handle_repo_error(
                lambda: repository.save_invoice(header, lines)
            )
            if result:
                st.session_state[edit_key] = result["invoice_number"]
                st.success(MSG_SAVED)
                st.rerun()

    if edit_id and st.button(BTN_DELETE):
        if handle_repo_error(lambda: repository.delete_invoice(edit_id)):
            st.session_state.pop(edit_key, None)
            clear_lines(LINES_KEY)
            st.success(MSG_DELETED)
            st.rerun()
