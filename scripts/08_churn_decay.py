"""
08_churn_decay.py — Fit exponential decay model; flag anomalous cohort drops.

Input  : data/cohort/cohort_retention_pct.csv
         data/cohort/cohort_survival_curve.csv
Output : data/cohort/cohort_anomalies.csv   ← Power BI anomaly table

Columns produced:
  CohortMonth | MonthOffset | ActualRetention | ExpectedRetention | Gap
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

ROOT       = Path(__file__).resolve().parent.parent
COHORT_DIR = ROOT / "data" / "cohort"

retention = pd.read_csv(COHORT_DIR / "cohort_retention_pct.csv", index_col=0)
retention.columns = retention.columns.astype(int)

survival = pd.read_csv(COHORT_DIR / "cohort_survival_curve.csv")
x = survival["MonthOffset"].values
y = survival["AvgRetentionPct"].values / 100   # scale to [0, 1]


# ── Exponential decay model: f(t) = a * exp(-b * t) + c ──────────────────────
def decay(t, a, b, c):
    return a * np.exp(-b * t) + c


# Fit on month offsets 1+ (skip month 0 = 100% by definition)
popt, _ = curve_fit(
    decay, x[1:], y[1:],
    p0=[0.8, 0.5, 0.05],
    bounds=([0, 0, 0], [1, 10, 0.5]),
    maxfev=5000,
)
a_fit, b_fit, c_fit = popt
print(f"  Decay model: a={a_fit:.3f}  b={b_fit:.3f}  c={c_fit:.3f}")

# ── Anomaly detection ─────────────────────────────────────────────────────────
# Flag any cohort/offset where actual retention falls >10 pp below expectation.
THRESHOLD = 10.0

anomalies = []
for cohort in retention.index:
    row = retention.loc[cohort].dropna()
    for idx in row.index[1:]:                        # skip offset 0
        expected = decay(idx, *popt) * 100
        actual   = row[idx]
        gap      = actual - expected
        if gap < -THRESHOLD:
            anomalies.append({
                "CohortMonth":        cohort,
                "MonthOffset":        int(idx),
                "ActualRetention":    round(actual,   1),
                "ExpectedRetention":  round(expected, 1),
                "Gap":                round(gap,      1),
            })

anomaly_df = pd.DataFrame(anomalies)

if anomaly_df.empty:
    print(
        f"  0 anomalies at threshold={THRESHOLD}. "
        "Lowering to 5 pp and retrying …"
    )
    THRESHOLD = 5.0
    for cohort in retention.index:
        row = retention.loc[cohort].dropna()
        for idx in row.index[1:]:
            expected = decay(idx, *popt) * 100
            actual   = row[idx]
            gap      = actual - expected
            if gap < -THRESHOLD:
                anomalies.append({
                    "CohortMonth":       cohort,
                    "MonthOffset":       int(idx),
                    "ActualRetention":   round(actual,   1),
                    "ExpectedRetention": round(expected, 1),
                    "Gap":               round(gap,      1),
                })
    anomaly_df = pd.DataFrame(anomalies)

anomaly_df = anomaly_df.sort_values("Gap").reset_index(drop=True)

print("=== Underperforming Cohort Drops ===")
print(anomaly_df.head(10).to_string(index=False))

# ── Save ──────────────────────────────────────────────────────────────────────
anomaly_df.to_csv(COHORT_DIR / "cohort_anomalies.csv", index=False)
print(f"\n✓  {len(anomaly_df)} anomalous drops detected and saved")
print(f"   Columns: {list(anomaly_df.columns)}")
