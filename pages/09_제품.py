import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.page_utils import setup_page

setup_page("제품 관리", "📊")


def _form_fields(record):
    data = {}
    if record:
        data["product_no"] = record["product_no"]
        st.number_input("Product No", value=record["product_no"], disabled=True)
    data["product_name"] = st.text_input(
        "제품명 *", value=(record or {}).get("product_name") or ""
    )
    return data


render_master_crud(
    title="제품 관리",
    pk_field="product_no",
    list_fn=repository.list_products,
    get_fn=repository.get_product,
    save_fn=repository.save_product,
    delete_fn=repository.delete_product,
    list_columns=["product_no", "product_name"],
    column_labels={"product_no": "번호", "product_name": "제품명"},
    render_form_fields=_form_fields,
)
