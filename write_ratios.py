code = '''import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def safe_divide(numerator, denominator):
    if denominator is None or denominator == 0:
        return None
    if numerator is None:
        return None
    return round(numerator / denominator, 4)


def compute_npm(net_profit, sales):
    result = safe_divide(net_profit, sales)
    return round(result * 100, 2) if result is not None else None


def compute_opm(operating_profit, sales):
    result = safe_divide(operating_profit, sales)
    return round(result * 100, 2) if result is not None else None


def compute_roe(net_profit, equity_capital, reserves):
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0:
        return None
    return round((net_profit / equity) * 100, 2)


def compute_roce(operating_profit, depreciation, equity_capital,
                 reserves, borrowings):
    ebit = (operating_profit or 0) - (depreciation or 0)
    capital = (equity_capital or 0) + (reserves or 0) + (borrowings or 0)
    if capital <= 0:
        return None
    return round((ebit / capital) * 100, 2)


def compute_roa(net_profit, total_assets):
    result = safe_divide(net_profit, total_assets)
    return round(result * 100, 2) if result is not None else None


def compute_de(borrowings, equity_capital, reserves, broad_sector=None):
    if borrowings is None or borrowings == 0:
        return 0.0, False
    equity = (equity_capital or 0) + (reserves or 0)
    if equity <= 0:
        return None, False
    de = round(borrowings / equity, 4)
    high_leverage_flag = de > 5 and broad_sector != "Financials"
    return de, high_leverage_flag


def compute_icr(operating_profit, other_income, interest):
    if interest is None or interest == 0:
        return None, "Debt Free"
    numerator = (operating_profit or 0) + (other_income or 0)
    icr = round(numerator / interest, 2)
    label = "At Risk" if icr < 1.5 else "OK"
    return icr, label


def compute_asset_turnover(sales, total_assets):
    return safe_divide(sales, total_assets)


def compute_net_debt(borrowings, investments):
    return (borrowings or 0) - (investments or 0)


def compute_all_ratios(pl_row: dict, bs_row: dict, broad_sector: str = None) -> dict:
    ratios = {}

    ratios["net_profit_margin_pct"] = compute_npm(
        pl_row.get("net_profit"), pl_row.get("sales"))

    ratios["operating_profit_margin_pct"] = compute_opm(
        pl_row.get("operating_profit"), pl_row.get("sales"))

    ratios["return_on_equity_pct"] = compute_roe(
        pl_row.get("net_profit"),
        bs_row.get("equity_capital"),
        bs_row.get("reserves"))

    ratios["return_on_capital_pct"] = compute_roce(
        pl_row.get("operating_profit"),
        pl_row.get("depreciation"),
        bs_row.get("equity_capital"),
        bs_row.get("reserves"),
        bs_row.get("borrowings"))

    ratios["return_on_assets_pct"] = compute_roa(
        pl_row.get("net_profit"),
        bs_row.get("total_assets"))

    de, high_leverage_flag = compute_de(
        bs_row.get("borrowings"),
        bs_row.get("equity_capital"),
        bs_row.get("reserves"),
        broad_sector)
    ratios["debt_to_equity"] = de
    ratios["high_leverage_flag"] = high_leverage_flag

    icr, icr_label = compute_icr(
        pl_row.get("operating_profit"),
        pl_row.get("other_income"),
        pl_row.get("interest"))
    ratios["interest_coverage"] = icr
    ratios["icr_label"] = icr_label

    ratios["net_debt_cr"] = compute_net_debt(
        bs_row.get("borrowings"),
        bs_row.get("investments"))

    ratios["asset_turnover"] = compute_asset_turnover(
        pl_row.get("sales"),
        bs_row.get("total_assets"))

    ratios["earnings_per_share"] = pl_row.get("eps")
    ratios["dividend_payout_ratio_pct"] = pl_row.get("dividend_payout")
    ratios["total_debt_cr"] = bs_row.get("borrowings")

    return ratios
'''

with open("src/analytics/ratios.py", "w") as f:
    f.write(code)

print("Done!")