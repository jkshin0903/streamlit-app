from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.auth_context import current_user_name
from lib.components.fk_select import vendor_select
from lib.components.line_items import clear_lines, init_lines, render_line_items
from lib.constants import PURCHASE_ORDER_STATUSES
from lib.labels import (
    BTN_CLEAR,
    BTN_DELETE,
    BTN_NEW,
    BTN_OPEN,
    BTN_PRINT_FAX,
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
from lib.po_document import build_po_html, format_po_number

begin_page("purchase_order", "📄")
st.caption("SCR-IN-01 · Purchase Order entry")

LINES_KEY = "po_lines"
edit_key = "edit_purchase_order_id"
CLEAR_CONFIRM_KEY = "po_clear_confirm"

pos = repository.list_purchase_orders()
tab_list, tab_form = st.tabs([TAB_LIST, TAB_FORM])

with tab_list:
    if pos:
        display = []
        for p in pos:
            row = dict(p)
            row["purchase_order_id"] = format_po_number(p["purchase_order_id"])
            display.append(row)
        st.dataframe(
            pd.DataFrame(display).rename(columns={c: col(c) for c in display[0].keys()}),
            width="stretch",
            hide_index=True,
        )
        ids = [p["purchase_order_id"] for p in pos]
        labels = [format_po_number(i) for i in ids]
        cur = st.session_state.get(edit_key)
        cur_label = format_po_number(cur) if cur else None
        idx = labels.index(cur_label) if cur_label in labels else 0
        pick = st.selectbox(col("purchase_order_id"), labels, index=idx)
        if st.button(BTN_OPEN):
            po_id = int(pick)
            st.session_state[edit_key] = po_id
            rec = repository.get_purchase_order(po_id)
            init_lines(LINES_KEY, rec["items"] if rec else None)
            st.rerun()
    else:
        st.info(f"No {col('purchase_order')} records.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_purchase_order(edit_id) if edit_id else None
    next_po = format_po_number(max([p["purchase_order_id"] for p in pos], default=0) + 1)

    if st.button(BTN_NEW):
        st.session_state.pop(edit_key, None)
        clear_lines(LINES_KEY)
        init_lines(LINES_KEY, None)
        st.rerun()

    if record:
        init_lines(LINES_KEY, record.get("items"))

    h1, h2, h3 = st.columns(3)
    with h1:
        st.text_input("PO Number", value=format_po_number(edit_id) if edit_id else next_po, disabled=True)
    with h2:
        po_date = st.date_input(
            req("purchase_order_date"),
            value=parse_date((record or {}).get("purchase_order_date")) or date.today(),
            max_value=date.today(),
        )
    with h3:
        st.text_input("Buyer", value=current_user_name(), disabled=True)

    vendor_id = vendor_select(key="po_vendor", default_id=(record or {}).get("vendor_id"))
    vend = repository.get_vendor(vendor_id) if vendor_id else None
    if vend:
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            vendor_address = st.text_input(
                col("address"), value=vend.get("address") or "", key="po_v_addr"
            )
        with vc2:
            vendor_phone = st.text_input(
                col("phone"), value=vend.get("phone") or "", key="po_v_phone"
            )
        with vc3:
            vendor_fax = st.text_input(
                col("fax"), value=vend.get("fax") or "", key="po_v_fax"
            )
    else:
        vendor_address = vendor_phone = vendor_fax = ""

    statuses = PURCHASE_ORDER_STATUSES
    psidx = (
        statuses.index(record["purchase_order_status"])
        if record and record["purchase_order_status"] in statuses
        else 0
    )
    po_status = st.selectbox(req("purchase_order_status"), statuses, index=psidx)

    lines = render_line_items(LINES_KEY, show_unit_price=True, form_key_prefix="po")

    product_nos = [ln["product_no"] for ln in lines]
    if len(product_nos) != len(set(product_nos)):
        st.warning("Duplicate product numbers on this purchase order.")

    btn_save, btn_fax, btn_clear = st.columns(3)
    if btn_save.button(BTN_SAVE, type="primary"):
        if not vendor_id:
            st.error(f"{col('vendor_id')} is required.")
        elif not lines:
            st.error("At least one line item is required.")
        else:
            header = {
                "purchase_order_id": edit_id,
                "vendor_id": vendor_id,
                "purchase_order_date": po_date,
                "purchase_order_status": po_status if edit_id else "Pending",
            }
            result = handle_repo_error(
                lambda: repository.save_purchase_order(header, lines)
            )
            if result:
                st.session_state[edit_key] = result["purchase_order_id"]
                st.success(MSG_SAVED)
                st.rerun()

    if btn_fax.button(BTN_PRINT_FAX):
        if not edit_id or not record:
            st.warning("Save the purchase order before printing or sending fax.")
        elif not (vend and vend.get("fax")):
            st.error("Vendor fax number is not registered. Cannot send fax.")
        else:
            html = build_po_html(record, record.get("items", []))
            st.download_button(
                "Download PO (HTML for print)",
                data=html,
                file_name=f"PO_{format_po_number(edit_id)}.html",
                mime="text/html",
            )
            st.success(f"Fax sent to {vend.get('fax')} (simulated).")

    if btn_clear.button(BTN_CLEAR):
        if not st.session_state.get(CLEAR_CONFIRM_KEY):
            st.session_state[CLEAR_CONFIRM_KEY] = True
            st.warning("Clear all fields? Click Clear again to confirm.")
        else:
            st.session_state.pop(edit_key, None)
            st.session_state.pop(CLEAR_CONFIRM_KEY, None)
            clear_lines(LINES_KEY)
            init_lines(LINES_KEY, None)
            st.rerun()

    if edit_id and st.button(BTN_DELETE):
        if handle_repo_error(lambda: repository.delete_purchase_order(edit_id)):
            st.session_state.pop(edit_key, None)
            clear_lines(LINES_KEY)
            st.success(MSG_DELETED)
            st.rerun()
