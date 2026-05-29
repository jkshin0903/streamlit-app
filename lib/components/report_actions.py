"""Shared export / print actions for report pages."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from lib.export_utils import dataframe_to_excel_bytes
from lib.labels import BTN_EXPORT_EXCEL, BTN_PRINT_REPORT


def render_report_actions(df: pd.DataFrame, *, file_prefix: str) -> None:
    c1, c2 = st.columns(2)
    if c1.button(BTN_EXPORT_EXCEL):
        st.download_button(
            "Download Excel",
            data=dataframe_to_excel_bytes(df),
            file_name=f"{file_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    if c2.button(BTN_PRINT_REPORT):
        st.info("Use browser Print (Ctrl/Cmd+P). Results are shown above.")
