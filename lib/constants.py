"""Allowed enum values (stored in DB / mock)."""

LOCATION_TYPES = ["Warehouse", "Store", "Site"]
CONTRACT_STATUSES = ["Active", "Expired", "Terminated"]
MACHINE_STATUSES = ["Operating", "Repair", "Idle", "Retired"]
ORDER_TYPES = ["Install", "Move", "Repair", "Retrieve"]
ORDER_STATUSES = ["Pending", "In Progress", "Completed", "Cancelled"]
REQUEST_STATUSES = ["Pending", "Approved", "Rejected"]
PURCHASE_ORDER_STATUSES = ["Ordered", "Confirmed", "Shipping", "Completed"]
INVOICE_STATUSES = ["Unpaid", "Paid", "Cancelled"]

ORDER_STATUS_COLORS = {
    "Pending": "orange",
    "In Progress": "blue",
    "Completed": "green",
    "Cancelled": "red",
}
