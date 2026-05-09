"""
03_feature_engineering.py — Derive CohortMonth & CohortIndex.

Input  : sales_clean    (SQLite)
Output : sales_features (SQLite)  +  data/processed/sales_features.csv
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "ecommerce.db"
OUT_CSV = ROOT / "data" / "processed" / "sales_features.csv"

conn = sqlite3.connect(DB_PATH)
df   = pd.read_sql("SELECT * FROM sales_clean", conn)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

# ── Invoice month (Period) ─────────────────────────────────────────────────────
df["InvoiceMonth"] = df["InvoiceDate"].dt.to_period("M")

# ── First purchase month per customer = CohortMonth ───────────────────────────
cohort_map = (
    df.groupby("CustomerID")["InvoiceMonth"]
      .min()
      .reset_index()
      .rename(columns={"InvoiceMonth": "CohortMonth"})
)
df = df.merge(cohort_map, on="CustomerID", how="left")

# ── CohortIndex = months since first purchase ──────────────────────────────────
df["CohortIndex"] = (df["InvoiceMonth"] - df["CohortMonth"]).apply(lambda x: x.n)

print("Sample (first 8 rows):")
print(
    df[["CustomerID", "InvoiceMonth", "CohortMonth", "CohortIndex"]]
    .head(8)
    .to_string(index=False)
)
print(f"\n  Unique cohorts   : {df['CohortMonth'].nunique()}")
print(f"  Max CohortIndex  : {df['CohortIndex'].max()}")

# ── Serialise Period columns for SQLite ───────────────────────────────────────
df["InvoiceMonth"] = df["InvoiceMonth"].astype(str)
df["CohortMonth"]  = df["CohortMonth"].astype(str)

df.to_sql("sales_features", conn, if_exists="replace", index=False)
df.to_csv(OUT_CSV, index=False)
conn.close()
print(f"✓  Saved → sales_features  |  {OUT_CSV.name}")
