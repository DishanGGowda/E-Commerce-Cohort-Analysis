"""
12_cohort_rfm_join.py — Join cohort data with RFM segments.

Produces:
  SQLite tables : cohort_segment_map, cohort_seg_count, cohort_seg_revenue,
                  cohort_seg_clv, cohort_health_scores, cohort_seg_pct
  CSV files     : data/processed/cohort_rfm_enriched.csv
                  data/processed/cohort_health_scores.csv
  Chart         : outputs/cohort_segment_heatmap.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sqlite3

ROOT     = Path(__file__).resolve().parent.parent
DB_PATH  = ROOT / "data" / "ecommerce.db"
OUT_DIR  = ROOT / "outputs"
PROC_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

rfm = pd.read_sql(
    "SELECT CustomerID, Segment, SegmentTier, RFM_Score, CLV_Score, "
    "Monetary, Frequency, Recency FROM rfm_segments",
    conn,
)
features = pd.read_sql(
    "SELECT DISTINCT CustomerID, CohortMonth FROM sales_features",
    conn,
)

# ── Base join ──────────────────────────────────────────────────────────────────
enriched = features.merge(rfm, on="CustomerID", how="left")

# ── Matrix 1: customer count per cohort × segment ─────────────────────────────
m_count = (
    enriched.groupby(["CohortMonth", "Segment"])
    .size()
    .unstack(fill_value=0)
)

# ── Matrix 2: total revenue per cohort × segment ──────────────────────────────
m_revenue = (
    enriched.groupby(["CohortMonth", "Segment"])["Monetary"]
    .sum()
    .unstack(fill_value=0)
    .round(2)
)

# ── Matrix 3: avg CLV per cohort × segment ────────────────────────────────────
m_clv = (
    enriched.groupby(["CohortMonth", "Segment"])["CLV_Score"]
    .mean()
    .unstack(fill_value=0)
    .round(2)
)

# ── Matrix 4: segment % share within each cohort ─────────────────────────────
m_pct = m_count.div(m_count.sum(axis=1), axis=0) * 100

# ── Cohort health score ────────────────────────────────────────────────────────
HIGH_VALUE = ["Champions", "Loyal Customers"]

hv_ratio = (
    enriched.groupby("CohortMonth")
    .apply(lambda g: (g["Segment"].isin(HIGH_VALUE)).mean() * 100)
    .round(1)
    .reset_index()
)
hv_ratio.columns = ["CohortMonth", "HighValuePct"]

avg_rfm = (
    enriched.groupby("CohortMonth")["RFM_Score"]
    .mean()
    .round(2)
    .reset_index()
    .rename(columns={"RFM_Score": "AvgRFMScore"})
)

avg_clv = (
    enriched.groupby("CohortMonth")["CLV_Score"]
    .mean()
    .round(2)
    .reset_index()
    .rename(columns={"CLV_Score": "AvgCLVScore"})
)

cohort_health = (
    hv_ratio
    .merge(avg_rfm, on="CohortMonth")
    .merge(avg_clv, on="CohortMonth")
)
cohort_health["HealthGrade"] = pd.cut(
    cohort_health["HighValuePct"],
    bins=[0, 10, 20, 30, 100],
    labels=["D — Weak", "C — Fair", "B — Good", "A — Strong"],
)

print("=== Cohort Health Scores ===")
print(
    cohort_health.sort_values("HighValuePct", ascending=False)
    .to_string(index=False)
)

print("\n=== Segment % Distribution (first 5 cohorts) ===")
print(m_pct.round(1).iloc[:5].to_string())

# ── Visualisation: segment % heatmap ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 6))
sns.heatmap(
    m_pct.round(1), annot=True, fmt=".1f",
    cmap="RdYlGn", ax=ax, linewidths=0.4,
    cbar_kws={"label": "% of Cohort"},
)
ax.set_title(
    "Segment % Distribution within Each Acquisition Cohort",
    fontsize=12, fontweight="bold",
)
ax.set_xlabel("RFM Segment")
ax.set_ylabel("Cohort Month")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
chart_path = OUT_DIR / "cohort_segment_heatmap.png"
plt.savefig(chart_path, dpi=150)
plt.close()

# ── Write all tables to SQLite ────────────────────────────────────────────────
tables = {
    "cohort_segment_map":   enriched,
    "cohort_seg_count":     m_count.reset_index(),
    "cohort_seg_revenue":   m_revenue.reset_index(),
    "cohort_seg_clv":       m_clv.reset_index(),
    "cohort_health_scores": cohort_health,
    "cohort_seg_pct":       m_pct.reset_index(),
}

for tbl, df_out in tables.items():
    df_out.to_sql(tbl, conn, if_exists="replace", index=False)
    print(f"  ✓  {tbl:<25}  {len(df_out):>5} rows")

# ── Write CSVs ─────────────────────────────────────────────────────────────────
enriched.to_csv(PROC_DIR / "cohort_rfm_enriched.csv", index=False)
cohort_health.to_csv(PROC_DIR / "cohort_health_scores.csv", index=False)

conn.close()
print(f"\n✓  6 cohort×RFM tables written  |  chart → {chart_path.name}")
