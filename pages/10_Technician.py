import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.labels import col, req
from lib.page_utils import begin_page

begin_page("technician", "👷")


def _form_fields(record):
    data = {}
    if record:
        data["technician_id"] = record["technician_id"]
        st.number_input(col("technician_id"), value=record["technician_id"], disabled=True)
    data["technician_name"] = st.text_input(
        req("technician_name"), value=(record or {}).get("technician_name") or ""
    )
    return data


render_master_crud(
    pk_field="technician_id",
    list_fn=repository.list_technicians,
    get_fn=repository.get_technician,
    save_fn=repository.save_technician,
    delete_fn=repository.delete_technician,
    list_columns=["technician_id", "technician_name"],
    render_form_fields=_form_fields,
)
