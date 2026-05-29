"""Export helpers for report screens."""

from __future__ import annotations

from io import BytesIO

import pandas as pd


def dataframe_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Report") -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buf.getvalue()
