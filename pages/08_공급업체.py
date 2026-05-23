import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.page_utils import setup_page

setup_page("공급업체 관리", "🏭")


def _form_fields(record):
    data = {}
    if record:
        data["vendor_id"] = record["vendor_id"]
        st.number_input("Vendor ID", value=record["vendor_id"], disabled=True)
    data["vendor_name"] = st.text_input(
        "공급업체명 *", value=(record or {}).get("vendor_name") or ""
    )
    data["address"] = st.text_input("주소 *", value=(record or {}).get("address") or "")
    data["phone"] = st.text_input("전화", value=(record or {}).get("phone") or "")
    data["fax"] = st.text_input("FAX", value=(record or {}).get("fax") or "")
    return data


render_master_crud(
    title="공급업체 관리",
    pk_field="vendor_id",
    list_fn=repository.list_vendors,
    get_fn=repository.get_vendor,
    save_fn=repository.save_vendor,
    delete_fn=repository.delete_vendor,
    list_columns=["vendor_id", "vendor_name", "address", "phone"],
    column_labels={
        "vendor_id": "ID",
        "vendor_name": "업체명",
        "address": "주소",
        "phone": "전화",
    },
    render_form_fields=_form_fields,
)
