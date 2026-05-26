"""Form action buttons outside st.form."""

from __future__ import annotations

import streamlit as st


def render_cancel_new(
    *,
    edit_state_key: str,
    on_new_key: str = "btn_new",
) -> bool:
    """Return True if user clicked '신규' or '취소'."""
    col1, col2 = st.columns(2)
    new_clicked = col1.button("신규 등록", key=on_new_key)
    cancel_clicked = col2.button("취소", key=f"{on_new_key}_cancel")
    if new_clicked or cancel_clicked:
        st.session_state.pop(edit_state_key, None)
        return True
    return False
