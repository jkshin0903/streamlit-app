"""Simple master-data list + form CRUD."""

from __future__ import annotations

from typing import Any, Callable, Optional

import pandas as pd
import streamlit as st

from lib import repository
from lib.labels import (
    BTN_DELETE,
    BTN_EDIT_SELECTED,
    BTN_NEW_MODE,
    BTN_SAVE,
    MSG_DELETED,
    MSG_NO_ROWS,
    MSG_SAVED,
    TAB_FORM,
    TAB_LIST,
    col,
)
from lib.page_utils import handle_repo_error


def render_master_crud(
    *,
    pk_field: str,
    list_fn: Callable[[], list[dict[str, Any]]],
    get_fn: Callable[[Any], Optional[dict[str, Any]]],
    save_fn: Callable[[dict[str, Any]], dict[str, Any]],
    delete_fn: Callable[[Any], None],
    list_columns: list[str],
    column_labels: dict[str, str] | None = None,
    render_form_fields: Callable[[Optional[dict[str, Any]]], dict[str, Any]],
    auto_id: bool = True,
) -> None:
    repository.init_if_needed()
    display_labels = column_labels or {c: col(c) for c in list_columns}

    edit_key = f"edit_{pk_field}"
    tab_list, tab_form = st.tabs([TAB_LIST, TAB_FORM])

    with tab_list:
        rows = list_fn()
        if rows:
            df = pd.DataFrame(rows)
            display_cols = [c for c in list_columns if c in df.columns]
            df = df[display_cols].rename(columns=display_labels)
            st.dataframe(df, width="stretch", hide_index=True)
            ids = [r[pk_field] for r in rows]
            labels = [str(i) for i in ids]
            cur = st.session_state.get(edit_key)
            idx = labels.index(str(cur)) if cur is not None and str(cur) in labels else 0
            pick = st.selectbox(col(pk_field), labels, index=idx, key=f"{pk_field}_pick")
            if st.button(BTN_EDIT_SELECTED, key=f"{pk_field}_edit_btn"):
                st.session_state[edit_key] = type(ids[0])(pick)
                st.rerun()
        else:
            st.info(MSG_NO_ROWS)

    with tab_form:
        edit_id = st.session_state.get(edit_key)
        record = get_fn(edit_id) if edit_id is not None else None
        is_new = record is None

        if st.button(BTN_NEW_MODE, key=f"{pk_field}_new"):
            st.session_state.pop(edit_key, None)
            st.rerun()

        if not is_new:
            st.caption(f"Editing {col(pk_field)} {edit_id}")

        with st.form(f"{pk_field}_form"):
            data = render_form_fields(record)
            submitted = st.form_submit_button(BTN_SAVE)

        if edit_id is not None and not is_new:
            if st.button(BTN_DELETE, type="secondary", key=f"{pk_field}_delete"):
                def _del():
                    delete_fn(edit_id)
                    st.session_state.pop(edit_key, None)
                    return True

                if handle_repo_error(_del):
                    st.success(MSG_DELETED)
                    st.rerun()

        if submitted:
            if not is_new:
                data[pk_field] = edit_id
            elif not auto_id:
                if data.get(pk_field) is None:
                    st.error(f"{col(pk_field)} is required.")
                    return

            def _save():
                saved = save_fn(data)
                st.session_state[edit_key] = saved[pk_field]
                return saved

            result = handle_repo_error(_save)
            if result:
                st.success(MSG_SAVED)
                st.rerun()
