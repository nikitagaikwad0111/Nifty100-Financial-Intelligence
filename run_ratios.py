import sys
import os
import sqlite3
import pandas as pd
import logging
import csv

sys.path.insert(0, os.path.abspath("."))

from src.analytics.ratios import compute_all_ratios
from src.analytics.cagr import compute_revenue_cagr, compute_pat_cagr, compute_eps_cagr
from src.analytics.cashflow_kpis import (
    compute_fcf, compute_cfo_quality_score,
    compute_capex_intensity, compute_fcf_conversion,
    classify_capital_allocation
)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "data/nifty100.db"


def load_data():
    """Load all required tables from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    pl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return pl, bs, cf, sectors


def build_time_series(df, company_id, value_col):
    """Build {year: value} dict for CAGR computation."""
    company_data = df[df["company_id"] == company_id].copy()
    company_data = company_data.sort_values("year")
    return dict(zip(company_data["year"], company_data[value_col]))


def compute_book_value_per_share(equity_capital, reserves, face_value=1):
    """Book Value Per Share = (equity + reserves) / shares outstanding."""
    if equity_capital is None or reserves is None:
        return None
    equity = equity_capital + reserves
    if face_value is None or face_value == 0:
        face_value = 1
    shares = equity_capital / face_value
    if shares <= 0:
        return None
    return round(equity / shares, 2)


def run_ratio_engine():
    logger.info("Loading data from SQLite...")
    pl, bs, cf, sectors = load_data()

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))
    companies = pl["company_id"].unique()
    logger.info(f"Processing {len(companies)} companies...")

    all_ratios = []
    capital_allocation_rows = []

    for company_id in companies:
        broad_sector = sector_map.get(company_id, None)

        pl_co = pl[pl["company_id"] == company_id].copy()
        bs_co = bs[bs["company_id"] == company_id].copy()
        cf_co = cf[cf["company_id"] == company_id].copy()

        # Build time series for CAGR
        rev_ts  = build_time_series(pl, company_id, "sales")
        pat_ts  = build_time_series(pl, company_id, "net_profit")
        eps_ts  = build_time_series(pl, company_id, "eps")

        # CFO/PAT for quality score (last 5 years)
        cf_sorted = cf_co.sort_values("year").tail(5)
        pl_sorted = pl_co.sort_values("year").tail(5)
        cfo_values = cf_sorted["operating_activity"].tolist()
        pat_values = pl_sorted["net_profit"].tolist()
        cfo_quality, cfo_label = compute_cfo_quality_score(
            cfo_values, pat_values)

        for _, pl_row in pl_co.iterrows():
            year = pl_row["year"]

            bs_row_df = bs_co[bs_co["year"] == year]
            cf_row_df = cf_co[cf_co["year"] == year]

            if bs_row_df.empty:
                continue

            bs_row = bs_row_df.iloc[0].to_dict()
            cf_row = cf_row_df.iloc[0].to_dict() if not cf_row_df.empty else {}

            # Base ratios
            ratios = compute_all_ratios(pl_row.to_dict(), bs_row, broad_sector)

            # CAGR
            rev_cagr = compute_revenue_cagr(rev_ts, year)
            pat_cagr = compute_pat_cagr(pat_ts, year)
            eps_cagr = compute_eps_cagr(eps_ts, year)
            ratios.update(rev_cagr)
            ratios.update(pat_cagr)
            ratios.update(eps_cagr)

            # Cash flow KPIs
            cfo = cf_row.get("operating_activity")
            cfi = cf_row.get("investing_activity")
            cff = cf_row.get("financing_activity")

            ratios["free_cash_flow_cr"] = compute_fcf(cfo, cfi)
            ratios["cash_from_operations_cr"] = cfo
            ratios["capex_cr"] = abs(cfi) if cfi is not None else None
            ratios["cfo_quality_score"] = cfo_quality
            ratios["cfo_quality_label"] = cfo_label

            capex_intensity, capex_label = compute_capex_intensity(
                cfi, pl_row.get("sales"))
            ratios["capex_intensity_pct"] = capex_intensity
            ratios["capex_intensity_label"] = capex_label

            ratios["fcf_conversion_rate"] = compute_fcf_conversion(
                ratios["free_cash_flow_cr"],
                pl_row.get("operating_profit"))

            # Book value per share
            ratios["book_value_per_share"] = compute_book_value_per_share(
                bs_row.get("equity_capital"),
                bs_row.get("reserves"))

            # Capital allocation
            pattern, cfo_sign, cfi_sign, cff_sign = classify_capital_allocation(
                cfo, cfi, cff)
            ratios["capital_allocation_pattern"] = pattern

            capital_allocation_rows.append({
                "company_id": company_id,
                "year": year,
                "cfo_sign": cfo_sign,
                "cfi_sign": cfi_sign,
                "cff_sign": cff_sign,
                "pattern_label": pattern
            })

            ratios["company_id"] = company_id
            ratios["year"] = year
            all_ratios.append(ratios)

    logger.info(f"Computed ratios for {len(all_ratios)} company-year combinations")

    # Write to SQLite
    ratios_df = pd.DataFrame(all_ratios)
    conn = sqlite3.connect(DB_PATH)
    ratios_df.to_sql("financial_ratios", conn,
                     if_exists="replace", index=False)
    conn.close()
    logger.info("financial_ratios table updated in SQLite")

    # Write capital allocation CSV
    os.makedirs("output", exist_ok=True)
    with open("output/capital_allocation.csv", "w",
              newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "company_id", "year", "cfo_sign",
            "cfi_sign", "cff_sign", "pattern_label"])
        writer.writeheader()
        writer.writerows(capital_allocation_rows)
    logger.info("capital_allocation.csv written")

    return ratios_df


if __name__ == "__main__":
    df = run_ratio_engine()
    print(f"\nDone! {len(df)} rows in financial_ratios table")
    print(f"Columns: {list(df.columns)}")
