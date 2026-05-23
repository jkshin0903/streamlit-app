from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import vendor_select
from lib.components.line_items import clear_lines, init_lines, render_line_items
from lib.constants import PURCHASE_ORDER_STATUSES
from lib.models import parse_date
from lib.page_utils import handle_repo_error, setup_page

setup_page("구매 발주", "📄")

st.title("구매 발주")
repository.init_if_needed()

LINES_KEY = "po_lines"
edit_key = "edit_purchase_order_id"

pos = repository.list_purchase_orders()
tab_list, tab_form = st.tabs(["목록 조회", "등록 / 수정"])

with tab_list:
    if pos:
        st.dataframe(pd.DataFrame(pos), use_container_width=True, hide_index=True)
        ids = [p["purchase_order_id"] for p in pos]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox("발주 선택", labels, index=idx)
        if st.button("열기"):
            st.session_state[edit_key] = int(pick)
            rec = repository.get_purchase_order(int(pick))
            init_lines(LINES_KEY, rec["items"] if rec else None)
            st.experimental_rerun()
    else:
        st.info("구매 발주가 없습니다.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_purchase_order(edit_id) if edit_id else None

    if st.button("신규"):
        st.session_state.pop(edit_key, None)
        clear_lines(LINES_KEY)
        init_lines(LINES_KEY, None)
        st.experimental_rerun()

    if record:
        init_lines(LINES_KEY, record.get("items"))

    with st.form("po_header"):
        if record:
            st.number_input("발주 ID", value=record["purchase_order_id"], disabled=True)
        vendor_id = vendor_select(
            "공급업체 *",
            key="po_vendor",
            default_id=(record or {}).get("vendor_id"),
        )
        po_date = st.date_input(
            "발주일 *",
            value=parse_date((record or {}).get("purchase_order_date")) or date.today(),
        )
        statuses = PURCHASE_ORDER_STATUSES
        psidx = (
            statuses.index(record["purchase_order_status"])
            if record and record["purchase_order_status"] in statuses
            else 0
        )
        po_status = st.selectbox("발주 상태 *", statuses, index=psidx)
        st.form_submit_button("확인")

    lines = render_line_items(LINES_KEY, show_unit_price=True, form_key_prefix="po")

    if st.button("저장", type="primary"):
        header = {
            "purchase_order_id": edit_id,
            "vendor_id": vendor_id,
            "purchase_order_date": po_date,
            "purchase_order_status": po_status,
        }

        def _save():
            return repository.save_purchase_order(header, lines)

        result = handle_repo_error(_save)
        if result:
            st.session_state[edit_key] = result["purchase_order_id"]
            st.success("저장되었습니다.")
            st.experimental_rerun()

    if edit_id and st.button("삭제"):
        if handle_repo_error(lambda: repository.delete_purchase_order(edit_id)):
            st.session_state.pop(edit_key, None)
            clear_lines(LINES_KEY)
            st.success("삭제되었습니다.")
            st.experimental_rerun()
