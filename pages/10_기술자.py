import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.page_utils import setup_page

setup_page("기술자 관리", "👷")


def _form_fields(record):
    data = {}
    if record:
        data["technician_id"] = record["technician_id"]
        st.number_input("Technician ID", value=record["technician_id"], disabled=True)
    data["technician_name"] = st.text_input(
        "기술자명 *", value=(record or {}).get("technician_name") or ""
    )
    return data


render_master_crud(
    title="기술자 관리",
    pk_field="technician_id",
    list_fn=repository.list_technicians,
    get_fn=repository.get_technician,
    save_fn=repository.save_technician,
    delete_fn=repository.delete_technician,
    list_columns=["technician_id", "technician_name"],
    column_labels={"technician_id": "ID", "technician_name": "이름"},
    render_form_fields=_form_fields,
)
