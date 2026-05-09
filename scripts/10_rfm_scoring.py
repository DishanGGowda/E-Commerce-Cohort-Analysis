"""
10_rfm_scoring.py — Compute RFM scores for every customer.

Input  : sales_features (SQLite)
Output : rfm_scores (SQLite)  +  data/processed/rfm_scores.csv
         outputs/rfm_distribution.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sqlite3

ROOT       = Path(__file__).resolve().parent.parent
DB_PATH    = ROOT / "data" / "ecommerce.db"
OUT_DIR    = ROOT / "outputs"
PROC_DIR   = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
df   = pd.read_sql("SELECT * FROM sales_features", conn)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

SNAPSHOT = pd.Timestamp("2011-12-31")

# ── Aggregate RFM metrics ──────────────────────────────────────────────────────
rfm = (
    df.groupby("CustomerID")
      .agg(
          Recency       =("InvoiceDate", lambda x: (SNAPSHOT - x.max()).days),
          Frequency     =("InvoiceNo",   "nunique"),
          Monetary      =("Revenue",     "sum"),
          AvgOrderValue =("Revenue",     "mean"),
          TxnSpread     =("InvoiceDate", lambda x: (x.max() - x.min()).days),
      )
      .reset_index()
)

# ── Monetary outlier cap at 99th percentile ───────────────────────────────────
m99 = rfm["Monetary"].quantile(0.99)
rfm["Monetary_capped"] = rfm["Monetary"].clip(upper=m99)
capped_n = (rfm["Monetary"] > m99).sum()
print(f"  Monetary 99th pct cap : £{m99:,.0f}  |  customers capped: {capped_n}")

# ── Quintile scoring ───────────────────────────────────────────────────────────
# Recency  : lower days  = better → label 5
rfm["R_score"] = pd.qcut(
    rfm["Recency"], q=5, labels=[5, 4, 3, 2, 1], duplicates="drop"
).astype(int)

# Frequency: rank first to handle ties
rfm["F_score"] = pd.qcut(
    rfm["Frequency"].rank(method="first"), q=5,
    labels=[1, 2, 3, 4, 5], duplicates="drop"
).astype(int)

rfm["M_score"] = pd.qcut(
    rfm["Monetary_capped"].rank(method="first"), q=5,
    labels=[1, 2, 3, 4, 5], duplicates="drop"
).astype(int)

# ── Composite scores ───────────────────────────────────────────────────────────
rfm["RFM_Cell"] = (
    rfm["R_score"].astype(str)
    + rfm["F_score"].astype(str)
    + rfm["M_score"].astype(str)
)
rfm["RFM_Score"] = (
    rfm["R_score"] * 0.35 + rfm["F_score"] * 0.35 + rfm["M_score"] * 0.30
).round(3)
rfm["FM_Score"] = ((rfm["F_score"] + rfm["M_score"]) / 2).round(2)

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n=== RFM Metric Distribution ===")
print(rfm[["Recency", "Frequency", "Monetary", "RFM_Score"]].describe().round(2))
print(f"\n  Unique customers   : {len(rfm):,}")
print(f"  Unique RFM cells   : {rfm['RFM_Cell'].nunique()} of 125")
print("\nTop 10 most common RFM cells:")
print(rfm["RFM_Cell"].value_counts().head(10).to_string())

# ── Visualisation ─────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

pivot = rfm.pivot_table(
    values="M_score", index="R_score", columns="F_score", aggfunc="mean"
)
sns.heatmap(
    pivot, annot=True, fmt=".1f", cmap="YlOrRd",
    ax=axes[0], linewidths=0.4, cbar_kws={"label": "Avg M Score"},
)
axes[0].set_title("Avg Monetary Score — R vs F Grid")
axes[0].set_xlabel("Frequency Score")
axes[0].set_ylabel("Recency Score")

sc = axes[1].scatter(
    rfm["Recency"], np.log1p(rfm["Frequency"]),
    c=rfm["RFM_Score"], cmap="RdYlGn", alpha=0.45, s=18,
)
plt.colorbar(sc, ax=axes[1], label="RFM Score")
axes[1].set_xlabel("Recency (days since last purchase)")
axes[1].set_ylabel("log(1 + Frequency)")
axes[1].set_title("Customer Cloud — Recency vs Frequency")
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
chart_path = OUT_DIR / "rfm_distribution.png"
plt.savefig(chart_path, dpi=150)
plt.close()

# ── Save ──────────────────────────────────────────────────────────────────────
rfm.to_sql("rfm_scores", conn, if_exists="replace", index=False)
rfm.to_csv(PROC_DIR / "rfm_scores.csv", index=False)
conn.close()
print(f"\n✓  RFM scoring complete  |  chart → {chart_path.name}")
