from datetime import date

import pandas as pd
import streamlit as st

from lib import repository
from lib.components.fk_select import fk_selectbox, location_select
from lib.constants import MACHINE_STATUSES
from lib.models import parse_date
from lib.page_utils import handle_repo_error, setup_page

setup_page("장비 관리", "🔧")

st.title("장비 관리")
repository.init_if_needed()

edit_key = "edit_serial_number"
tab_list, tab_form, tab_hst = st.tabs(["목록 조회", "신규 등록 / 수정", "계약 이력"])

with tab_list:
    machines = repository.list_machines()
    if machines:
        df = pd.DataFrame(machines)[
            ["serial_number", "machine_name", "model_name", "machine_status", "location_id"]
        ]
        st.dataframe(df, use_container_width=True, hide_index=True)
        ids = [m["serial_number"] for m in machines]
        labels = [str(i) for i in ids]
        cur = st.session_state.get(edit_key)
        idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
        pick = st.selectbox("수정할 시리얼", labels, index=idx)
        if st.button("선택 항목 수정"):
            st.session_state[edit_key] = int(pick)
            st.experimental_rerun()
    else:
        st.info("등록된 장비가 없습니다.")

with tab_form:
    edit_id = st.session_state.get(edit_key)
    record = repository.get_machine(edit_id) if edit_id else None
    if st.button("신규 등록 모드"):
        st.session_state.pop(edit_key, None)
        st.experimental_rerun()

    with st.form("machine_form"):
        if record:
            st.number_input("시리얼 번호", value=record["serial_number"], disabled=True)
        data = {}
        if not record:
            sn = st.number_input(
                "시리얼 번호 * (0이면 자동 부여)", min_value=0, value=0, step=1
            )
            if sn > 0:
                data["serial_number"] = int(sn)
        data["machine_name"] = st.text_input(
            "장비명 *", value=(record or {}).get("machine_name") or ""
        )
        data["model_name"] = st.text_input(
            "모델명 *", value=(record or {}).get("model_name") or ""
        )
        statuses = MACHINE_STATUSES
        sidx = (
            statuses.index(record["machine_status"])
            if record and record["machine_status"] in statuses
            else 0
        )
        data["machine_status"] = st.selectbox("장비 상태 *", statuses, index=sidx)
        data["location_id"] = location_select(
            "배치 사업장",
            key="machine_loc",
            default_id=(record or {}).get("location_id"),
            allow_none=True,
        )
        data["invoice_number"] = fk_selectbox(
            "연결 송장 *",
            repository.list_invoices(),
            "invoice_number",
            lambda n: f"송장 #{n}",
            key="machine_inv",
            default_id=(record or {}).get("invoice_number"),
        )
        submitted = st.form_submit_button("저장")

    if edit_id and record and st.button("삭제"):
        if handle_repo_error(lambda: repository.delete_machine(edit_id)):
            st.session_state.pop(edit_key, None)
            st.success("삭제되었습니다.")
            st.experimental_rerun()

    if submitted:
        if record:
            data["serial_number"] = record["serial_number"]
        if data.get("invoice_number") is None:
            st.error("연결 송장을 선택하세요.")
        else:

            def _save():
                return repository.save_machine(data)

            if handle_repo_error(_save):
                st.session_state[edit_key] = data["serial_number"]
                st.success("저장되었습니다.")
                st.experimental_rerun()

with tab_hst:
    machines = repository.list_machines()
    if not machines:
        st.warning("장비를 먼저 등록하세요.")
    else:
        serial = fk_selectbox(
            "시리얼 번호",
            machines,
            "serial_number",
            lambda s: f"{repository.get_machine(s)['machine_name']} ({s})",
            key="hst_serial",
            default_id=machines[0]["serial_number"],
        )
        if serial:
            rows = repository.list_machine_contract_hst(serial)
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("계약 이력이 없습니다.")

            st.markdown("**이력 추가**")
            with st.form("hst_add"):
                contract_id = fk_selectbox(
                    "계약 *",
                    repository.list_contracts(),
                    "contract_id",
                    lambda c: f"계약 #{c}",
                    key="hst_contract",
                )
                c_start = st.date_input("계약 시작일 *", value=date.today())
                c_end = st.date_input("계약 종료일 *", value=date.today())
                add = st.form_submit_button("추가")
            if add and contract_id:

                def _add():
                    return repository.save_machine_contract_hst(
                        {
                            "serial_number": serial,
                            "contract_id": contract_id,
                            "contract_start_date": c_start,
                            "contract_end_date": c_end,
                        }
                    )

                if handle_repo_error(_add):
                    st.success("이력이 추가되었습니다.")
                    st.experimental_rerun()
