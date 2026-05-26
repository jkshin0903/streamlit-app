"""UI labels derived from table/column names (no underscores)."""


def col(name: str) -> str:
    """snake_case column name -> Title Case label, e.g. location_id -> Location Id."""
    return name.replace("_", " ").title()


def cols(names: list[str]) -> dict[str, str]:
    return {n: col(n) for n in names}


def req(name: str) -> str:
    return f"{col(name)} *"


# Tabs & actions
TAB_LIST = "List"
TAB_FORM = "Create / Edit"
TAB_HISTORY = "Contract History"
BTN_SAVE = "Save"
BTN_DELETE = "Delete"
BTN_CANCEL = "Cancel"
BTN_NEW = "New"
BTN_OPEN = "Open"
BTN_CONFIRM = "Confirm"
BTN_ADD_LINE = "+ Add Line Item"
BTN_REMOVE = "Remove"
BTN_EDIT_SELECTED = "Edit Selected"
BTN_NEW_MODE = "New Record Mode"
NONE_OPTION = "(none)"
MSG_SAVED = "Saved."
MSG_DELETED = "Deleted."
MSG_NO_ROWS = "No records yet."
MSG_SELECT_ROW = "Select a row from the list or click New."

# Home (main script) — sidebar label comes from the entry filename
HOME_TITLE = "Equipment And Procurement Management"
