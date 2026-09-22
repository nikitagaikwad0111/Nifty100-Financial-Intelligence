# src/analytics/portfolio_stats.py
#
# Sprint 6 - Day 37: Portfolio statistics table.
#
# P10/P25/P50/P75/P90/Mean/Std for each of the 10 core KPIs across
# all companies (latest year each). Saved to output/portfolio_stats.csv.
# This is the same table the Day 40 /api/v1/portfolio/stats endpoint
# will serve.
#
# Usage:
#   python -m src.analytics.portfolio_stats

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB_PATH = Path("data/nifty100.db")
OUTPUT_DIR = Path("output")

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


def compute_portfolio_stats(df):
    rows = []
    for metric in KPI_COLUMNS:
        series = df[metric].dropna()
        rows.append({
            "metric": metric,
            "n": len(series),
            "p10": np.percentile(series, 10),
            "p25": np.percentile(series, 25),
            "p50": np.percentile(series, 50),
            "p75": np.percentile(series, 75),
            "p90": np.percentile(series, 90),
            "mean": series.mean(),
            "std": series.std(),
        })
    return pd.DataFrame(rows)


def main():
    df = load_latest_kpis()
    print(f"[portfolio_stats] Loaded {len(df)} companies.")

    stats_df = compute_portfolio_stats(df)
    stats_df = stats_df.round(2)

    print()
    print(stats_df.to_string(index=False))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "portfolio_stats.csv"
    stats_df.to_csv(out_path, index=False)
    print()
    print(f"[portfolio_stats] Saved {out_path}")


if __name__ == "__main__":
    main()