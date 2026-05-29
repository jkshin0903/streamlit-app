"""Shared page bootstrap."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lib import repository  # noqa: E402
from lib.labels import col  # noqa: E402


def setup_page(title: str, icon: str = "") -> None:
    """Browser tab title only. Prefer begin_page() for sidebar + heading alignment."""
    if icon:
        st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    else:
        st.set_page_config(page_title=title, layout="wide")
    try:
        repository.init_if_needed()
    except Exception as e:
        from lib.db import DbConfigError

        if isinstance(e, DbConfigError):
            st.error(str(e))
            st.stop()
        raise


def begin_page(entity: str, icon: str = "", *, title: str | None = None) -> str:
    """
    Page heading and browser tab title.
    entity: table/entity key when title is omitted (e.g. business_location).
    title: override display name (sidebar label uses st.navigation in app.py).
    """
    display = title if title is not None else col(entity)
    setup_page(display, icon)
    st.title(display)
    return display


def handle_repo_error(fn):
    try:
        return fn()
    except repository.RepositoryError as e:
        st.error(str(e))
        return None
