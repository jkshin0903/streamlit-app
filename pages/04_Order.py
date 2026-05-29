from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.auth_context import current_user_name
from lib.components.move_order_lines import (
    clear_move_lines,
    init_move_lines,
    render_move_order_lines,
)
from lib.components.fk_select import technician_select
from lib.constants import ORDER_STATUSES, ORDER_TYPES
from lib.labels import (
    BTN_CANCEL,
    BTN_DELETE,
    BTN_NEW,
    BTN_OPEN,
    BTN_PRINT_ORDER,
    BTN_SAVE_DRAFT,
    BTN_SUBMIT,
    MSG_DELETED,
    MSG_SAVED,
    MSG_SELECT_ROW,
    col,
    req,
)
from lib.models import parse_date
from lib.page_utils import begin_page, handle_repo_error

ORDER_TITLE = "Machine Install/Remove Order"

begin_page("order", "📦", title=ORDER_TITLE)
st.caption("SCR-IN-02 · Machine Install/Remove Order")

if st.session_state.get("prefill_move_serial"):
    sn = st.session_state.pop("prefill_move_serial")
    st.session_state["order_is_new"] = True
    st.session_state.pop("edit_order_id", None)
    init_move_lines(
        "move_order_lines",
        [{"serial_number": sn, "from_location_id": None, "to_location_id": None}],
    )

MOVE_LINES_KEY = "move_order_lines"
edit_key = "edit_order_id"
PERF_THRESHOLD_KEY = "move_perf_threshold"

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
            rec = repository.get_order(int(pick))
            if rec:
                init_move_lines(
                    MOVE_LINES_KEY,
                    [
                        {
                            "serial_number": rec["serial_number"],
                            "from_location_id": rec.get("from_location_id"),
                            "to_location_id": rec.get("to_location_id"),
                            "scheduled_date": parse_date(rec.get("request_date"))
                            or date.today(),
                            "order_id": rec["order_id"],
                            "completed": rec.get("order_status") == "Completed",
                        }
                    ],
                )
            st.rerun()
        if c2.button(BTN_NEW):
            st.session_state[edit_key] = None
            st.session_state["order_is_new"] = True
            clear_move_lines(MOVE_LINES_KEY)
            st.rerun()
    else:
        st.info(MSG_SELECT_ROW)
        if st.button(f"{BTN_NEW} {col('order')}"):
            st.session_state[edit_key] = None
            st.session_state["order_is_new"] = True
            clear_move_lines(MOVE_LINES_KEY)
            st.rerun()

with col_detail:
    is_new = st.session_state.get("order_is_new", False)
    edit_id = st.session_state.get(edit_key)
    record = None if is_new else (repository.get_order(edit_id) if edit_id else None)
    readonly = bool(
        record
        and record.get("order_status") in ("In Progress", "Completed")
        and not is_new
    )

    if not is_new and edit_id is None and orders:
        st.info(MSG_SELECT_ROW)
    else:
        if readonly:
            st.info("This order can no longer be edited after work has started.")

        h1, h2, h3 = st.columns(3)
        with h1:
            st.text_input(
                "Order Number",
                value=str(edit_id or "— (auto on save)"),
                disabled=True,
            )
        with h2:
            request_d = st.date_input(
                req("request_date"),
                value=parse_date((record or {}).get("request_date")) or date.today(),
                disabled=readonly,
            )
        with h3:
            st.text_input("Issuing Manager", value=current_user_name(), disabled=True)

        tech_id = technician_select(
            key="ord_tech",
            default_id=(record or {}).get("technician_id"),
            allow_none=False,
        )

        types = ORDER_TYPES
        tidx = (
            types.index(record["order_type"])
            if record and record["order_type"] in types
            else 0
        )
        order_type = st.selectbox(
            req("order_type"), types, index=tidx, disabled=readonly
        )

        perf_threshold = st.number_input(
            "Performance threshold (for warnings)",
            min_value=0.0,
            value=float(st.session_state.get(PERF_THRESHOLD_KEY, 100.0)),
            key=PERF_THRESHOLD_KEY,
        )

        lines = render_move_order_lines(
            MOVE_LINES_KEY,
            form_key_prefix="move",
            performance_threshold=perf_threshold,
            readonly=readonly,
        )

        notes = st.text_area(
            "Notes / Special Instructions",
            value=st.session_state.get("move_order_notes", ""),
            key="move_order_notes",
            disabled=readonly,
        )

        btn1, btn2, btn3, btn4, btn5 = st.columns(5)
        draft_clicked = btn1.button(BTN_SAVE_DRAFT, disabled=readonly)
        submit_clicked = btn2.button(BTN_SUBMIT, type="primary", disabled=readonly)
        cancel_clicked = btn3.button(BTN_CANCEL)
        delete_clicked = btn4.button(BTN_DELETE) if record else False
        print_clicked = btn5.button(BTN_PRINT_ORDER)

        if cancel_clicked:
            st.session_state.pop("order_is_new", None)
            st.rerun()

        if print_clicked and record:
            st.markdown(f"### Move Order #{record['order_id']}")
            st.write(record)
            st.caption("Use browser Print (Ctrl/Cmd+P) from the menu above.")

        if delete_clicked and edit_id and handle_repo_error(
            lambda: repository.delete_order(edit_id)
        ):
            st.session_state.pop(edit_key, None)
            st.session_state.pop("order_is_new", None)
            clear_move_lines(MOVE_LINES_KEY)
            st.success(MSG_DELETED)
            st.rerun()

        def _persist(status: str) -> None:
            if not tech_id:
                st.error(f"{col('technician_id')} is required.")
                return
            if not lines:
                st.error("At least one machine line is required.")
                return
            header = {
                "technician_id": tech_id,
                "location_id": lines[0].get("to_location_id")
                or lines[0].get("from_location_id"),
                "request_date": request_d,
                "order_type": order_type,
                "order_status": status,
                "completion_date": lines[0].get("completion_date")
                if lines[0].get("completed")
                else None,
            }
            payloads = []
            for ln in lines:
                st_status = "Completed" if ln.get("completed") else status
                payloads.append(
                    {
                        **header,
                        "order_id": ln.get("order_id"),
                        "serial_number": ln["serial_number"],
                        "from_location_id": ln.get("from_location_id"),
                        "to_location_id": ln.get("to_location_id"),
                        "order_status": st_status,
                        "completion_date": ln.get("completion_date")
                        if ln.get("completed")
                        else header.get("completion_date"),
                    }
                )
            result = handle_repo_error(
                lambda: repository.save_move_order_batch(header, payloads)
            )
            if result:
                st.session_state[edit_key] = result[0]["order_id"]
                st.session_state.pop("order_is_new", None)
                st.success(MSG_SAVED)
                if status == "Pending":
                    st.info("Technician notification sent (simulated).")
                st.rerun()

        if draft_clicked:
            _persist("Draft")
        if submit_clicked:
            _persist("Pending")
