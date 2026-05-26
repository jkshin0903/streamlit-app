"""Home page content."""

import streamlit as st

from lib import repository
from lib.labels import HOME_TITLE, col
from lib.page_utils import setup_page


def render() -> None:
    setup_page(HOME_TITLE, "🏭")
    st.title(HOME_TITLE)
    st.caption("Mock in-memory data — aligns with GP2 MariaDB DDL")

    st.markdown(
        """
This app is a **UI prototype** based on the GP2 MariaDB DDL.  
Data is kept in an **in-memory mock store** loaded from `data/seed.json`.
"""
    )

    if st.button("Reset Demo Data"):
        repository.reset_demo_data()
        st.success("Restored from seed.json.")
        st.experimental_rerun()

    st.divider()

    st.subheader("Recommended Workflow")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
**1. Master data**  
1. {col('business_location')}  
2. {col('vendor')} · {col('product')} · {col('technician')}  

**2. Procurement**  
{col('purchase_request')} → {col('purchase_order')} → {col('invoice')} → {col('machine')}
"""
        )

    with col2:
        st.markdown(
            f"""
**3. Equipment operations**  
{col('contract')} → {col('machine')} → {col('machine_contract_hst')}  

**4. Orders**  
{col('order')} (Pending) → assign {col('technician_id')} → Completed
"""
        )

    st.subheader("Sidebar Navigation")
    st.markdown("Use the sidebar pages; numeric prefixes follow the workflow order.")

    with st.expander("Data Summary"):
        st.write(
            {
                col("business_location"): len(repository.list_locations()),
                col("vendor"): len(repository.list_vendors()),
                col("product"): len(repository.list_products()),
                col("technician"): len(repository.list_technicians()),
                col("purchase_request"): len(repository.list_purchase_requests()),
                col("purchase_order"): len(repository.list_purchase_orders()),
                col("invoice"): len(repository.list_invoices()),
                col("contract"): len(repository.list_contracts()),
                col("machine"): len(repository.list_machines()),
                col("order"): len(repository.list_orders()),
            }
        )
