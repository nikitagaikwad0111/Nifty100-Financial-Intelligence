# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import numpy as np
import os
import sys
sys.path.insert(0, os.path.abspath("."))

DB_PATH = "data/nifty100.db"

# 10 metrics to rank — with direction (higher = better or lower = better)
PEER_METRICS = {
    "return_on_equity_pct":      "higher",
    "return_on_capital_pct":     "higher",
    "net_profit_margin_pct":     "higher",
    "debt_to_equity":            "lower",
    "free_cash_flow_cr":         "higher",
    "pat_cagr_5yr":              "higher",
    "revenue_cagr_5yr":          "higher",
    "eps_cagr_5yr":              "higher",
    "interest_coverage":         "higher",
    "asset_turnover":            "higher",
}


def load_peer_groups() -> pd.DataFrame:
    """Load peer groups from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM peer_groups", conn)
    conn.close()
    return df


def load_latest_ratios() -> pd.DataFrame:
    """Load latest year financial ratios for all companies."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT fr.*, c.company_name, s.broad_sector
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s ON fr.company_id = s.company_id
        WHERE fr.year = (
            SELECT MAX(year) FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id
            AND fr2.year LIKE '%-03'
        )
    """, conn)
    conn.close()
    return df


def compute_percentile_rank(series: pd.Series,
                             direction: str) -> pd.Series:
    """
    Compute percentile rank for a series.
    direction='higher' means higher value = higher rank.
    direction='lower' means lower value = higher rank (e.g. D/E).
    Returns rank between 0 and 1.
    """
    if direction == "lower":
        # Invert: lower D/E = better = higher percentile
        return 1 - series.rank(pct=True, na_option="bottom")
    else:
        return series.rank(pct=True, na_option="bottom")


def compute_peer_percentiles() -> pd.DataFrame:
    """
    Compute percentile ranks for all companies in all peer groups.
    Returns DataFrame with columns:
    company_id, peer_group_name, metric, value,
    percentile_rank, year, is_benchmark
    """
    peer_groups = load_peer_groups()
    ratios = load_latest_ratios()

    all_rows = []

    for group_name in peer_groups["peer_group_name"].unique():
        group_df = peer_groups[
            peer_groups["peer_group_name"] == group_name]
        member_ids = group_df["company_id"].tolist()
        benchmark_ids = group_df[
            group_df["is_benchmark"] == 1]["company_id"].tolist()

        # Filter ratios for this peer group
        group_ratios = ratios[
            ratios["company_id"].isin(member_ids)].copy()

        if group_ratios.empty:
            continue

        # Compute percentile rank for each metric
        for metric, direction in PEER_METRICS.items():
            if metric not in group_ratios.columns:
                continue

            metric_series = pd.to_numeric(
                group_ratios[metric], errors="coerce")
            pct_ranks = compute_percentile_rank(
                metric_series, direction)

            for idx, row in group_ratios.iterrows():
                company_id = row["company_id"]
                value = row.get(metric)
                pct_rank = pct_ranks.get(idx)
                year = row.get("year")
                is_benchmark = 1 if company_id in benchmark_ids else 0

                all_rows.append({
                    "company_id":       company_id,
                    "peer_group_name":  group_name,
                    "metric":           metric,
                    "value":            value,
                    "percentile_rank":  round(float(pct_rank), 4)
                                        if pct_rank is not None
                                        else None,
                    "year":             year,
                    "is_benchmark":     is_benchmark,
                })

    result_df = pd.DataFrame(all_rows)
    return result_df


def save_peer_percentiles(df: pd.DataFrame) -> None:
    """Save peer percentiles to SQLite."""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql("peer_percentiles", conn,
              if_exists="replace", index=False)
    conn.close()


def get_peer_summary(group_name: str) -> pd.DataFrame:
    """
    Get a summary table for one peer group showing
    all companies with their percentile ranks per metric.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"""
        SELECT company_id, metric,
               value, percentile_rank, is_benchmark
        FROM peer_percentiles
        WHERE peer_group_name = ?
        ORDER BY metric, percentile_rank DESC
    """, conn, params=[group_name])
    conn.close()
    return df


def get_company_peer_rank(company_id: str) -> pd.DataFrame:
    """Get all peer group rankings for one company."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT peer_group_name, metric,
               value, percentile_rank
        FROM peer_percentiles
        WHERE company_id = ?
        ORDER BY peer_group_name, percentile_rank DESC
    """, conn, params=[company_id])
    conn.close()
    return df


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Computing peer percentile rankings...")
    df = compute_peer_percentiles()
    print(f"Total rows computed: {len(df)}")
    print(f"Peer groups: {df['peer_group_name'].nunique()}")
    print(f"Companies: {df['company_id'].nunique()}")

    print("\nSaving to SQLite...")
    save_peer_percentiles(df)
    print("peer_percentiles table saved!")

    # Spot check IT Services group
    print("\n--- IT Services Peer Group (ROE ranking) ---")
    it = df[
        (df["peer_group_name"] == "IT Services") &
        (df["metric"] == "return_on_equity_pct")
    ].sort_values("percentile_rank", ascending=False)
    print(it[["company_id", "value",
               "percentile_rank", "is_benchmark"]].to_string())

    # Spot check FMCG group
    print("\n--- FMCG Peer Group (Revenue CAGR ranking) ---")
    fmcg = df[
        (df["peer_group_name"] == "FMCG") &
        (df["metric"] == "revenue_cagr_5yr")
    ].sort_values("percentile_rank", ascending=False)
    print(fmcg[["company_id", "value",
                 "percentile_rank", "is_benchmark"]].to_string())
