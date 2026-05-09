"""
06_survival_curve.py — Average cohort survival curve + PNG chart.

Input  : data/cohort/cohort_retention_pct.csv  (wide)
Output : data/cohort/cohort_survival_curve.csv
         outputs/cohort_survival_curve.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # headless
import matplotlib.pyplot as plt
import pandas as pd

ROOT       = Path(__file__).resolve().parent.parent
COHORT_DIR = ROOT / "data" / "cohort"
OUT_DIR    = ROOT / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

retention = pd.read_csv(COHORT_DIR / "cohort_retention_pct.csv", index_col=0)
retention.columns = retention.columns.astype(int)

# ── Average retention across all cohorts at each offset ───────────────────────
survival = retention.mean(axis=0).reset_index()
survival.columns = ["MonthOffset", "AvgRetentionPct"]
survival["AvgRetentionPct"] = survival["AvgRetentionPct"].round(2)

print("=== Cohort Survival Curve ===")
print(survival.to_string(index=False))

# ── Chart ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(
    survival["MonthOffset"], survival["AvgRetentionPct"],
    marker="o", linewidth=2, color="#1D9E75",
)
ax.fill_between(
    survival["MonthOffset"], survival["AvgRetentionPct"],
    alpha=0.15, color="#1D9E75",
)
ax.set_xlabel("Months Since First Purchase")
ax.set_ylabel("Average Retention %")
ax.set_title("Cohort Survival Curve — All Cohorts Average")
ax.set_ylim(0, 110)
ax.grid(True, alpha=0.3)
plt.tight_layout()

chart_path = OUT_DIR / "cohort_survival_curve.png"
plt.savefig(chart_path, dpi=150)
plt.close()

# ── Save ──────────────────────────────────────────────────────────────────────
survival.to_csv(COHORT_DIR / "cohort_survival_curve.csv", index=False)
print(f"✓  Survival curve saved  |  chart → {chart_path.name}")
