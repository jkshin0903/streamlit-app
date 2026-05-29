"""Purchase order printable document (HTML for print / fax workflow)."""

from __future__ import annotations

from datetime import date
from typing import Any

from lib import repository
from lib.labels import col


def format_po_number(po_id: int) -> str:
    return f"{po_id:05d}"


def build_po_html(header: dict[str, Any], items: list[dict[str, Any]]) -> str:
    vendor = repository.get_vendor(header["vendor_id"]) or {}
    po_date = header.get("purchase_order_date", "")
    lines_html = ""
    total = 0.0
    for item in items:
        prod = repository.get_product(item["product_no"]) or {}
        qty = int(item["quantity"])
        unit = float(item["unit_price"])
        line_total = qty * unit
        total += line_total
        lines_html += f"""
        <tr>
          <td>{item['product_no']}</td>
          <td>{prod.get('product_name', '')}</td>
          <td style="text-align:right">{qty}</td>
          <td style="text-align:right">${unit:,.2f}</td>
          <td style="text-align:right">${line_total:,.2f}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>PO {format_po_number(header['purchase_order_id'])}</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 2em; }}
  h1 {{ font-size: 1.4em; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
  th, td {{ border: 1px solid #ccc; padding: 6px; }}
  th {{ background: #f0f0f0; }}
</style></head><body>
<h1>Purchase Order #{format_po_number(header['purchase_order_id'])}</h1>
<p><b>{col('purchase_order_date')}:</b> {po_date}</p>
<p><b>{col('vendor_name')}:</b> {vendor.get('vendor_name', '')}<br>
{vendor.get('address', '')}<br>
Phone: {vendor.get('phone', '')} · Fax: {vendor.get('fax', '') or '—'}</p>
<table>
  <thead><tr>
    <th>{col('product_no')}</th><th>{col('product_name')}</th>
    <th>{col('quantity')}</th><th>{col('unit_price')}</th><th>Line Total</th>
  </tr></thead>
  <tbody>{lines_html}</tbody>
  <tfoot><tr><td colspan="4" style="text-align:right"><b>Total</b></td>
  <td style="text-align:right"><b>${total:,.2f}</b></td></tr></tfoot>
</table>
<p><b>{col('purchase_order_status')}:</b> {header.get('purchase_order_status', '')}</p>
</body></html>"""
