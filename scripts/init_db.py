"""
init_db.py — Initialise the SQLite database schema.
Run once before 01_load_data.py.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ecommerce.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_data (
    InvoiceNo   TEXT,
    StockCode   TEXT,
    Description TEXT,
    Quantity    INTEGER,
    InvoiceDate TEXT,
    UnitPrice   REAL,
    CustomerID  INTEGER,
    Country     TEXT,
    Revenue     REAL,
    Month       TEXT
)
""")

conn.commit()
conn.close()
print(f"✓  Database initialised: {DB_PATH}")
