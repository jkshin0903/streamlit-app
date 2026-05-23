from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import fk_selectbox
from lib.components.line_items import clear_lines, init_lines, render_line_items
from lib.constants import INVOICE_STATUSES
from lib.models import parse_date
from lib.page_utils import handle_repo_error, setup_page

setup_page("송장 관리", "🧾")

st.title("송장 관리")
repository.init_if_needed()

LINES_KEY = "inv_lines"
edit_key = "edit_invoice_number"

invoices = repository.list_invoices()
tab_list, tab_form = st.tabs(["목록 조회", "등록 / 수정"])

with tab_list:
    if invoices:
        st.dataframe(pd.DataFrame(invoices), use_container_width=True, hide_index=True)
        ids = [i["invoice_number"] for i in invoices]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox("송장 선택", labels, index=idx)
        if st.button("열기"):
            st.session_state[edit_key] = int(pick)
            rec = repository.get_invoice(int(pick))
            init_lines(LINES_KEY, rec["items"] if rec else None)
            st.experimental_rerun()
    else:
        st.info("송장이 없습니다.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_invoice(edit_id) if edit_id else None

    if st.button("신규"):
        st.session_state.pop(edit_key, None)
        clear_lines(LINES_KEY)
        init_lines(LINES_KEY, None)
        st.experimental_rerun()

    if record:
        init_lines(LINES_KEY, record.get("items"))

    pos = repository.list_purchase_orders()
    po_labels, po_map = repository.id_options(
        pos, "purchase_order_id", lambda x: f"발주 #{x}"
    )

    with st.form("inv_header"):
        if record:
            st.number_input("송장 번호", value=record["invoice_number"], disabled=True)
        if po_labels:
            default_po = (record or {}).get("purchase_order_id")
            default_lbl = next(
                (l for l, p in po_map.items() if p == default_po), po_labels[0]
            )
            po_idx = po_labels.index(default_lbl) if default_lbl in po_labels else 0
            po_lbl = st.selectbox("연결 발주 *", po_labels, index=po_idx, key="inv_po_sel")
            po_id = po_map[po_lbl]
        else:
            st.warning("구매 발주를 먼저 등록하세요.")
            po_id = None

        vendor_id = repository.get_po_vendor_id(po_id) if po_id else None
        if vendor_id:
            st.text_input(
                "공급업체 (발주 연동)",
                value=repository.vendor_label(vendor_id),
                disabled=True,
            )
        inv_date = st.date_input(
            "송장일 *",
            value=parse_date((record or {}).get("invoice_date")) or date.today(),
        )
        statuses = INVOICE_STATUSES
        isidx = (
            statuses.index(record["invoice_status"])
            if record and record["invoice_status"] in statuses
            else 0
        )
        inv_status = st.selectbox("송장 상태 *", statuses, index=isidx)
        terms = st.text_area(
            "결제 조건 *", value=(record or {}).get("terms") or ""
        )
        st.form_submit_button("확인")

    lines = render_line_items(LINES_KEY, show_unit_price=True, form_key_prefix="inv")

    if st.button("저장", type="primary"):
        if po_id is None or vendor_id is None:
            st.error("발주와 공급업체를 확인하세요.")
        else:
            header = {
                "invoice_number": edit_id,
                "purchase_order_id": po_id,
                "vendor_id": vendor_id,
                "invoice_date": inv_date,
                "invoice_status": inv_status,
                "terms": terms,
            }

            def _save():
                return repository.save_invoice(header, lines)

            result = handle_repo_error(_save)
            if result:
                st.session_state[edit_key] = result["invoice_number"]
                st.success("저장되었습니다.")
                st.experimental_rerun()

    if edit_id and st.button("삭제"):
        if handle_repo_error(lambda: repository.delete_invoice(edit_id)):
            st.session_state.pop(edit_key, None)
            clear_lines(LINES_KEY)
            st.success("삭제되었습니다.")
            st.experimental_rerun()
