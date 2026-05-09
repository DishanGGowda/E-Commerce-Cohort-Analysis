"""
09_cohort_sql_views.py — Load all cohort CSVs into SQLite tables.

The 7 tables written here map directly to the Power BI data source:

  Table name            Source file                      Power BI visual
  ──────────────────    ──────────────────────────────   ────────────────────
  cohort_retention      cohort_retention_long.csv        Retention heatmap
  cohort_revenue        cohort_revenue_long.csv          Revenue analysis
  cohort_ltv            cohort_ltv_summary.csv           LTV bar chart
  cohort_survival       cohort_survival_curve.csv        Survival line chart
  cohort_anomalies      cohort_anomalies.csv             Anomaly table
  cohort_segment_map    written by 12_cohort_rfm_join    Cross-filtering
  rfm_segments          written by 11_segmentation       Donut chart
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT       = Path(__file__).resolve().parent.parent
DB_PATH    = ROOT / "data" / "ecommerce.db"
COHORT_DIR = ROOT / "data" / "cohort"

# ── File → SQLite table mapping ───────────────────────────────────────────────
# cohort_segment_map and rfm_segments are populated by later scripts;
# they are excluded here and loaded from SQLite directly in those scripts.
FILES = {
    "cohort_retention": COHORT_DIR / "cohort_retention_long.csv",
    "cohort_revenue":   COHORT_DIR / "cohort_revenue_long.csv",
    "cohort_ltv":       COHORT_DIR / "cohort_ltv_summary.csv",
    "cohort_survival":  COHORT_DIR / "cohort_survival_curve.csv",
    "cohort_anomalies": COHORT_DIR / "cohort_anomalies.csv",
}

conn = sqlite3.connect(DB_PATH)

for table_name, filepath in FILES.items():
    if not filepath.exists():
        print(f"  ⚠  Missing: {filepath.name} — skipping {table_name}")
        continue
    df = pd.read_csv(filepath)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"  ✓  {table_name:<25}  {len(df):>5} rows  ←  {filepath.name}")

conn.close()
print("\n✓  All cohort tables loaded into SQLite")
print("   (cohort_segment_map and rfm_segments are written by scripts 11 & 12)")
