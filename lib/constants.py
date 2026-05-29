"""Allowed enum values (stored in DB / mock)."""

LOCATION_TYPES = ["Warehouse", "Store", "Site"]
CONTRACT_STATUSES = ["Active", "Expired", "Terminated"]
MACHINE_STATUSES = ["Operating", "Repair", "Idle", "Retired"]

# Spec-aligned PO statuses (func spec SCR-IN-01)
PURCHASE_ORDER_STATUSES = ["Pending", "Received", "Cancelled"]
LEGACY_PURCHASE_ORDER_STATUSES = ["Ordered", "Confirmed", "Shipping", "Completed"]

ORDER_TYPES = ["Install", "Move", "Repair", "Retrieve"]
ORDER_STATUSES = ["Draft", "Pending", "In Progress", "Completed", "Cancelled"]
REQUEST_STATUSES = ["Pending", "Approved", "Rejected"]
INVOICE_STATUSES = ["Unpaid", "Paid", "Cancelled"]

# Report filters (SCR-RPT-01)
REPORT_MACHINE_STATUSES = [
    "Active",
    "In Warehouse",
    "Under Repair",
    "Disposed",
]
MACHINE_STATUS_TO_REPORT = {
    "Operating": "Active",
    "Idle": "In Warehouse",
    "Repair": "Under Repair",
    "Retired": "Disposed",
}
REPORT_MACHINE_TYPES = [
    "All",
    "Pinball",
    "Pool Table",
    "Jukebox",
    "Video Game",
    "Other",
]

DISPOSAL_REASONS = ["Junk", "Sold", "Stolen", "Fire", "Vandalism"]

ORDER_STATUS_COLORS = {
    "Draft": "gray",
    "Pending": "orange",
    "In Progress": "blue",
    "Completed": "green",
    "Cancelled": "red",
}

# Performance report (SCR-RPT-03)
DEFAULT_RS_REVENUE_SHARE = 0.5
REPAIR_COST_ESTIMATE = 500.0
MIN_EVALUATION_DAYS = 30
MIN_DATA_DAYS_WARNING = 90
REPAIR_TO_REVENUE_JUNK_RATIO = 0.5

MAX_PO_LINE_ITEMS = 20
MAX_MOVE_ORDER_LINES = 10
