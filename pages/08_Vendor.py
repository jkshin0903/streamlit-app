import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.labels import col, req
from lib.page_utils import begin_page

begin_page("vendor", "🏭")


def _form_fields(record):
    data = {}
    if record:
        data["vendor_id"] = record["vendor_id"]
        st.number_input(col("vendor_id"), value=record["vendor_id"], disabled=True)
    data["vendor_name"] = st.text_input(
        req("vendor_name"), value=(record or {}).get("vendor_name") or ""
    )
    data["address"] = st.text_input(req("address"), value=(record or {}).get("address") or "")
    data["phone"] = st.text_input(col("phone"), value=(record or {}).get("phone") or "")
    data["fax"] = st.text_input(col("fax"), value=(record or {}).get("fax") or "")
    return data


render_master_crud(
    pk_field="vendor_id",
    list_fn=repository.list_vendors,
    get_fn=repository.get_vendor,
    save_fn=repository.save_vendor,
    delete_fn=repository.delete_vendor,
    list_columns=["vendor_id", "vendor_name", "address", "phone"],
    render_form_fields=_form_fields,
)
