import pytest
from src.analytics.ratios import (
    compute_npm, compute_opm, compute_roe, compute_roce,
    compute_roa, compute_de, compute_icr, compute_asset_turnover,
    compute_all_ratios
)


class TestProfitability:

    def test_npm_normal(self):
        assert compute_npm(1000, 10000) == 10.0

    def test_npm_zero_sales(self):
        assert compute_npm(1000, 0) is None

    def test_opm_normal(self):
        assert compute_opm(2000, 10000) == 20.0

    def test_roe_normal(self):
        assert compute_roe(1000, 500, 4500) == 20.0

    def test_roe_negative_equity(self):
        assert compute_roe(1000, -500, -100) is None

    def test_roce_normal(self):
        result = compute_roce(2000, 500, 1000, 4000, 2000)
        assert result is not None

    def test_roa_normal(self):
        assert compute_roa(1000, 10000) == 10.0

    def test_roa_zero_assets(self):
        assert compute_roa(1000, 0) is None


class TestLeverage:

    def test_de_debt_free(self):
        de, flag = compute_de(0, 500, 4500)
        assert de == 0.0
        assert flag is False

    def test_de_normal(self):
        de, flag = compute_de(1000, 500, 4500)
        assert de == 0.2

    def test_de_high_leverage_non_financial(self):
        de, flag = compute_de(30000, 500, 4500, "Industrials")
        assert flag is True

    def test_de_high_leverage_bank_no_flag(self):
        de, flag = compute_de(30000, 500, 4500, "Financials")
        assert flag is False

    def test_icr_interest_zero(self):
        icr, label = compute_icr(2000, 100, 0)
        assert icr is None
        assert label == "Debt Free"

    def test_icr_at_risk(self):
        icr, label = compute_icr(100, 0, 100)
        assert label == "At Risk"

    def test_icr_ok(self):
        icr, label = compute_icr(2000, 100, 100)
        assert label == "OK"


class TestEfficiency:

    def test_asset_turnover_normal(self):
        assert compute_asset_turnover(10000, 5000) == 2.0

    def test_asset_turnover_zero_assets(self):
        assert compute_asset_turnover(10000, 0) is None


class TestComputeAllRatios:

    def test_full_computation(self):
        pl_row = {
            "net_profit": 34990, "sales": 225458,
            "operating_profit": 48534, "depreciation": 5800,
            "other_income": 3800, "interest": 0,
            "eps": 95.3, "dividend_payout": 45.0
        }
        bs_row = {
            "equity_capital": 366, "reserves": 101133,
            "borrowings": 0, "total_assets": 161124,
            "investments": 5000
        }
        result = compute_all_ratios(pl_row, bs_row, "Information Technology")
        assert result["net_profit_margin_pct"] is not None
        assert result["debt_to_equity"] == 0.0
        assert result["icr_label"] == "Debt Free"
        assert result["earnings_per_share"] == 95.3

    def test_negative_equity_case(self):
        pl_row = {
            "net_profit": -500, "sales": 10000,
            "operating_profit": -200, "depreciation": 100,
            "other_income": 0, "interest": 50,
            "eps": -5.0, "dividend_payout": 0
        }
        bs_row = {
            "equity_capital": 100, "reserves": -300,
            "borrowings": 1000, "total_assets": 5000,
            "investments": 0
        }
        result = compute_all_ratios(pl_row, bs_row, "Materials")
        assert result["return_on_equity_pct"] is None
