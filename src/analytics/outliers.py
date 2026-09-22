# src/analytics/outliers.py
#
# Sprint 6 - Day 37: Outlier detection.
#
# Computes a Z-score for each of the 10 core KPIs, within each
# company's broad_sector (not across the whole market - a high D/E
# is normal for banks but not for FMCG, for example). Flags any
# company-metric pair where |Z| > 3 and saves to
# output/outlier_report.csv.
#
# Usage:
#   python -m src.analytics.outliers

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/nifty100.db")
OUTPUT_DIR = Path("output")
Z_THRESHOLD = 3

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


def load_latest_kpis_with_sector(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        cols = ", ".join(f"fr.{c}" for c in KPI_COLUMNS)
        query = f"""
            SELECT fr.company_id, c.company_name, s.broad_sector, {cols}
            FROM financial_ratios fr
            INNER JOIN (
                SELECT company_id, MAX(year) AS max_year
                FROM financial_ratios
                GROUP BY company_id
            ) latest
              ON fr.company_id = latest.company_id
             AND fr.year = latest.max_year
            INNER JOIN companies c ON fr.company_id = c.id
            INNER JOIN sectors s ON fr.company_id = s.company_id
        """
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df


def compute_outliers(df):
    rows = []
    for metric in KPI_COLUMNS:
        grouped = df.groupby("broad_sector")[metric]
        sector_mean = grouped.transform("mean")
        sector_std = grouped.transform("std")
        z = (df[metric] - sector_mean) / sector_std
        flagged = z.abs() > Z_THRESHOLD
        for idx in df.index[flagged]:
            rows.append({
                "company_id": df.loc[idx, "company_id"],
                "company_name": df.loc[idx, "company_name"],
                "broad_sector": df.loc[idx, "broad_sector"],
                "metric": metric,
                "value": df.loc[idx, metric],
                "z_score": round(z.loc[idx], 2),
            })
    return pd.DataFrame(rows)


def main():
    df = load_latest_kpis_with_sector()
    print(f"[outliers] Loaded {len(df)} companies across {df['broad_sector'].nunique()} sectors.")

    outlier_df = compute_outliers(df)
    print(f"[outliers] Flagged {len(outlier_df)} company-metric pairs with |Z| > {Z_THRESHOLD}.")

    if not outlier_df.empty:
        outlier_df = outlier_df.sort_values("z_score", key=lambda s: s.abs(), ascending=False)
        print()
        print(outlier_df.to_string(index=False))

        companies_flagged = outlier_df["company_id"].nunique()
        print()
        print(f"[outliers] {companies_flagged} distinct companies have at least 1 flagged metric.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "outlier_report.csv"
    outlier_df.to_csv(out_path, index=False)
    print(f"[outliers] Saved {out_path}")


if __name__ == "__main__":
    main()