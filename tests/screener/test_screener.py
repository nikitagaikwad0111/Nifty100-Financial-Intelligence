import pytest
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from src.screener.engine import (
    run_screener, apply_filters,
    compute_composite_score, winsorise, normalise_0_100
)
import pandas as pd
import numpy as np


class TestWinsorise:

    def test_caps_extreme_high(self):
        s = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
        result = winsorise(s)
        assert result.max() < 100

    def test_caps_extreme_low(self):
        s = pd.Series([-100, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        result = winsorise(s)
        assert result.min() > -100


class TestNormalise:

    def test_range_0_100(self):
        s = pd.Series([10, 20, 30, 40, 50])
        result = normalise_0_100(s)
        assert result.min() >= 0
        assert result.max() <= 100

    def test_flat_series_returns_50(self):
        s = pd.Series([5, 5, 5, 5, 5])
        result = normalise_0_100(s)
        assert (result == 50.0).all()


class TestApplyFilters:

    def make_df(self):
        return pd.DataFrame({
            "company_id": ["TCS", "INFY", "HDFCBANK", "SBIN", "ONGC"],
            "company_name": ["TCS", "Infosys", "HDFC Bank",
                             "SBI", "ONGC"],
            "broad_sector": ["Information Technology",
                             "Information Technology",
                             "Financials", "Financials", "Energy"],
            "return_on_equity_pct": [50.0, 30.0, 14.0, 12.0, 16.0],
            "debt_to_equity": [0.09, 0.09, 6.8, 12.0, 0.45],
            "free_cash_flow_cr": [50000, 20000, 12000, -5000, 8000],
            "revenue_cagr_5yr": [10.0, 13.0, 21.0, 8.0, 7.0],
            "pat_cagr_5yr": [8.0, 10.0, 23.0, 5.0, 6.0],
            "operating_profit_margin_pct": [27.0, 24.0, 30.0, 20.0, 18.0],
            "pe_ratio": [28.0, 25.0, 18.0, 8.0, 10.0],
            "pb_ratio": [12.0, 7.0, 2.5, 1.2, 1.5],
            "dividend_yield_pct": [1.5, 3.0, 1.2, 2.5, 4.0],
            "interest_coverage": [None, None, 2.0, 1.8, 3.0],
            "icr_label": ["Debt Free", "Debt Free", "OK", "OK", "OK"],
            "net_profit_margin_pct": [19.0, 17.0, 14.0, 8.0, 9.0],
            "return_on_capital_pct": [45.0, 35.0, 12.0, 10.0, 14.0],
            "cfo_quality_score": [1.2, 1.1, 0.8, 0.6, 0.9],
            "revenue_cagr_3yr": [13.0, 10.0, 18.0, 6.0, 8.0],
            "eps_cagr_5yr": [8.0, 10.0, 22.0, 4.0, 5.0],
            "asset_turnover": [1.5, 1.2, 0.1, 0.08, 0.5],
            "dividend_payout_ratio_pct": [45.0, 60.0, 16.0, 20.0, 42.0],
        })

    def test_min_roe_filter(self):
        df = self.make_df()
        result = apply_filters(df, {"min_roe": 20})
        assert all(result["return_on_equity_pct"] >= 20)

    def test_max_de_skips_financials(self):
        df = self.make_df()
        result = apply_filters(df, {"max_de": 1.0})
        financials = result[result["broad_sector"] == "Financials"]
        assert len(financials) > 0

    def test_min_fcf_filter(self):
        df = self.make_df()
        result = apply_filters(df, {"min_fcf": 0})
        assert all(result["free_cash_flow_cr"] >= 0)

    def test_sector_filter(self):
        df = self.make_df()
        result = apply_filters(
            df, {"sector": "Information Technology"})
        assert all(result["broad_sector"] == "Information Technology")
        assert len(result) == 2

    def test_icr_debt_free_always_passes(self):
        df = self.make_df()
        result = apply_filters(df, {"min_icr": 5})
        debt_free = result[result["icr_label"] == "Debt Free"]
        assert len(debt_free) > 0

    def test_empty_filters_returns_all(self):
        df = self.make_df()
        result = apply_filters(df, {})
        assert len(result) == len(df)

    def test_combined_filters(self):
        df = self.make_df()
        result = apply_filters(df, {
            "min_roe": 15,
            "max_de": 1.0,
            "min_fcf": 0
        })
        assert len(result) > 0
        for _, row in result.iterrows():
            assert row["return_on_equity_pct"] >= 15
            assert row["free_cash_flow_cr"] >= 0


class TestCompositeScore:

    def make_df(self):
        return pd.DataFrame({
            "return_on_equity_pct": [50.0, 15.0, 8.0],
            "return_on_capital_pct": [45.0, 12.0, 6.0],
            "net_profit_margin_pct": [20.0, 10.0, 5.0],
            "free_cash_flow_cr": [50000.0, 5000.0, -1000.0],
            "cfo_quality_score": [1.2, 0.8, 0.4],
            "revenue_cagr_5yr": [12.0, 8.0, 3.0],
            "pat_cagr_5yr": [10.0, 6.0, 2.0],
            "debt_to_equity": [0.1, 0.5, 2.0],
            "interest_coverage": [None, 5.0, 2.0],
        })

    def test_score_range_0_100(self):
        df = self.make_df()
        scores = compute_composite_score(df)
        assert scores.min() >= 0
        assert scores.max() <= 100

    def test_better_company_higher_score(self):
        df = self.make_df()
        scores = compute_composite_score(df)
        assert scores.iloc[0] > scores.iloc[2]


class TestRunScreener:

    def test_quality_compounder_returns_results(self):
        results = run_screener(preset_name="quality_compounder")
        assert len(results) >= 5
        assert len(results) <= 50

    def test_growth_accelerator_returns_results(self):
        results = run_screener(preset_name="growth_accelerator")
        assert len(results) >= 5
        assert len(results) <= 50

    def test_composite_score_column_exists(self):
        results = run_screener(preset_name="quality_compounder")
        assert "composite_quality_score" in results.columns

    def test_results_sorted_by_score(self):
        results = run_screener(preset_name="quality_compounder")
        scores = results["composite_quality_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_invalid_preset_raises_error(self):
        with pytest.raises(ValueError):
            run_screener(preset_name="invalid_preset")

    def test_custom_filter(self):
        results = run_screener(filters={"min_roe": 20})
        assert all(results["return_on_equity_pct"] >= 20)
