# src/analytics/clustering.py
#
# Sprint 6 - Day 36: KMeans clustering (5 clusters).
#
# Features (per project spec, adapted to actual schema):
#   return_on_equity_pct, debt_to_equity, revenue_cagr_5yr,
#   pat_cagr_5yr (substituted for fcf_cagr_5yr - no FCF CAGR column
#   exists in financial_ratios), operating_profit_margin_pct
#
# Schema notes (confirmed from live DB):
#   - financial_ratios.company_id, companies.id and sectors.company_id
#     are all TEXT ticker strings (e.g. ABB), not integer IDs.
#   - financial_ratios.year is TEXT in YYYY-MM format (e.g. 2016-03).
#     MAX(year) still works correctly since the format sorts the same
#     as a string as it would as a date.
#   - Sector lives in a separate sectors table (broad_sector column),
#     joined on company_id.
#
# Pipeline:
#   1. Pull latest-year financial_ratios joined to sectors.broad_sector
#   2. Impute missing values with the SECTOR median for each metric
#   3. StandardScaler to zero mean / unit variance
#   4. KMeans(n_clusters=5, random_state=42)
#   5. Elbow plot (inertia vs k=2..10) -> reports/elbow_plot.png
#   6. output/cluster_labels.csv with columns:
#      company_id, cluster_id (0-4), cluster_name, distance_from_centroid
#
# cluster_name is a placeholder (Cluster 0 .. Cluster 4) at this stage.
# Day 37 cluster_profile.py assigns the real archetype names.
#
# Usage:
#   python -m src.analytics.clustering

from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

DB_PATH = Path("data/nifty100.db")
REPORTS_DIR = Path("reports")
OUTPUT_DIR = Path("output")

N_CLUSTERS = 5
RANDOM_STATE = 42

CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
]

PLACEHOLDER_NAMES = {i: f"Cluster {i}" for i in range(N_CLUSTERS)}


def load_latest_ratios(db_path: Path = DB_PATH) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        cols = ", ".join(f"fr.{f}" for f in CLUSTER_FEATURES)
        query = f"""
            SELECT fr.company_id,
                   s.broad_sector,
                   {cols}
            FROM financial_ratios fr
            INNER JOIN (
                SELECT company_id, MAX(year) AS max_year
                FROM financial_ratios
                GROUP BY company_id
            ) latest
              ON fr.company_id = latest.company_id
             AND fr.year = latest.max_year
            INNER JOIN sectors s
              ON fr.company_id = s.company_id
        """
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    if df.empty:
        raise RuntimeError(
            "No rows returned - check financial_ratios and sectors "
            "company_id values line up."
        )
    return df


def impute_with_sector_median(df, features):
    df = df.copy()
    for feature in features:
        sector_median = df.groupby("broad_sector")[feature].transform("median")
        df[feature] = df[feature].fillna(sector_median)
        remaining_na = df[feature].isna()
        if remaining_na.any():
            global_median = df[feature].median()
            df.loc[remaining_na, feature] = global_median
            print(f"[clustering] {remaining_na.sum()} rows for {feature} had no sector median; used global median ({global_median:.3f}).")
    return df


def run_elbow_analysis(X_scaled, k_range=range(2, 11)):
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
    return inertias


def save_elbow_plot(k_range, inertias, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.plot(list(k_range), inertias, marker="o")
    plt.axvline(x=N_CLUSTERS, color="red", linestyle="--", alpha=0.6, label=f"k={N_CLUSTERS} (chosen)")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia (within-cluster sum of squares)")
    plt.title("Elbow Plot - KMeans Clustering")
    plt.xticks(list(k_range))
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"[clustering] Saved {out_path}")


def run_clustering(db_path=DB_PATH):
    df = load_latest_ratios(db_path)
    print(f"[clustering] Loaded {len(df)} companies (latest year each).")

    missing_before = df[CLUSTER_FEATURES].isna().sum()
    if missing_before.sum() > 0:
        print("[clustering] Missing values before imputation:")
        print(missing_before[missing_before > 0])

    df = impute_with_sector_median(df, CLUSTER_FEATURES)

    X = df[CLUSTER_FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    k_range = range(2, 11)
    inertias = run_elbow_analysis(X_scaled, k_range)
    save_elbow_plot(k_range, inertias, REPORTS_DIR / "elbow_plot.png")
    print(f"[clustering] Inertia by k: {dict(zip(k_range, [round(i, 1) for i in inertias]))}")
    print(f"[clustering] Confirm visually that k={N_CLUSTERS} sits near the elbow (reports/elbow_plot.png).")

    model = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    labels = model.fit_predict(X_scaled)

    all_distances = model.transform(X_scaled)
    distance_from_centroid = all_distances[np.arange(len(labels)), labels]

    result_df = pd.DataFrame({
        "company_id": df["company_id"],
        "cluster_id": labels,
        "cluster_name": [PLACEHOLDER_NAMES[c] for c in labels],
        "distance_from_centroid": distance_from_centroid,
    })

    print("")
    print("[clustering] Cluster sizes:")
    print(result_df["cluster_id"].value_counts().sort_index().to_string())

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "cluster_labels.csv"
    result_df.to_csv(out_path, index=False)
    print(f"[clustering] Saved {out_path}")

    n_companies = len(result_df)
    print(f"[clustering] {n_companies} companies received a cluster_id.")
    if n_companies != 92:
        print("[clustering] NOTE: this is not 92 - some companies may be missing financial_ratios or sectors rows. Cross-check before relying on acceptance gate AC-15.")

    return result_df


if __name__ == "__main__":
    run_clustering()