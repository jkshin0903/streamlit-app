import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.constants import LOCATION_TYPES
from lib.page_utils import setup_page

setup_page("사업장 관리", "🏢")


def _form_fields(record):
    data = {}
    if record:
        data["location_id"] = record["location_id"]
        st.number_input("Location ID", value=record["location_id"], disabled=True)
    data["location_name"] = st.text_input(
        "사업장명 *", value=record.get("location_name", "") if record else ""
    )
    types = LOCATION_TYPES
    idx = types.index(record["location_type"]) if record and record["location_type"] in types else 0
    data["location_type"] = st.selectbox("사업장 유형 *", types, index=idx)
    data["address"] = st.text_input("주소", value=(record or {}).get("address") or "")
    data["city"] = st.text_input("도시", value=(record or {}).get("city") or "")
    data["state"] = st.text_input("주/지역", value=(record or {}).get("state") or "")
    data["zipcode"] = st.text_input("우편번호", value=(record or {}).get("zipcode") or "")
    data["phone"] = st.text_input("전화번호", value=(record or {}).get("phone") or "")
    return data


render_master_crud(
    title="사업장 관리",
    pk_field="location_id",
    list_fn=repository.list_locations,
    get_fn=repository.get_location,
    save_fn=repository.save_location,
    delete_fn=repository.delete_location,
    list_columns=["location_id", "location_name", "location_type", "city", "phone"],
    column_labels={
        "location_id": "ID",
        "location_name": "사업장명",
        "location_type": "유형",
        "city": "도시",
        "phone": "전화",
    },
    render_form_fields=_form_fields,
    id_label="Location ID",
)
