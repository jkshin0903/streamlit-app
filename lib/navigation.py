"""Sidebar navigation with per-page titles and icons (st.navigation)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"

# Sidebar title overrides (default: derived from filename)
PAGE_TITLES: dict[str, str] = {
    "04_Order.py": "Machine Install/Remove Order",
}

# Icons aligned with each page's begin_page(..., icon=...)
PAGE_ICONS: dict[str, str] = {
    "01_Business_Location.py": "🏢",
    "02_Contract.py": "📋",
    "03_Machine.py": "🔧",
    "04_Order.py": "📦",
    "05_Purchase_Request.py": "🛒",
    "06_Purchase_Order.py": "📄",
    "07_Invoice.py": "🧾",
    "08_Vendor.py": "🏭",
    "09_Product.py": "📊",
    "10_Technician.py": "👷",
    "11_Installation_Report.py": "📊",
    "12_Annual_Purchase_Report.py": "📈",
    "13_Machine_Performance_Report.py": "📉",
}


def _render_home() -> None:
    from lib.views.home import render

    render()


def _title_from_filename(path: Path) -> str:
    stem = path.stem
    if "_" in stem:
        return stem.split("_", 1)[1].replace("_", " ")
    return stem


def build_navigation() -> st.navigation:
    entries: list[st.Page] = [
        st.Page(_render_home, title="Home", icon="🏭", default=True),
    ]
    for path in sorted(PAGES_DIR.glob("*.py")):
        title = PAGE_TITLES.get(path.name, _title_from_filename(path))
        icon = PAGE_ICONS.get(path.name, "📄")
        entries.append(st.Page(str(path), title=title, icon=icon))

    return st.navigation(entries, position="sidebar")
