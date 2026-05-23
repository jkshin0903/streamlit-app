from datetime import date

import streamlit as st

from lib import repository
from lib.components.fk_select import location_select
from lib.components.master_crud import render_master_crud
from lib.constants import CONTRACT_STATUSES
from lib.models import parse_date
from lib.page_utils import setup_page

setup_page("계약 관리", "📋")


def _d(val):
    return parse_date(val) or date.today()


def _form_fields(record):
    data = {}
    if record:
        data["contract_id"] = record["contract_id"]
        st.number_input("Contract ID", value=record["contract_id"], disabled=True)
    data["location_id"] = location_select(
        "사업장 *",
        key="contract_loc",
        default_id=(record or {}).get("location_id"),
    )
    data["contract_date"] = st.date_input(
        "계약일 *", value=_d((record or {}).get("contract_date"))
    )
    data["start_date"] = st.date_input(
        "시작일 *", value=_d((record or {}).get("start_date"))
    )
    data["end_date"] = st.date_input(
        "종료일 *", value=_d((record or {}).get("end_date"))
    )
    statuses = CONTRACT_STATUSES
    idx = (
        statuses.index(record["contract_status"])
        if record and record["contract_status"] in statuses
        else 0
    )
    data["contract_status"] = st.selectbox("계약 상태 *", statuses, index=idx)
    pickup = (record or {}).get("pickup_date")
    data["pickup_date"] = st.date_input(
        "회수일",
        value=parse_date(pickup) if pickup else None,
    )
    data["pickup_reason"] = st.text_area(
        "회수 사유", value=(record or {}).get("pickup_reason") or ""
    )
    return data


render_master_crud(
    title="계약 관리",
    pk_field="contract_id",
    list_fn=repository.list_contracts,
    get_fn=repository.get_contract,
    save_fn=repository.save_contract,
    delete_fn=repository.delete_contract,
    list_columns=["contract_id", "location_id", "start_date", "end_date", "contract_status"],
    column_labels={
        "contract_id": "ID",
        "location_id": "사업장ID",
        "start_date": "시작",
        "end_date": "종료",
        "contract_status": "상태",
    },
    render_form_fields=_form_fields,
)
