from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import fk_selectbox, location_select, technician_select
from lib.components.order_header import render_order_header
from lib.constants import ORDER_STATUSES, ORDER_TYPES
from lib.models import parse_date
from lib.page_utils import handle_repo_error, setup_page

setup_page("주문 관리", "📦")

st.title("주문 관리")
repository.init_if_needed()

edit_key = "edit_order_id"

orders = repository.list_orders()
col_list, col_detail = st.columns([1, 2])

with col_list:
    st.subheader("주문 목록")
    if orders:
        df = pd.DataFrame(orders)[
            ["order_id", "order_type", "order_status", "request_date", "serial_number"]
        ]
        st.dataframe(df, use_container_width=True, hide_index=True)
        ids = [o["order_id"] for o in orders]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox("주문 선택", labels, index=idx, key="order_pick")
        c1, c2 = st.columns(2)
        if c1.button("열기"):
            st.session_state[edit_key] = int(pick)
            st.session_state.pop("order_is_new", None)
            st.experimental_rerun()
        if c2.button("신규"):
            st.session_state[edit_key] = None
            st.session_state["order_is_new"] = True
            st.experimental_rerun()
    else:
        st.info("주문이 없습니다.")
        if st.button("신규 주문"):
            st.session_state[edit_key] = None
            st.session_state["order_is_new"] = True
            st.experimental_rerun()

with col_detail:
    is_new = st.session_state.get("order_is_new", False)
    edit_id = st.session_state.get(edit_key)
    record = None if is_new else (repository.get_order(edit_id) if edit_id else None)

    if not is_new and edit_id is None and orders:
        st.info("목록에서 주문을 선택하거나 신규를 누르세요.")
    else:
        render_order_header(
            None if is_new else edit_id,
            (record or {}).get("order_status"),
        )

        def _d(val):
            return parse_date(val) or date.today()

        c1, c2 = st.columns(2)
        with c1:
            customer_loc = location_select(
                "고객(사업장) *",
                key="ord_cust",
                default_id=(record or {}).get("location_id"),
            )
            request_d = st.date_input(
                "요청일 *", value=_d((record or {}).get("request_date"))
            )
        with c2:
            tech_id = technician_select(
                "담당 기술자",
                key="ord_tech",
                default_id=(record or {}).get("technician_id"),
            )
            comp = (record or {}).get("completion_date")
            completion_d = st.date_input(
                "완료일",
                value=parse_date(comp) if comp else None,
            )

        tab_order, tab_ship, tab_other = st.tabs(
            ["주문 정보", "운송 정보", "기타 정보"]
        )

        with tab_order:
            types = ORDER_TYPES
            tidx = (
                types.index(record["order_type"])
                if record and record["order_type"] in types
                else 0
            )
            order_type = st.selectbox("주문 유형 *", types, index=tidx)
            serial = fk_selectbox(
                "장비(시리얼) *",
                repository.list_machines(),
                "serial_number",
                lambda s: f"{repository.get_machine(s)['machine_name']} ({s})",
                key="ord_serial",
                default_id=(record or {}).get("serial_number"),
            )
            statuses = ORDER_STATUSES
            sidx = (
                statuses.index(record["order_status"])
                if record and record["order_status"] in statuses
                else 0
            )
            order_status = st.selectbox("주문 상태 *", statuses, index=sidx)

        with tab_ship:
            from_loc = location_select(
                "출발 사업장",
                key="ord_from",
                default_id=(record or {}).get("from_location_id"),
                allow_none=True,
            )
            to_loc = location_select(
                "도착 사업장 *",
                key="ord_to",
                default_id=(record or {}).get("to_location_id"),
            )
            rel_loc = location_select(
                "관련 사업장",
                key="ord_rel",
                default_id=(record or {}).get("location_id"),
                allow_none=True,
            )

        with tab_other:
            st.caption("메모 필드는 목 데이터 전용이며 DB DDL에는 없습니다.")
            memo = st.text_area(
                "메모",
                value=(record or {}).get("memo") or "",
            )

        btn1, btn2, btn3 = st.columns(3)
        save_clicked = btn1.button("저장", type="primary")
        cancel_clicked = btn2.button("취소")
        delete_clicked = btn3.button("삭제") if record else False

        if cancel_clicked:
            st.session_state.pop("order_is_new", None)
            st.experimental_rerun()

        if delete_clicked and edit_id:

            def _del():
                repository.delete_order(edit_id)

            if handle_repo_error(_del):
                st.session_state.pop(edit_key, None)
                st.session_state.pop("order_is_new", None)
                st.success("삭제되었습니다.")
                st.experimental_rerun()

        if save_clicked:
            if to_loc is None or serial is None or customer_loc is None:
                st.error("고객 사업장, 도착 사업장, 장비는 필수입니다.")
            else:
                payload = {
                    "order_id": edit_id if not is_new else None,
                    "location_id": rel_loc if rel_loc is not None else customer_loc,
                    "technician_id": tech_id,
                    "request_date": request_d,
                    "completion_date": completion_d,
                    "order_type": order_type,
                    "serial_number": serial,
                    "order_status": order_status,
                    "from_location_id": from_loc,
                    "to_location_id": to_loc,
                    "memo": memo,
                }

                def _save():
                    return repository.save_order(payload)

                result = handle_repo_error(_save)
                if result:
                    st.session_state[edit_key] = result["order_id"]
                    st.session_state.pop("order_is_new", None)
                    st.success("저장되었습니다.")
                    st.experimental_rerun()
