from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import fk_selectbox, location_select, technician_select
from lib.components.order_header import render_order_header
from lib.constants import ORDER_STATUSES, ORDER_TYPES
from lib.labels import (
    BTN_CANCEL,
    BTN_DELETE,
    BTN_NEW,
    BTN_OPEN,
    BTN_SAVE,
    MSG_DELETED,
    MSG_SAVED,
    MSG_SELECT_ROW,
    col,
    req,
)
from lib.models import parse_date
from lib.page_utils import begin_page, handle_repo_error

begin_page("order", "📦")

edit_key = "edit_order_id"
orders = repository.list_orders()
col_list, col_detail = st.columns([1, 2])

with col_list:
    st.subheader(f"{col('order')} List")
    if orders:
        order_cols = [
            "order_id",
            "order_type",
            "order_status",
            "request_date",
            "serial_number",
        ]
        df = pd.DataFrame(orders)[order_cols].rename(
            columns={c: col(c) for c in order_cols}
        )
        st.dataframe(df, width="stretch", hide_index=True)
        ids = [o["order_id"] for o in orders]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox(col("order_id"), labels, index=idx, key="order_pick")
        c1, c2 = st.columns(2)
        if c1.button(BTN_OPEN):
            st.session_state[edit_key] = int(pick)
            st.session_state.pop("order_is_new", None)
            st.rerun()
        if c2.button(BTN_NEW):
            st.session_state[edit_key] = None
            st.session_state["order_is_new"] = True
            st.rerun()
    else:
        st.info(MSG_SELECT_ROW)
        if st.button(f"{BTN_NEW} {col('order')}"):
            st.session_state[edit_key] = None
            st.session_state["order_is_new"] = True
            st.rerun()

with col_detail:
    is_new = st.session_state.get("order_is_new", False)
    edit_id = st.session_state.get(edit_key)
    record = None if is_new else (repository.get_order(edit_id) if edit_id else None)

    if not is_new and edit_id is None and orders:
        st.info(MSG_SELECT_ROW)
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
                key="ord_cust",
                default_id=(record or {}).get("location_id"),
                required=True,
            )
            request_d = st.date_input(
                req("request_date"), value=_d((record or {}).get("request_date"))
            )
        with c2:
            tech_id = technician_select(
                key="ord_tech",
                default_id=(record or {}).get("technician_id"),
            )
            comp = (record or {}).get("completion_date")
            completion_d = st.date_input(
                col("completion_date"),
                value=parse_date(comp) if comp else None,
            )

        tab_order, tab_ship, tab_other = st.tabs(
            [col("order_type"), "Shipping", "Other"]
        )

        with tab_order:
            types = ORDER_TYPES
            tidx = (
                types.index(record["order_type"])
                if record and record["order_type"] in types
                else 0
            )
            order_type = st.selectbox(req("order_type"), types, index=tidx)
            serial = fk_selectbox(
                req("serial_number"),
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
            order_status = st.selectbox(req("order_status"), statuses, index=sidx)

        with tab_ship:
            from_loc = location_select(
                key="ord_from",
                default_id=(record or {}).get("from_location_id"),
                allow_none=True,
                field="from_location_id",
            )
            to_loc = location_select(
                key="ord_to",
                default_id=(record or {}).get("to_location_id"),
                required=True,
                field="to_location_id",
            )
            rel_loc = location_select(
                key="ord_rel",
                default_id=(record or {}).get("location_id"),
                allow_none=True,
            )

        with tab_other:
            st.caption(
                f"{col('memo')} is mock-only and not in the database DDL."
            )
            memo = st.text_area(
                col("memo"),
                value=(record or {}).get("memo") or "",
            )

        btn1, btn2, btn3 = st.columns(3)
        save_clicked = btn1.button(BTN_SAVE, type="primary")
        cancel_clicked = btn2.button(BTN_CANCEL)
        delete_clicked = btn3.button(BTN_DELETE) if record else False

        if cancel_clicked:
            st.session_state.pop("order_is_new", None)
            st.rerun()

        if delete_clicked and edit_id and handle_repo_error(
            lambda: repository.delete_order(edit_id)
        ):
            st.session_state.pop(edit_key, None)
            st.session_state.pop("order_is_new", None)
            st.success(MSG_DELETED)
            st.rerun()

        if save_clicked:
            if to_loc is None or serial is None or customer_loc is None:
                st.error(
                    f"{col('location_id')}, {col('to_location_id')}, "
                    f"{col('serial_number')} are required."
                )
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
                result = handle_repo_error(lambda: repository.save_order(payload))
                if result:
                    st.session_state[edit_key] = result["order_id"]
                    st.session_state.pop("order_is_new", None)
                    st.success(MSG_SAVED)
                    st.rerun()
