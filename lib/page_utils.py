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
    repository.init_if_needed()


def begin_page(entity: str, icon: str = "") -> str:
    """
    Single display name for sidebar (via pages/NN_Name.py filename) and st.title.
    entity: table/entity key, e.g. business_location -> "Business Location"
    """
    title = col(entity)
    setup_page(title, icon)
    st.title(title)
    return title


def handle_repo_error(fn):
    try:
        return fn()
    except repository.RepositoryError as e:
        st.error(str(e))
        return None
