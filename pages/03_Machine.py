from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import fk_selectbox, location_select
from lib.constants import MACHINE_STATUSES
from lib.labels import (
    BTN_CONFIRM,
    BTN_DELETE,
    BTN_NEW_MODE,
    BTN_SAVE,
    MSG_DELETED,
    MSG_NO_ROWS,
    MSG_SAVED,
    TAB_FORM,
    TAB_HISTORY,
    TAB_LIST,
    col,
    req,
)
from lib.page_utils import begin_page, handle_repo_error

begin_page("machine", "🔧")

edit_key = "edit_serial_number"
tab_list, tab_form, tab_hst = st.tabs([TAB_LIST, TAB_FORM, TAB_HISTORY])

with tab_list:
    machines = repository.list_machines()
    if machines:
        df = pd.DataFrame(machines)[
            ["serial_number", "machine_name", "model_name", "machine_status", "location_id"]
        ].rename(columns={c: col(c) for c in ["serial_number", "machine_name", "model_name", "machine_status", "location_id"]})
        st.dataframe(df, use_container_width=True, hide_index=True)
        ids = [m["serial_number"] for m in machines]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox(col("serial_number"), labels, index=idx)
        if st.button("Edit Selected"):
            st.session_state[edit_key] = int(pick)
            st.experimental_rerun()
    else:
        st.info(MSG_NO_ROWS)

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_machine(edit_id) if edit_id else None
    if st.button(BTN_NEW_MODE):
        st.session_state.pop(edit_key, None)
        st.experimental_rerun()

    with st.form("machine_form"):
        if record:
            st.number_input(col("serial_number"), value=record["serial_number"], disabled=True)
        data = {}
        if not record:
            sn = st.number_input(
                f"{col('serial_number')} (0 = auto)",
                min_value=0,
                value=0,
                step=1,
            )
            if sn > 0:
                data["serial_number"] = int(sn)
        data["machine_name"] = st.text_input(
            req("machine_name"), value=(record or {}).get("machine_name") or ""
        )
        data["model_name"] = st.text_input(
            req("model_name"), value=(record or {}).get("model_name") or ""
        )
        statuses = MACHINE_STATUSES
        sidx = (
            statuses.index(record["machine_status"])
            if record and record["machine_status"] in statuses
            else 0
        )
        data["machine_status"] = st.selectbox(req("machine_status"), statuses, index=sidx)
        data["location_id"] = location_select(
            key="machine_loc",
            default_id=(record or {}).get("location_id"),
            allow_none=True,
        )
        data["invoice_number"] = fk_selectbox(
            req("invoice_number"),
            repository.list_invoices(),
            "invoice_number",
            lambda n: f"{col('invoice_number')} {n}",
            key="machine_inv",
            default_id=(record or {}).get("invoice_number"),
        )
        submitted = st.form_submit_button(BTN_SAVE)

    if edit_id and record and st.button(BTN_DELETE):
        if handle_repo_error(lambda: repository.delete_machine(edit_id)):
            st.session_state.pop(edit_key, None)
            st.success(MSG_DELETED)
            st.experimental_rerun()

    if submitted:
        if record:
            data["serial_number"] = record["serial_number"]
        if data.get("invoice_number") is None:
            st.error(f"{col('invoice_number')} is required.")
        elif handle_repo_error(lambda: repository.save_machine(data)):
            st.session_state[edit_key] = data["serial_number"]
            st.success(MSG_SAVED)
            st.experimental_rerun()

with tab_hst:
    machines = repository.list_machines()
    if not machines:
        st.warning(f"Register {col('machine')} first.")
    else:
        serial = fk_selectbox(
            col("serial_number"),
            machines,
            "serial_number",
            lambda s: f"{repository.get_machine(s)['machine_name']} ({s})",
            key="hst_serial",
            default_id=machines[0]["serial_number"],
        )
        if serial:
            rows = repository.list_machine_contract_hst(serial)
            if rows:
                st.dataframe(
                    pd.DataFrame(rows).rename(
                        columns={
                            c: col(c)
                            for c in [
                                "machine_contract_no",
                                "contract_id",
                                "contract_start_date",
                                "contract_end_date",
                            ]
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(MSG_NO_ROWS)

            st.markdown(f"**Add {col('machine_contract_hst')}**")
            with st.form("hst_add"):
                contract_id = fk_selectbox(
                    req("contract_id"),
                    repository.list_contracts(),
                    "contract_id",
                    lambda c: f"{col('contract_id')} {c}",
                    key="hst_contract",
                )
                c_start = st.date_input(req("contract_start_date"), value=date.today())
                c_end = st.date_input(req("contract_end_date"), value=date.today())
                add = st.form_submit_button(BTN_CONFIRM)
            if add and contract_id and handle_repo_error(
                lambda: repository.save_machine_contract_hst(
                    {
                        "serial_number": serial,
                        "contract_id": contract_id,
                        "contract_start_date": c_start,
                        "contract_end_date": c_end,
                    }
                )
            ):
                st.success(MSG_SAVED)
                st.experimental_rerun()
