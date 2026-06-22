import pytest
import pandas as pd
from src.etl.validator import validate_all


def make_companies():
    """Helper — valid companies table."""
    return pd.DataFrame({
        "id": ["TCS", "INFY", "HDFCBANK"],
        "company_name": ["Tata Consultancy", "Infosys", "HDFC Bank"]
    })


def make_pl():
    """Helper — valid P&L table."""
    return pd.DataFrame({
        "company_id": ["TCS", "TCS", "INFY"],
        "year": ["2023-03", "2022-03", "2023-03"],
        "sales": [225458, 198000, 146767],
        "operating_profit": [48534, 41000, 31000],
        "opm_percentage": [21.5, 20.7, 21.1],
        "net_profit": [34990, 30000, 22500],
        "eps": [95.3, 81.0, 53.0],
        "tax_percentage": [25.0, 26.0, 25.5],
        "dividend_payout": [45.0, 40.0, 35.0]
    })


def make_bs():
    """Helper — valid balance sheet table."""
    return pd.DataFrame({
        "company_id": ["TCS", "INFY"],
        "year": ["2023-03", "2023-03"],
        "total_assets": [1000, 800],
        "total_liabilities": [1000, 800],
        "fixed_assets": [200, 150]
    })


def make_cf():
    """Helper — valid cash flow table."""
    return pd.DataFrame({
        "company_id": ["TCS", "INFY"],
        "year": ["2023-03", "2023-03"],
        "operating_activity": [40000, 25000],
        "investing_activity": [-10000, -5000],
        "financing_activity": [-5000, -3000],
        "net_cash_flow": [25000, 17000]
    })


# ── DQ-01: Company PK uniqueness ────────────────────────────────────────
class TestDQ01:

    def test_no_duplicates(self):
        tables = {"companies": make_companies(),
                  "profitandloss": pd.DataFrame(),
                  "balancesheet": pd.DataFrame(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        critical = [f for f in failures
                    if f["severity"] == "CRITICAL"
                    and "Duplicate company PK" in f["issue"]]
        assert len(critical) == 0

    def test_duplicate_company_id(self):
        companies = pd.DataFrame({
            "id": ["TCS", "TCS", "INFY"],
            "company_name": ["Tata", "Tata Dupe", "Infosys"]
        })
        tables = {"companies": companies,
                  "profitandloss": pd.DataFrame(),
                  "balancesheet": pd.DataFrame(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        critical = [f for f in failures
                    if "Duplicate company PK" in f["issue"]]
        assert len(critical) > 0


# ── DQ-02: Annual PK uniqueness ─────────────────────────────────────────
class TestDQ02:

    def test_duplicate_pl_row(self):
        pl = pd.DataFrame({
            "company_id": ["TCS", "TCS"],
            "year": ["2023-03", "2023-03"],
            "sales": [225458, 225458],
            "operating_profit": [48534, 48534],
            "opm_percentage": [21.5, 21.5],
            "net_profit": [34990, 34990],
            "eps": [95.3, 95.3],
            "tax_percentage": [25.0, 25.0],
            "dividend_payout": [45.0, 45.0]
        })
        tables = {"companies": make_companies(),
                  "profitandloss": pl,
                  "balancesheet": pd.DataFrame(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        critical = [f for f in failures
                    if "Duplicate PK in profitandloss" in f["issue"]]
        assert len(critical) > 0


# ── DQ-03: FK integrity ──────────────────────────────────────────────────
class TestDQ03:

    def test_orphan_company_id(self):
        pl = make_pl().copy()
        pl.loc[len(pl)] = {
            "company_id": "UNKNOWN", "year": "2023-03",
            "sales": 1000, "operating_profit": 200,
            "opm_percentage": 20.0, "net_profit": 100,
            "eps": 10.0, "tax_percentage": 25.0,
            "dividend_payout": 30.0
        }
        tables = {"companies": make_companies(),
                  "profitandloss": pl,
                  "balancesheet": pd.DataFrame(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        critical = [f for f in failures
                    if "FK violation" in f["issue"]
                    and f["company_id"] == "UNKNOWN"]
        assert len(critical) > 0

    def test_valid_fk(self):
        tables = {"companies": make_companies(),
                  "profitandloss": make_pl(),
                  "balancesheet": make_bs(),
                  "cashflow": make_cf()}
        failures = validate_all(tables)
        fk_fails = [f for f in failures
                    if "FK violation" in f["issue"]]
        assert len(fk_fails) == 0


# ── DQ-04: Balance sheet balance ────────────────────────────────────────
class TestDQ04:

    def test_bs_imbalance(self):
        bs = pd.DataFrame({
            "company_id": ["TCS"],
            "year": ["2023-03"],
            "total_assets": [1000],
            "total_liabilities": [1020],
            "fixed_assets": [200]
        })
        tables = {"companies": make_companies(),
                  "profitandloss": pd.DataFrame(),
                  "balancesheet": bs,
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        warns = [f for f in failures
                 if "BS imbalance" in f["issue"]]
        assert len(warns) > 0

    def test_bs_balanced(self):
        tables = {"companies": make_companies(),
                  "profitandloss": pd.DataFrame(),
                  "balancesheet": make_bs(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        warns = [f for f in failures
                 if "BS imbalance" in f["issue"]]
        assert len(warns) == 0


# ── DQ-06: Positive sales ────────────────────────────────────────────────
class TestDQ06:

    def test_zero_sales(self):
        pl = make_pl().copy()
        pl.loc[len(pl)] = {
            "company_id": "TCS", "year": "2020-03",
            "sales": 0, "operating_profit": 0,
            "opm_percentage": 0, "net_profit": -100,
            "eps": -1, "tax_percentage": 0,
            "dividend_payout": 0
        }
        tables = {"companies": make_companies(),
                  "profitandloss": pl,
                  "balancesheet": pd.DataFrame(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        warns = [f for f in failures if "sales <= 0" in f["issue"]]
        assert len(warns) > 0


# ── DQ-11: Tax rate range ────────────────────────────────────────────────
class TestDQ11:

    def test_tax_out_of_range(self):
        pl = make_pl().copy()
        pl.loc[0, "tax_percentage"] = 75.0
        tables = {"companies": make_companies(),
                  "profitandloss": pl,
                  "balancesheet": pd.DataFrame(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        warns = [f for f in failures
                 if "Tax rate out of range" in f["issue"]]
        assert len(warns) > 0


# ── DQ-14: EPS sign consistency ─────────────────────────────────────────
class TestDQ14:

    def test_eps_sign_mismatch(self):
        pl = make_pl().copy()
        pl.loc[0, "net_profit"] = 5000
        pl.loc[0, "eps"] = -10.0
        tables = {"companies": make_companies(),
                  "profitandloss": pl,
                  "balancesheet": pd.DataFrame(),
                  "cashflow": pd.DataFrame()}
        failures = validate_all(tables)
        warns = [f for f in failures
                 if "eps" in f["field"]
                 and "net_profit > 0 but eps <= 0" in f["issue"]]
        assert len(warns) > 0