from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import location_select
from lib.components.line_items import clear_lines, init_lines, render_line_items
from lib.constants import REQUEST_STATUSES
from lib.models import parse_date
from lib.page_utils import handle_repo_error, setup_page

setup_page("구매 요청", "🛒")

st.title("구매 요청")
repository.init_if_needed()

LINES_KEY = "pr_lines"
edit_key = "edit_purchase_request_id"

prs = repository.list_purchase_requests()
tab_list, tab_form = st.tabs(["목록 조회", "등록 / 수정"])

with tab_list:
    if prs:
        df = pd.DataFrame(prs)
        st.dataframe(df, use_container_width=True, hide_index=True)
        ids = [p["purchase_request_id"] for p in prs]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox("요청 선택", labels, index=idx)
        if st.button("열기"):
            st.session_state[edit_key] = int(pick)
            rec = repository.get_purchase_request(int(pick))
            init_lines(LINES_KEY, rec["items"] if rec else None)
            st.experimental_rerun()
    else:
        st.info("구매 요청이 없습니다.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_purchase_request(edit_id) if edit_id else None

    if st.button("신규"):
        st.session_state.pop(edit_key, None)
        clear_lines(LINES_KEY)
        init_lines(LINES_KEY, None)
        st.experimental_rerun()

    if record:
        init_lines(LINES_KEY, record.get("items"))

    with st.form("pr_header"):
        if record:
            st.number_input("요청 ID", value=record["purchase_request_id"], disabled=True)
        loc_id = location_select(
            "요청 사업장 *",
            key="pr_loc",
            default_id=(record or {}).get("location_id"),
        )
        req_date = st.date_input(
            "요청일 *",
            value=parse_date((record or {}).get("request_date")) or date.today(),
        )
        statuses = REQUEST_STATUSES
        rsidx = (
            statuses.index(record["request_status"])
            if record and record["request_status"] in statuses
            else 0
        )
        req_status = st.selectbox("요청 상태 *", statuses, index=rsidx)
        st.form_submit_button("확인")

    lines = render_line_items(LINES_KEY, show_unit_price=False, form_key_prefix="pr")

    if st.button("저장", type="primary"):
        header = {
            "purchase_request_id": edit_id,
            "location_id": loc_id,
            "request_date": req_date,
            "request_status": req_status,
        }

        def _save():
            return repository.save_purchase_request(header, lines)

        result = handle_repo_error(_save)
        if result:
            st.session_state[edit_key] = result["purchase_request_id"]
            st.success("저장되었습니다.")
            st.experimental_rerun()

    if edit_id and st.button("삭제"):
        if handle_repo_error(lambda: repository.delete_purchase_request(edit_id)):
            st.session_state.pop(edit_key, None)
            clear_lines(LINES_KEY)
            st.success("삭제되었습니다.")
            st.experimental_rerun()
