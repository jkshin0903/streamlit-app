"""Multi-line move order editor (SCR-IN-02, up to 10 machines)."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

import streamlit as st

from lib import repository
from lib.components.fk_select import fk_selectbox
from lib.constants import MAX_MOVE_ORDER_LINES
from lib.labels import BTN_ADD_MACHINE, BTN_REMOVE, col
from lib.models import parse_date
from lib.repository.reports import low_performance_at_location


def init_move_lines(state_key: str, lines: list[dict[str, Any]] | None = None) -> None:
    if state_key not in st.session_state:
        st.session_state[state_key] = lines or [_empty_line()]


def _empty_line() -> dict[str, Any]:
    return {
        "serial_number": None,
        "from_location_id": None,
        "to_location_id": None,
        "scheduled_date": date.today(),
        "scheduled_time": time(13, 0),
        "completed": False,
        "signature": "",
        "order_id": None,
    }


def clear_move_lines(state_key: str) -> None:
    st.session_state.pop(state_key, None)


def render_move_order_lines(
    state_key: str,
    *,
    form_key_prefix: str = "move",
    performance_threshold: float = 100.0,
    readonly: bool = False,
) -> list[dict[str, Any]]:
    init_move_lines(state_key)
    lines: list[dict[str, Any]] = st.session_state[state_key]

    if not readonly and st.button(BTN_ADD_MACHINE, key=f"{form_key_prefix}_add_m"):
        if len(lines) >= MAX_MOVE_ORDER_LINES:
            st.warning(f"Maximum {MAX_MOVE_ORDER_LINES} machines per order.")
        else:
            lines.append(_empty_line())
            st.session_state[state_key] = lines
            st.rerun()

    machines = repository.list_machines()
    to_remove: list[int] = []

    for idx, line in enumerate(lines):
        mrec = None
        with st.expander(f"Machine line {idx + 1}", expanded=idx == 0):
            if not machines:
                st.warning("Register machines before creating move orders.")
                continue
            serial_labels = [m["serial_number"] for m in machines]
            sn_default = (
                serial_labels.index(line["serial_number"])
                if line.get("serial_number") in serial_labels
                else 0
            )
            serial = st.selectbox(
                col("serial_number"),
                options=serial_labels,
                index=sn_default,
                key=f"{form_key_prefix}_sn_{idx}",
                disabled=readonly,
            )
            line["serial_number"] = serial
            mrec = repository.get_machine(serial)
            if mrec:
                loc = repository.get_location(mrec.get("location_id"))
                st.caption(
                    f"Current: {mrec.get('machine_name')} @ "
                    f"{loc['location_name'] if loc else '—'} "
                    f"({mrec.get('machine_status')})"
                )
                if line.get("from_location_id") is None:
                    line["from_location_id"] = mrec.get("location_id")

            c1, c2 = st.columns(2)
            with c1:
                line["from_location_id"] = fk_selectbox(
                    col("from_location_id"),
                    repository.list_locations(),
                    "location_id",
                    repository.location_label,
                    key=f"{form_key_prefix}_from_{idx}",
                    default_id=line.get("from_location_id"),
                    allow_none=True,
                )
            with c2:
                line["to_location_id"] = fk_selectbox(
                    col("to_location_id"),
                    repository.list_locations(),
                    "location_id",
                    repository.location_label,
                    key=f"{form_key_prefix}_to_{idx}",
                    default_id=line.get("to_location_id"),
                    allow_none=True,
                )

            if (
                line.get("from_location_id")
                and line.get("to_location_id")
                and line["from_location_id"] == line["to_location_id"]
            ):
                st.error("Install and remove location cannot be the same.")

            if (
                line.get("serial_number")
                and line.get("to_location_id")
                and mrec
                and mrec.get("location_id") == line["to_location_id"]
            ):
                st.warning("Machine is already installed at this location.")

            if (
                line.get("serial_number")
                and line.get("to_location_id")
                and low_performance_at_location(
                    line["serial_number"], line["to_location_id"], performance_threshold
                )
            ):
                st.warning(
                    "This machine had low performance at this location in the past."
                )

            d1, d2 = st.columns(2)
            with d1:
                today = date.today()
                raw_scheduled = line.get("scheduled_date") or today
                scheduled = (
                    raw_scheduled
                    if isinstance(raw_scheduled, date)
                    else (parse_date(raw_scheduled) or today)
                )
                # New orders: today+ only (spec). Existing/historical dates may be in the past.
                is_existing_line = bool(line.get("order_id"))
                if is_existing_line or readonly or scheduled < today:
                    line["scheduled_date"] = st.date_input(
                        "Scheduled Date",
                        value=scheduled,
                        key=f"{form_key_prefix}_sdate_{idx}",
                        disabled=readonly,
                    )
                else:
                    line["scheduled_date"] = st.date_input(
                        "Scheduled Date",
                        value=max(scheduled, today),
                        min_value=today,
                        key=f"{form_key_prefix}_sdate_{idx}",
                        disabled=readonly,
                    )
            with d2:
                line["scheduled_time"] = st.time_input(
                    "Scheduled Time",
                    value=line.get("scheduled_time") or time(13, 0),
                    key=f"{form_key_prefix}_stime_{idx}",
                    disabled=readonly,
                )

            line["completed"] = st.checkbox(
                "Completion",
                value=bool(line.get("completed")),
                key=f"{form_key_prefix}_done_{idx}",
                disabled=readonly,
            )
            if line["completed"]:
                line["completion_date"] = datetime.now().date()
            line["signature"] = st.text_input(
                "Technician Signature",
                value=line.get("signature") or "",
                key=f"{form_key_prefix}_sig_{idx}",
                disabled=readonly,
            )

            if not readonly and st.button(BTN_REMOVE, key=f"{form_key_prefix}_rm_{idx}"):
                to_remove.append(idx)

    if to_remove:
        for i in sorted(to_remove, reverse=True):
            del lines[i]
        if not lines:
            lines.append(_empty_line())
        st.session_state[state_key] = lines
        st.rerun()

    return [dict(ln) for ln in lines if ln.get("serial_number") is not None]
