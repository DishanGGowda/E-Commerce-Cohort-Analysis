"""
05_cohort_revenue.py — Revenue & ARPU per cohort × period.

Input  : sales_features (SQLite)
Output : data/cohort/cohort_revenue_matrix.csv
         data/cohort/cohort_arpu_matrix.csv
         data/cohort/cohort_revenue_long.csv   ← Power BI ready
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT       = Path(__file__).resolve().parent.parent
DB_PATH    = ROOT / "data" / "ecommerce.db"
COHORT_DIR = ROOT / "data" / "cohort"
COHORT_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
df   = pd.read_sql("SELECT * FROM sales_features", conn)
conn.close()

# ── Aggregate revenue & customer count ────────────────────────────────────────
rev_data = (
    df.groupby(["CohortMonth", "CohortIndex"])["Revenue"]
      .sum()
      .reset_index()
)

cust_data = (
    df.groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
      .nunique()
      .reset_index()
      .rename(columns={"CustomerID": "Customers"})
)

merged = rev_data.merge(cust_data, on=["CohortMonth", "CohortIndex"])
merged["ARPU"] = (merged["Revenue"] / merged["Customers"]).round(2)

# ── Wide matrices ──────────────────────────────────────────────────────────────
rev_matrix  = merged.pivot_table(index="CohortMonth", columns="CohortIndex", values="Revenue")
arpu_matrix = merged.pivot_table(index="CohortMonth", columns="CohortIndex", values="ARPU")

print("=== ARPU by Cohort — £ (first 5 cohorts) ===")
print(arpu_matrix.round(2).iloc[:5].fillna("-").to_string())

# ── Save ───────────────────────────────────────────────────────────────────────
rev_matrix.to_csv(COHORT_DIR / "cohort_revenue_matrix.csv")
arpu_matrix.to_csv(COHORT_DIR / "cohort_arpu_matrix.csv")
merged.to_csv(COHORT_DIR / "cohort_revenue_long.csv", index=False)
print(f"✓  Revenue matrices saved  |  long rows: {len(merged):,}")
