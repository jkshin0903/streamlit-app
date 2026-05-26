"""List view with row selection."""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd
import streamlit as st


def list_with_selection(
    df: pd.DataFrame,
    *,
    state_key: str,
    id_column: str,
    empty_message: str = "등록된 데이터가 없습니다.",
) -> Optional[Any]:
    if df.empty:
        st.info(empty_message)
        return None

    st.dataframe(df, width="stretch", hide_index=True)

    options = df[id_column].tolist()
    labels = [str(o) for o in options]
    current = st.session_state.get(state_key)
    idx = labels.index(str(current)) if current is not None and str(current) in labels else 0

    selected_label = st.selectbox(
        "수정할 항목 선택",
        labels,
        index=idx,
        key=f"{state_key}_picker",
    )
    selected_id = type(options[0])(selected_label) if options else None
    st.session_state[state_key] = selected_id
    return selected_id


def clear_selection(state_key: str) -> None:
    st.session_state.pop(state_key, None)
