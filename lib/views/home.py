"""Home page content."""

import streamlit as st

from lib import repository
from lib.labels import HOME_TITLE, col
from lib.page_utils import setup_page


def render() -> None:
    setup_page(HOME_TITLE, "🏭")
    st.title(HOME_TITLE)
    st.caption("Live MySQL/MariaDB (direct) · Amusement Machine Asset Tracking")

    st.markdown(
        """
This app reads and writes your database (GP2 MariaDB DDL).  
Configure `db.ini` for a direct connection (Aiven, etc.).  
See `db.ini.example` or set `DB_HOST` environment variables.
"""
    )

    st.divider()

    st.subheader("Functional spec screens")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
**Input (SCR-IN)**  
- **06 Purchase Order** — PO entry, PDF/fax, Pending status  
- **04 Order** — Install / remove / move (multi-machine)  
"""
        )
    with c2:
        st.markdown(
            """
**Reports (SCR-RPT)**  
- **11 Installation Report** — equipment by location  
- **12 Annual Purchase Report** — purchases & disposal for accounting  
- **13 Machine Performance Report** — revenue, repair, recommendations  
"""
        )

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

**4. Field service**  
{col('order')} (Draft → Pending → Completed)  
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
