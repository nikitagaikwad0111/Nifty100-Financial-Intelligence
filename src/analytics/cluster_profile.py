# src/analytics/cluster_profile.py
#
# Sprint 6 - Day 37: Cluster Profiling & Naming.
#
# Reads output/cluster_labels.csv (from Day 36 clustering.py), joins back
# to financial_ratios for the same clustering features, computes
# mean/median per cluster, and auto-suggests one of the 5 archetype
# names based on each cluster's quality/growth profile:
#
#   High-Quality Compounders, Defensive Dividend Payers,
#   Value Cyclicals, Distressed or Turnaround, Emerging Growth
#
# Prints sample companies per cluster for manual review - edit
# MANUAL_OVERRIDE below if a name does not fit once you have looked
# at which companies actually landed in each cluster. Rewrites
# output/cluster_labels.csv with the final names.
#
# Usage:
#   python -m src.analytics.cluster_profile

import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path("data/nifty100.db")
CLUSTER_LABELS_PATH = Path("output/cluster_labels.csv")

CLUSTER_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin_pct",
]

# Edit this if the auto-suggested name for a cluster ID does not match
# reality once you have reviewed the printed profile, e.g.:
# MANUAL_OVERRIDE = {0: "Value Cyclicals", 1: "Emerging Growth"}
MANUAL_OVERRIDE = {
    1: "Financial Services (High Structural Leverage)",
    2: "Outlier / Data Anomaly - Needs Review",
}


def load_cluster_data():
    labels_df = pd.read_csv(CLUSTER_LABELS_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        cols = ", ".join(f"fr.{f}" for f in CLUSTER_FEATURES)
        query = (
            "SELECT fr.company_id, c.company_name, " + cols + " "
            "FROM financial_ratios fr "
            "INNER JOIN (SELECT company_id, MAX(year) AS max_year "
            "FROM financial_ratios GROUP BY company_id) latest "
            "ON fr.company_id = latest.company_id AND fr.year = latest.max_year "
            "INNER JOIN companies c ON fr.company_id = c.id"
        )
        ratios_df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    return labels_df.merge(ratios_df, on="company_id", how="left")


def profile_clusters(df):
    return df.groupby("cluster_id")[CLUSTER_FEATURES].agg(["mean", "median"])


def suggest_names(df):
    means = df.groupby("cluster_id")[CLUSTER_FEATURES].mean()

    quality_score = means["return_on_equity_pct"] - means["debt_to_equity"] * 5
    growth_score = (means["revenue_cagr_5yr"] + means["pat_cagr_5yr"]) / 2

    scores = pd.DataFrame({
        "quality_score": quality_score,
        "growth_score": growth_score,
    })

    suggestions = {}
    remaining = scores.copy()

    distressed_id = remaining["quality_score"].idxmin()
    suggestions[distressed_id] = "Distressed or Turnaround"
    remaining = remaining.drop(index=distressed_id)

    hq_id = remaining["quality_score"].idxmax()
    suggestions[hq_id] = "High-Quality Compounders"
    remaining = remaining.drop(index=hq_id)

    growth_id = remaining["growth_score"].idxmax()
    suggestions[growth_id] = "Emerging Growth"
    remaining = remaining.drop(index=growth_id)

    defensive_id = remaining["growth_score"].idxmin()
    suggestions[defensive_id] = "Defensive Dividend Payers"
    remaining = remaining.drop(index=defensive_id)

    for cid in remaining.index:
        suggestions[cid] = "Value Cyclicals"

    return suggestions, scores


def main():
    df = load_cluster_data()

    print("=" * 70)
    print("CLUSTER PROFILE (mean / median of clustering features)")
    print("=" * 70)
    print(profile_clusters(df).round(2))

    print()
    print("CLUSTER SIZES")
    print(df["cluster_id"].value_counts().sort_index().to_string())

    suggestions, scores = suggest_names(df)

    print()
    print("QUALITY / GROWTH SCORES (used to suggest names)")
    print(scores.round(2))

    final_names = dict(suggestions)
    final_names.update(MANUAL_OVERRIDE)

    print()
    print("SUGGESTED CLUSTER NAMES")
    print("(edit MANUAL_OVERRIDE at the top of this file to change one)")
    for cid in sorted(final_names.keys()):
        tag = " (manual override)" if cid in MANUAL_OVERRIDE else " (auto-suggested)"
        print("  Cluster " + str(cid) + ": " + final_names[cid] + tag)

    print()
    print("Sample companies per cluster:")
    for cid in sorted(df["cluster_id"].unique()):
        subset = df.loc[df["cluster_id"] == cid, "company_name"]
        sample = subset.head(8).tolist()
        suffix = " ..." if len(subset) > 8 else ""
        print("  Cluster " + str(cid) + " (" + final_names[cid] + "): " + ", ".join(sample) + suffix)

    labels_df = pd.read_csv(CLUSTER_LABELS_PATH)
    labels_df["cluster_name"] = labels_df["cluster_id"].map(final_names)
    labels_df.to_csv(CLUSTER_LABELS_PATH, index=False)
    print()
    print("Updated " + str(CLUSTER_LABELS_PATH) + " with final cluster names.")


if __name__ == "__main__":
    main()