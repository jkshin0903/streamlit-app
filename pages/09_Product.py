import streamlit as st

from lib import repository
from lib.components.master_crud import render_master_crud
from lib.labels import col, req
from lib.page_utils import begin_page

begin_page("product", "📊")


def _form_fields(record):
    data = {}
    if record:
        data["product_no"] = record["product_no"]
        st.number_input(col("product_no"), value=record["product_no"], disabled=True)
    data["product_name"] = st.text_input(
        req("product_name"), value=(record or {}).get("product_name") or ""
    )
    return data


render_master_crud(
    pk_field="product_no",
    list_fn=repository.list_products,
    get_fn=repository.get_product,
    save_fn=repository.save_product,
    delete_fn=repository.delete_product,
    list_columns=["product_no", "product_name"],
    render_form_fields=_form_fields,
)
