"""
04_cohort_matrix.py — Build cohort customer-count & retention % matrices.

Input  : sales_features (SQLite)
Output : data/cohort/cohort_count_matrix.csv
         data/cohort/cohort_retention_pct.csv   ← wide (archive)
         data/cohort/cohort_retention_long.csv  ← long (Power BI ready)
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT      = Path(__file__).resolve().parent.parent
DB_PATH   = ROOT / "data" / "ecommerce.db"
COHORT_DIR = ROOT / "data" / "cohort"
COHORT_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
df   = pd.read_sql("SELECT * FROM sales_features", conn)
conn.close()

# ── Count unique customers per cohort × CohortIndex ──────────────────────────
cohort_data = (
    df.groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
      .nunique()
      .reset_index()
      .rename(columns={"CustomerID": "Customers"})
)

# ── Wide count matrix ──────────────────────────────────────────────────────────
cohort_matrix = cohort_data.pivot_table(
    index="CohortMonth", columns="CohortIndex", values="Customers"
)

# ── Wide retention % matrix ────────────────────────────────────────────────────
cohort_size      = cohort_matrix.iloc[:, 0]
retention_matrix = cohort_matrix.divide(cohort_size, axis=0) * 100

# ── Long retention format (required for Power BI field mapping) ───────────────
retention_long = (
    retention_matrix
    .reset_index()
    .melt(id_vars="CohortMonth", var_name="CohortIndex", value_name="AvgRetentionPct")
    .dropna(subset=["AvgRetentionPct"])
)
retention_long["CohortIndex"]     = retention_long["CohortIndex"].astype(int)
retention_long["AvgRetentionPct"] = retention_long["AvgRetentionPct"].round(2)

print("=== Retention % Matrix (wide — first 5 cohorts) ===")
print(retention_matrix.round(1).iloc[:5].fillna("-").to_string())

print(f"\n  Retention long rows : {len(retention_long):,}")
print(retention_long.head(6).to_string(index=False))

# ── Save ───────────────────────────────────────────────────────────────────────
cohort_matrix.to_csv(COHORT_DIR / "cohort_count_matrix.csv")
retention_matrix.to_csv(COHORT_DIR / "cohort_retention_pct.csv")
retention_long.to_csv(COHORT_DIR / "cohort_retention_long.csv", index=False)
print("✓  Cohort matrices saved (wide + long format)")
