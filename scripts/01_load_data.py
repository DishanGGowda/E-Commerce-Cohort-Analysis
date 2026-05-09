"""
01_load_data.py — Load raw Excel file → SQLite.

Expected input : data/raw/salesdata.xlsx
Sheet name     : cleaned_online_retail
Output table   : sales_data (SQLite)
"""

import sqlite3
from pathlib import Path

import pandas as pd

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "data" / "raw" / "salesdata.xlsx"
DB_PATH  = ROOT / "data" / "ecommerce.db"

# ── Guard ──────────────────────────────────────────────────────────────────────
if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {RAW_FILE}\n"
        "Place salesdata.xlsx inside data/raw/ and re-run."
    )

# ── Load ───────────────────────────────────────────────────────────────────────
COLS = [
    "InvoiceNo", "StockCode", "Description",
    "Quantity",  "InvoiceDate", "UnitPrice",
    "CustomerID", "Country", "Revenue", "Month",
]

print(f"Loading {RAW_FILE.name} …")
df = pd.read_excel(
    RAW_FILE,
    sheet_name="cleaned_online_retail",
    usecols=COLS,
)

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"  Rows loaded      : {len(df):,}")
print(f"  Date range       : {df['InvoiceDate'].min().date()} → {df['InvoiceDate'].max().date()}")
print(f"  Unique customers : {df['CustomerID'].nunique():,}")
nulls = df.isnull().sum()
nulls = nulls[nulls > 0]
if not nulls.empty:
    print(f"  Null counts      :\n{nulls.to_string()}")

# ── Write to SQLite ────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
df.to_sql("sales_data", conn, if_exists="replace", index=False)
conn.close()
print(f"✓  Written to SQLite → sales_data  ({len(df):,} rows)")
