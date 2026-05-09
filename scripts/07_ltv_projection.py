"""
07_ltv_projection.py — Cumulative 12-month LTV projection per cohort.

Input  : data/cohort/cohort_arpu_matrix.csv
Output : data/cohort/cohort_ltv_cumulative.csv
         data/cohort/cohort_ltv_summary.csv   ← Power BI ready (LTV bar chart)
"""

from pathlib import Path

import pandas as pd

ROOT       = Path(__file__).resolve().parent.parent
COHORT_DIR = ROOT / "data" / "cohort"

arpu = pd.read_csv(COHORT_DIR / "cohort_arpu_matrix.csv", index_col=0)
arpu.columns = arpu.columns.astype(int)

# ── Cumulative LTV: running sum of ARPU across month offsets ─────────────────
ltv_cumulative = arpu.cumsum(axis=1)

# ── 12-month LTV per cohort: highest cumulative value observed ────────────────
ltv_summary = (
    ltv_cumulative.max(axis=1)
    .reset_index()
    .rename(columns={ltv_cumulative.max(axis=1).index.name: "CohortMonth", 0: "LTV_12M"})
)
# Rename safely regardless of index name
ltv_summary.columns = ["CohortMonth", "LTV_12M"]
ltv_summary["LTV_12M"] = ltv_summary["LTV_12M"].round(2)
ltv_summary = ltv_summary.sort_values("LTV_12M", ascending=False)

print("=== 12-Month LTV by Cohort — £ per customer ===")
print(ltv_summary.to_string(index=False))

# ── Save ──────────────────────────────────────────────────────────────────────
ltv_cumulative.to_csv(COHORT_DIR / "cohort_ltv_cumulative.csv")
ltv_summary.to_csv(COHORT_DIR / "cohort_ltv_summary.csv", index=False)
print("✓  LTV files saved")
