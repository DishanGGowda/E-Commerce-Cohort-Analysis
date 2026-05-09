"""
11_segmentation.py — Assign customers to 11 RFM segments.

Input  : rfm_scores (SQLite)
Output : rfm_segments (SQLite)  +  data/processed/rfm_segments.csv
                                    data/processed/rfm_segment_summary.csv
         outputs/rfm_segment_profile.png

Segment rules mirror the standard Klaviyo / RFM grid used in production e-commerce.
All comparison operators are explicit — no HTML-encoded fragments.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import sqlite3

ROOT     = Path(__file__).resolve().parent.parent
DB_PATH  = ROOT / "data" / "ecommerce.db"
OUT_DIR  = ROOT / "outputs"
PROC_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
rfm  = pd.read_sql("SELECT * FROM rfm_scores", conn)


# ── 11-Segment assignment ──────────────────────────────────────────────────────
def assign_segment(r: int, f: int, m: int) -> str:
    fm = (f + m) / 2
    if   r >= 4 and fm >= 4:                   return "Champions"
    elif r >= 2 and fm >= 3 and r < 5:         return "Loyal Customers"
    elif r >= 3 and fm >= 1 and fm < 3:        return "Potential Loyalists"
    elif r >= 4 and fm < 2:                    return "New Customers"
    elif r == 3 and fm < 2:                    return "Promising"
    elif r == 3 and fm >= 3:                   return "Need Attention"
    elif r == 2 and fm >= 3:                   return "About to Sleep"
    elif r < 3  and fm >= 3:                   return "At Risk"
    elif r <= 1 and f >= 4 and m >= 4:         return "Can't Lose Them"
    elif r < 2  and fm < 3:                    return "Hibernating"
    else:                                       return "Lost"


rfm["Segment"] = rfm.apply(
    lambda row: assign_segment(row["R_score"], row["F_score"], row["M_score"]),
    axis=1,
)

# ── Priority tier ──────────────────────────────────────────────────────────────
TIER_MAP = {
    "Champions": 1,            "Loyal Customers": 1,
    "Can't Lose Them": 2,      "At Risk": 2,          "Potential Loyalists": 2,
    "Need Attention": 3,       "About to Sleep": 3,   "Promising": 3,
    "New Customers": 3,
    "Hibernating": 4,           "Lost": 4,
}
rfm["SegmentTier"] = rfm["Segment"].map(TIER_MAP)

# ── CLV score: time-discounted value estimate ─────────────────────────────────
rfm["CLV_Score"] = (
    rfm["Monetary"] * rfm["Frequency"] * (1 / (1 + rfm["Recency"] / 365))
).round(2)

# ── Segment summary ────────────────────────────────────────────────────────────
summary = (
    rfm.groupby("Segment")
       .agg(
           CustomerCount=("CustomerID", "count"),
           AvgRecency   =("Recency",    "mean"),
           AvgFrequency =("Frequency",  "mean"),
           AvgMonetary  =("Monetary",   "mean"),
           TotalRevenue =("Monetary",   "sum"),
           AvgCLVScore  =("CLV_Score",  "mean"),
           AvgRFMScore  =("RFM_Score",  "mean"),
           Tier         =("SegmentTier","first"),
       )
       .round(2)
       .reset_index()
)
total_rev = summary["TotalRevenue"].sum()
summary["RevenuePct"] = (summary["TotalRevenue"] / total_rev * 100).round(1)

print("=== Segment Profile (sorted by Revenue) ===")
print(
    summary.sort_values("TotalRevenue", ascending=False)
    [["Segment", "Tier", "CustomerCount", "RevenuePct", "AvgMonetary", "AvgCLVScore"]]
    .to_string(index=False)
)

# ── Visualisation ──────────────────────────────────────────────────────────────
COLORS = {
    "Champions":           "#04342C",
    "Loyal Customers":     "#1D9E75",
    "Potential Loyalists": "#5DCAA5",
    "New Customers":       "#9FE1CB",
    "Promising":           "#B5D4F4",
    "Need Attention":      "#FAC775",
    "About to Sleep":      "#EF9F27",
    "At Risk":             "#BA7517",
    "Can't Lose Them":    "#F7C1C1",
    "Hibernating":         "#B4B2A9",
    "Lost":                "#791F1F",
}

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

cnt = rfm["Segment"].value_counts()
axes[0].barh(cnt.index, cnt.values, color=[COLORS.get(s, "#888") for s in cnt.index])
axes[0].set_title("Customer Count by Segment", fontsize=12, fontweight="bold")
axes[0].set_xlabel("Customers")
axes[0].grid(True, alpha=0.3, axis="x")

rev = rfm.groupby("Segment")["Monetary"].sum().sort_values(ascending=False)
axes[1].barh(rev.index, rev.values, color=[COLORS.get(s, "#888") for s in rev.index])
axes[1].set_title("Total Revenue by Segment (£)", fontsize=12, fontweight="bold")
axes[1].set_xlabel("Revenue (£)")
axes[1].grid(True, alpha=0.3, axis="x")

plt.tight_layout()
chart_path = OUT_DIR / "rfm_segment_profile.png"
plt.savefig(chart_path, dpi=150)
plt.close()

# ── Save ──────────────────────────────────────────────────────────────────────
rfm.to_sql("rfm_segments", conn, if_exists="replace", index=False)
rfm.to_csv(PROC_DIR / "rfm_segments.csv", index=False)
summary.to_csv(PROC_DIR / "rfm_segment_summary.csv", index=False)
conn.close()
print(f"\n✓  Segmentation complete  |  {rfm['Segment'].nunique()} segments  "
      f"|  {len(rfm):,} customers  |  chart → {chart_path.name}")
