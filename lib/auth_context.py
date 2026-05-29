"""Current user display name for spec read-only fields (Buyer / Issuing Manager)."""

from __future__ import annotations

import streamlit as st


def current_user_name() -> str:
    try:
        user = st.secrets.get("app", {}).get("current_user")
        if user:
            return str(user)
    except Exception:
        pass
    return st.session_state.get("app_current_user", "Marge Brooks")
