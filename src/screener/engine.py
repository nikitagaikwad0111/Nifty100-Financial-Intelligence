# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import sqlite3
import yaml
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
CONFIG_PATH = "config/screener_config.yaml"


def load_config() -> dict:
    """Load screener configuration from YAML file."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def load_financial_data() -> pd.DataFrame:
    """Load latest year financial ratios joined with sector and market cap."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT fr.*,
               s.broad_sector,
               s.sub_sector,
               c.company_name,
               mc.pe_ratio,
               mc.pb_ratio,
               mc.dividend_yield_pct,
               mc.market_cap_crore
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id
            AND mc.year = '2024-03'
        WHERE fr.year = (
            SELECT MAX(year) FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id
            AND fr2.year LIKE '%-03'
        )
    """, conn)
    conn.close()
    return df


def winsorise(series: pd.Series, p_low=10, p_high=90) -> pd.Series:
    """Cap extreme values at P10 and P90."""
    low = series.quantile(p_low / 100)
    high = series.quantile(p_high / 100)
    return series.clip(lower=low, upper=high)


def normalise_0_100(series: pd.Series) -> pd.Series:
    """Normalise a series to 0-100 scale."""
    series = winsorise(series)
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - min_val) / (max_val - min_val)) * 100


def compute_composite_score(df: pd.DataFrame) -> pd.Series:
    """
    Compute composite quality score (0-100).
    Weights: 35% Profitability + 30% Cash Quality +
             20% Growth + 15% Leverage
    """
    scores = pd.DataFrame(index=df.index)

    # Profitability (35%)
    roe = normalise_0_100(df["return_on_equity_pct"].fillna(0))
    roce = normalise_0_100(df["return_on_capital_pct"].fillna(0))
    npm = normalise_0_100(df["net_profit_margin_pct"].fillna(0))
    scores["profitability"] = (roe * 0.15 + roce * 0.10 + npm * 0.10) / 0.35

    # Cash Quality (30%)
    fcf_score = normalise_0_100(df["free_cash_flow_cr"].fillna(0))
    cfo_score = normalise_0_100(df["cfo_quality_score"].fillna(0))
    fcf_flag = (df["free_cash_flow_cr"] > 0).astype(float) * 100
    scores["cash_quality"] = (
        fcf_score * 0.15 + cfo_score * 0.10 + fcf_flag * 0.05) / 0.30

    # Growth (20%)
    rev_cagr = normalise_0_100(df["revenue_cagr_5yr"].fillna(0))
    pat_cagr = normalise_0_100(df["pat_cagr_5yr"].fillna(0))
    scores["growth"] = (rev_cagr * 0.10 + pat_cagr * 0.10) / 0.20

    # Leverage (15%) ' lower D/E is better so invert
    de_inv = normalise_0_100(-df["debt_to_equity"].fillna(0))
    icr = normalise_0_100(df["interest_coverage"].fillna(0))
    scores["leverage"] = (de_inv * 0.10 + icr * 0.05) / 0.15

    # Weighted composite
    composite = (
        scores["profitability"] * 0.35 +
        scores["cash_quality"] * 0.30 +
        scores["growth"] * 0.20 +
        scores["leverage"] * 0.15
    )
    return composite.round(2)


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply threshold filters to DataFrame."""
    mask = pd.Series([True] * len(df), index=df.index)

    # ROE minimum
    if filters.get("min_roe"):
        mask &= df["return_on_equity_pct"] >= filters["min_roe"]

    # D/E maximum ' skip Financials sector
    if filters.get("max_de") is not None:
        de_mask = (
            (df["debt_to_equity"] <= filters["max_de"]) |
            (df["broad_sector"] == "Financials")
        )
        mask &= de_mask

    # FCF minimum
    if filters.get("min_fcf") is not None:
        mask &= df["free_cash_flow_cr"] >= filters["min_fcf"]

    # Revenue CAGR 5yr minimum
    if filters.get("min_revenue_cagr_5yr"):
        mask &= df["revenue_cagr_5yr"] >= filters["min_revenue_cagr_5yr"]

    # Revenue CAGR 3yr minimum
    if filters.get("min_revenue_cagr_3yr"):
        mask &= df["revenue_cagr_3yr"] >= filters["min_revenue_cagr_3yr"]

    # PAT CAGR 5yr minimum
    if filters.get("min_pat_cagr_5yr"):
        mask &= df["pat_cagr_5yr"] >= filters["min_pat_cagr_5yr"]

    # OPM minimum
    if filters.get("min_opm"):
        mask &= df["operating_profit_margin_pct"] >= filters["min_opm"]

    # P/E maximum
    if filters.get("max_pe"):
        mask &= df["pe_ratio"] <= filters["max_pe"]

    # P/B maximum
    if filters.get("max_pb"):
        mask &= df["pb_ratio"] <= filters["max_pb"]

    # Dividend yield minimum
    if filters.get("min_dividend_yield"):
        mask &= df["dividend_yield_pct"] >= filters["min_dividend_yield"]

    # ICR minimum ' treat Debt Free as infinity
    if filters.get("min_icr"):
        icr_mask = (
            (df["interest_coverage"] >= filters["min_icr"]) |
            (df["icr_label"] == "Debt Free")
        )
        mask &= icr_mask

    # Sales minimum
    if filters.get("min_sales"):
        mask &= df["total_debt_cr"].fillna(0) >= 0
        conn = sqlite3.connect(DB_PATH)
        sales_df = pd.read_sql("""
            SELECT company_id, sales FROM profitandloss
            WHERE year = (
                SELECT MAX(year) FROM profitandloss p2
                WHERE p2.company_id = profitandloss.company_id
                AND year LIKE '%-03'
            )
        """, conn)
        conn.close()
        df = df.merge(sales_df, on="company_id", how="left")
        mask = mask.reindex(df.index, fill_value=True)
        mask &= df["sales"] >= filters["min_sales"]

    # Sector filter
    if filters.get("sector"):
        mask &= df["broad_sector"] == filters["sector"]

    return df[mask].copy()


def run_screener(filters: dict = None,
                 preset_name: str = None) -> pd.DataFrame:
    """
    Main screener function.
    Pass either custom filters dict or a preset_name.
    Returns sorted DataFrame with composite_quality_score.
    """
    config = load_config()
    df = load_financial_data()

    # Use preset if specified
    if preset_name:
        if preset_name not in config["presets"]:
            raise ValueError(f"Unknown preset: {preset_name}")
        filters = config["presets"][preset_name]
        filters = {k: v for k, v in filters.items()
                   if k != "description"}

    if filters is None:
        filters = {}

    # Apply filters
    results = apply_filters(df, filters)

    # Add composite score
    results["composite_quality_score"] = compute_composite_score(results)

    # Sort by composite score
    results = results.sort_values(
        "composite_quality_score", ascending=False)

    logger.info(
        f"Screener returned {len(results)} companies")
    return results


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    logging.basicConfig(level=logging.INFO)

    print("Testing Quality Compounder preset...")
    results = run_screener(preset_name="quality_compounder")
    print(f"Results: {len(results)} companies")
    print(results[["company_id", "company_name",
                   "return_on_equity_pct",
                   "debt_to_equity",
                   "composite_quality_score"]].head(10).to_string())
