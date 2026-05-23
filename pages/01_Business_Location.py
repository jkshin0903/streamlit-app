import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.constants import LOCATION_TYPES
from lib.labels import col, req
from lib.page_utils import begin_page

begin_page("business_location", "🏢")


def _form_fields(record):
    data = {}
    if record:
        data["location_id"] = record["location_id"]
        st.number_input(col("location_id"), value=record["location_id"], disabled=True)
    data["location_name"] = st.text_input(
        req("location_name"), value=record.get("location_name", "") if record else ""
    )
    types = LOCATION_TYPES
    idx = types.index(record["location_type"]) if record and record["location_type"] in types else 0
    data["location_type"] = st.selectbox(req("location_type"), types, index=idx)
    data["address"] = st.text_input(col("address"), value=(record or {}).get("address") or "")
    data["city"] = st.text_input(col("city"), value=(record or {}).get("city") or "")
    data["state"] = st.text_input(col("state"), value=(record or {}).get("state") or "")
    data["zipcode"] = st.text_input(col("zipcode"), value=(record or {}).get("zipcode") or "")
    data["phone"] = st.text_input(col("phone"), value=(record or {}).get("phone") or "")
    return data


render_master_crud(
    pk_field="location_id",
    list_fn=repository.list_locations,
    get_fn=repository.get_location,
    save_fn=repository.save_location,
    delete_fn=repository.delete_location,
    list_columns=["location_id", "location_name", "location_type", "city", "phone"],
    render_form_fields=_form_fields,
)
