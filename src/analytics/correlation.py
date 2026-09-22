# src/analytics/correlation.py
#
# Sprint 6 - Day 37: Correlation matrix heatmap.
#
# Pearson correlation of the 10 core KPIs (same set used in
# peer_percentiles) across all companies, latest year each.
# Saved as reports/correlation_heatmap.png using seaborn with
# annotations, per spec.
#
# Usage:
#   python -m src.analytics.correlation

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DB_PATH = Path("data/nifty100.db")
REPORTS_DIR = Path("reports")

KPI_COLUMNS = [
    "asset_turnover",
    "debt_to_equity",
    "eps_cagr_5yr",
    "free_cash_flow_cr",
    "interest_coverage",
    "net_profit_margin_pct",
    "pat_cagr_5yr",
    "return_on_capital_pct",
    "return_on_equity_pct",
    "revenue_cagr_5yr",
]


def load_latest_kpis(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cols = ", ".join(f"fr.{c}" for c in KPI_COLUMNS)
        query = f"""
            SELECT fr.company_id, {cols}
            FROM financial_ratios fr
            INNER JOIN (
                SELECT company_id, MAX(year) AS max_year
                FROM financial_ratios
                GROUP BY company_id
            ) latest
              ON fr.company_id = latest.company_id
             AND fr.year = latest.max_year
        """
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df


def main():
    df = load_latest_kpis()
    print(f"[correlation] Loaded {len(df)} companies.")

    corr = df[KPI_COLUMNS].corr(method="pearson")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(11, 9))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
    )
    plt.title("KPI Correlation Matrix (Pearson) - Latest Year, All Companies")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    out_path = REPORTS_DIR / "correlation_heatmap.png"
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"[correlation] Saved {out_path}")

    print()
    print("Top 10 |correlation| pairs (excluding self-pairs):")
    pairs = corr.where(~corr.isna())
    unstacked = pairs.abs().unstack()
    unstacked = unstacked[unstacked < 0.999]
    seen = set()
    rows = []
    for (a, b), v in unstacked.sort_values(ascending=False).items():
        key = tuple(sorted([a, b]))
        if key in seen:
            continue
        seen.add(key)
        rows.append((a, b, corr.loc[a, b]))
        if len(rows) >= 10:
            break
    for a, b, v in rows:
        print(f"  {a} <-> {b}: {v:.2f}")

    corr.to_csv("output/correlation_matrix.csv")
    print()
    print("[correlation] Saved output/correlation_matrix.csv")


if __name__ == "__main__":
    main()