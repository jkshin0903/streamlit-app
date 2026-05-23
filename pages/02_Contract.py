from datetime import date

import streamlit as st

from lib import repository
from lib.components.fk_select import location_select
from lib.components.master_crud import render_master_crud
from lib.constants import CONTRACT_STATUSES
from lib.labels import col, req
from lib.models import parse_date
from lib.page_utils import begin_page

begin_page("contract", "📋")


def _d(val):
    return parse_date(val) or date.today()


def _form_fields(record):
    data = {}
    if record:
        data["contract_id"] = record["contract_id"]
        st.number_input(col("contract_id"), value=record["contract_id"], disabled=True)
    data["location_id"] = location_select(
        key="contract_loc",
        default_id=(record or {}).get("location_id"),
        required=True,
    )
    data["contract_date"] = st.date_input(
        req("contract_date"), value=_d((record or {}).get("contract_date"))
    )
    data["start_date"] = st.date_input(
        req("start_date"), value=_d((record or {}).get("start_date"))
    )
    data["end_date"] = st.date_input(
        req("end_date"), value=_d((record or {}).get("end_date"))
    )
    statuses = CONTRACT_STATUSES
    idx = (
        statuses.index(record["contract_status"])
        if record and record["contract_status"] in statuses
        else 0
    )
    data["contract_status"] = st.selectbox(req("contract_status"), statuses, index=idx)
    pickup = (record or {}).get("pickup_date")
    data["pickup_date"] = st.date_input(
        col("pickup_date"),
        value=parse_date(pickup) if pickup else None,
    )
    data["pickup_reason"] = st.text_area(
        col("pickup_reason"), value=(record or {}).get("pickup_reason") or ""
    )
    return data


render_master_crud(
    pk_field="contract_id",
    list_fn=repository.list_contracts,
    get_fn=repository.get_contract,
    save_fn=repository.save_contract,
    delete_fn=repository.delete_contract,
    list_columns=["contract_id", "location_id", "start_date", "end_date", "contract_status"],
    render_form_fields=_form_fields,
)
