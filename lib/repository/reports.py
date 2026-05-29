"""Report data builders (func spec SCR-RPT-01..03)."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from lib.constants import (
    DEFAULT_RS_REVENUE_SHARE,
    MACHINE_STATUS_TO_REPORT,
    MIN_DATA_DAYS_WARNING,
    MIN_EVALUATION_DAYS,
    REPAIR_COST_ESTIMATE,
    REPAIR_TO_REVENUE_JUNK_RATIO,
)
from lib.models import parse_date
from lib.repository import (
    business_location,
    contract,
    invoice,
    machine,
    order,
    product,
    purchase_order,
    vendor,
)


def _machine_type(model_name: str | None, machine_name: str | None) -> str:
    text = f"{model_name or ''} {machine_name or ''}".lower()
    for kind in ("pinball", "pool", "jukebox", "video"):
        if kind in text:
            if kind == "pool":
                return "Pool Table"
            if kind == "video":
                return "Video Game"
            return kind.title() if kind != "pinball" else "Pinball"
    return "Other"


def _invoice_totals_for_machine(serial_number: int) -> tuple[Optional[date], float]:
    m = machine.get_machine(serial_number)
    if not m or not m.get("invoice_number"):
        return None, 0.0
    inv = invoice.get_invoice(m["invoice_number"])
    if not inv:
        return None, 0.0
    inv_date = parse_date(inv.get("invoice_date"))
    total = sum(
        float(i["quantity"]) * float(i["unit_price"])
        for i in inv.get("items", invoice.list_invoice_items(m["invoice_number"]))
    )
    return inv_date, total


def _repair_count(serial_number: int) -> int:
    return sum(
        1
        for o in order.list_orders()
        if o["serial_number"] == serial_number and o.get("order_type") == "Repair"
    )


def _installation_date(serial_number: int, location_id: int | None) -> Optional[date]:
    completed = [
        o
        for o in order.list_orders()
        if o["serial_number"] == serial_number
        and o.get("order_status") == "Completed"
        and o.get("to_location_id") == location_id
    ]
    if completed:
        dates = [parse_date(o["completion_date"] or o["request_date"]) for o in completed]
        dates = [d for d in dates if d]
        if dates:
            return max(dates)
    hst = machine.list_machine_contract_hst(serial_number)
    if hst:
        dates = [parse_date(h["contract_start_date"]) for h in hst]
        dates = [d for d in dates if d]
        if dates:
            return min(dates)
    return None


def _location_history_text(serial_number: int) -> str:
    parts: list[str] = []
    moves = sorted(
        [
            o
            for o in order.list_orders()
            if o["serial_number"] == serial_number and o.get("order_status") == "Completed"
        ],
        key=lambda o: o.get("request_date") or "",
    )
    for o in moves:
        to_id = o.get("to_location_id")
        loc = business_location.get_location(to_id) if to_id else None
        name = loc["location_name"] if loc else f"#{to_id}"
        rd = o.get("request_date", "")
        cd = o.get("completion_date") or rd
        parts.append(f"{name} ({rd}~{cd})")
    return " → ".join(parts) if parts else "—"


def build_installation_report(
    *,
    location_ids: list[int] | None,
    machine_types: list[str] | None,
    report_statuses: list[str],
    install_from: Optional[date],
    install_to: Optional[date],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for m in machine.list_machines():
        loc_id = m.get("location_id")
        loc = business_location.get_location(loc_id) if loc_id else None
        report_status = MACHINE_STATUS_TO_REPORT.get(
            m.get("machine_status", ""), m.get("machine_status", "")
        )
        if report_status not in report_statuses:
            continue
        mtype = _machine_type(m.get("model_name"), m.get("machine_name"))
        if machine_types and "All" not in machine_types and mtype not in machine_types:
            continue
        if location_ids and loc_id not in location_ids:
            continue
        purchase_d, purchase_price = _invoice_totals_for_machine(m["serial_number"])
        install_d = _installation_date(m["serial_number"], loc_id)
        if install_from and install_d and install_d < install_from:
            continue
        if install_to and install_d and install_d > install_to:
            continue
        rows.append(
            {
                "business_location": loc["location_name"] if loc else "—",
                "location_address": (
                    f"{loc.get('address', '')}, {loc.get('city', '')}"
                    if loc
                    else "—"
                ),
                "machine_type": mtype,
                "machine_name": m.get("machine_name", ""),
                "serial_number": m["serial_number"],
                "manufacturer": m.get("model_name") or "—",
                "purchase_date": purchase_d.isoformat() if purchase_d else "",
                "purchase_price": purchase_price,
                "installation_date": install_d.isoformat() if install_d else "",
                "current_status": report_status,
                "repair_count": _repair_count(m["serial_number"]),
                "location_id": loc_id,
            }
        )
    rows.sort(
        key=lambda r: (
            r["business_location"],
            r["machine_type"],
            r.get("installation_date") or "",
        )
    )
    return rows


def build_annual_purchase_report(
    *,
    year: int,
    date_from: Optional[date],
    date_to: Optional[date],
    vendor_id: Optional[int],
    machine_type: Optional[str],
    po_status: Optional[str],
) -> list[dict[str, Any]]:
    if date_from is None:
        date_from = date(year, 1, 1)
    if date_to is None:
        date_to = date(year, 12, 31)

    rows: list[dict[str, Any]] = []
    for po in purchase_order.list_purchase_orders():
        po_d = parse_date(po.get("purchase_order_date"))
        if not po_d or po_d < date_from or po_d > date_to:
            continue
        status = po.get("purchase_order_status", "")
        if po_status and po_status != "All" and status != po_status:
            continue
        if vendor_id is not None and po["vendor_id"] != vendor_id:
            continue
        v = vendor.get_vendor(po["vendor_id"])
        items = purchase_order.list_purchase_order_items(po["purchase_order_id"])
        invs = [
            i
            for i in invoice.list_invoices()
            if i["purchase_order_id"] == po["purchase_order_id"]
        ]
        receive_date = ""
        serials = ""
        if invs:
            inv = invoice.get_invoice(invs[0]["invoice_number"])
            receive_date = inv.get("invoice_date", "") if inv else ""
            linked = [
                str(m["serial_number"])
                for m in machine.list_machines()
                if m.get("invoice_number") == invs[0]["invoice_number"]
            ]
            serials = ", ".join(linked)

        for item in items:
            prod = product.get_product(item["product_no"]) or {}
            mtype = _machine_type(None, prod.get("product_name"))
            if machine_type and machine_type != "All" and mtype != machine_type:
                continue
            qty = int(item["quantity"])
            unit = float(item["unit_price"])
            disposed = status == "Cancelled"
            rows.append(
                {
                    "po_number": f"{po['purchase_order_id']:05d}",
                    "purchase_order_id": po["purchase_order_id"],
                    "po_date": po_d.isoformat(),
                    "vendor_name": v["vendor_name"] if v else "",
                    "product_no": item["product_no"],
                    "product_name": prod.get("product_name", ""),
                    "machine_type": mtype,
                    "quantity": qty,
                    "unit_price": unit,
                    "total_price": qty * unit,
                    "serial_numbers": serials,
                    "receive_date": receive_date,
                    "po_status": status,
                    "disposal_date": po_d.isoformat() if disposed else "",
                    "disposal_reason": "Cancelled" if disposed else "",
                    "vendor_id": po["vendor_id"],
                }
            )
    rows.sort(key=lambda r: (r["po_date"], r["vendor_name"]))
    return rows


def build_performance_report(
    *,
    period_from: date,
    period_to: date,
    location_ids: list[int] | None,
    machine_type: Optional[str],
    threshold: float,
) -> tuple[list[dict[str, Any]], str | None]:
    warning = None
    period_days = (period_to - period_from).days + 1
    if period_days < MIN_DATA_DAYS_WARNING:
        warning = (
            "Insufficient data — use for reference only "
            f"(less than {MIN_DATA_DAYS_WARNING} days in range)."
        )

    rows: list[dict[str, Any]] = []
    today = date.today()

    for m in machine.list_machines():
        loc_id = m.get("location_id")
        if location_ids and loc_id not in location_ids:
            continue
        mtype = _machine_type(m.get("model_name"), m.get("machine_name"))
        if machine_type and machine_type != "All" and mtype != machine_type:
            continue
        loc = business_location.get_location(loc_id) if loc_id else None
        install_d = _installation_date(m["serial_number"], loc_id) or today
        days_installed = max((today - install_d).days, 1)

        if days_installed < MIN_EVALUATION_DAYS:
            perf_status = "New — evaluation pending"
            recommendation = "Keep"
            total_revenue = 0.0
        else:
            _, asset_val = _invoice_totals_for_machine(m["serial_number"])
            daily = asset_val / max(days_installed, 1) * 0.02
            total_revenue = round(daily * period_days, 2)
            rs_share = round(total_revenue * DEFAULT_RS_REVENUE_SHARE, 2)
            rev_per_day = round(total_revenue / max(period_days, 1), 2)
            repairs = _repair_count(m["serial_number"])
            repair_cost = repairs * REPAIR_COST_ESTIMATE

            if total_revenue < threshold:
                perf_status = "Low"
            elif total_revenue >= threshold * 2:
                perf_status = "High"
            else:
                perf_status = "Average"

            if repair_cost > 0 and total_revenue > 0 and repair_cost / total_revenue > REPAIR_TO_REVENUE_JUNK_RATIO:
                recommendation = "Junk"
            elif perf_status == "Low":
                recommendation = "Relocate"
            elif perf_status == "High":
                recommendation = "Keep"
            else:
                recommendation = "Keep"

            rows.append(
                {
                    "business_location": loc["location_name"] if loc else "—",
                    "machine_name": m.get("machine_name", ""),
                    "machine_type": mtype,
                    "serial_number": m["serial_number"],
                    "installation_date": install_d.isoformat(),
                    "total_revenue": total_revenue,
                    "rs_revenue_share": rs_share,
                    "revenue_per_day": rev_per_day,
                    "repair_count": repairs,
                    "total_repair_cost": repair_cost,
                    "location_history": _location_history_text(m["serial_number"]),
                    "performance_status": perf_status,
                    "recommendation": recommendation,
                    "highlight": perf_status == "Low",
                }
            )
            continue

        rows.append(
            {
                "business_location": loc["location_name"] if loc else "—",
                "machine_name": m.get("machine_name", ""),
                "machine_type": mtype,
                "serial_number": m["serial_number"],
                "installation_date": install_d.isoformat(),
                "total_revenue": 0.0,
                "rs_revenue_share": 0.0,
                "revenue_per_day": 0.0,
                "repair_count": _repair_count(m["serial_number"]),
                "total_repair_cost": 0.0,
                "location_history": _location_history_text(m["serial_number"]),
                "performance_status": perf_status,
                "recommendation": recommendation,
                "highlight": False,
            }
        )

    rows.sort(key=lambda r: (r["total_revenue"], r["serial_number"]))
    return rows, warning


def low_performance_at_location(serial_number: int, location_id: int, threshold: float) -> bool:
    """Used by move order screen (SCR-IN-02 warning)."""
    rows, _ = build_performance_report(
        period_from=date.today() - timedelta(days=365),
        period_to=date.today(),
        location_ids=[location_id],
        machine_type=None,
        threshold=threshold,
    )
    for r in rows:
        if r["serial_number"] == serial_number and r.get("performance_status") == "Low":
            return True
    return False
