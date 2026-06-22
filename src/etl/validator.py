import pandas as pd
import csv
import logging
import os

logger = logging.getLogger(__name__)
FAILURES = []


def _flag(company_id, year, field, issue, severity):
    FAILURES.append({
        "company_id": company_id,
        "year": year,
        "field": field,
        "issue": issue,
        "severity": severity
    })


def validate_all(tables: dict) -> list:
    global FAILURES
    FAILURES = []

    companies = tables.get("companies", pd.DataFrame())
    pl        = tables.get("profitandloss", pd.DataFrame())
    bs        = tables.get("balancesheet", pd.DataFrame())
    cf        = tables.get("cashflow", pd.DataFrame())

    if "id" in companies.columns:
        dupes = companies[companies.duplicated("id", keep=False)]
        for _, row in dupes.iterrows():
            _flag(row["id"], "N/A", "id", "Duplicate company PK", "CRITICAL")

    for tname, df in [("profitandloss", pl), ("balancesheet", bs), ("cashflow", cf)]:
        if "company_id" in df.columns and "year" in df.columns:
            dupes = df[df.duplicated(["company_id", "year"], keep=False)]
            for _, row in dupes.iterrows():
                _flag(row["company_id"], row["year"], "company_id+year", f"Duplicate PK in {tname}", "CRITICAL")

    valid_ids = set(companies["id"].tolist()) if "id" in companies.columns else set()
    for tname, df in tables.items():
        if tname == "companies":
            continue
        if "company_id" in df.columns:
            orphans = df[~df["company_id"].isin(valid_ids)]
            for _, row in orphans.iterrows():
                _flag(row["company_id"], row.get("year", "N/A"), "company_id", f"FK violation in {tname}", "CRITICAL")

    if not bs.empty and all(c in bs.columns for c in ["total_assets", "total_liabilities", "company_id", "year"]):
        check = bs.dropna(subset=["total_assets", "total_liabilities"])
        check = check[check["total_assets"] != 0].copy()
        bad = check[abs(check["total_assets"] - check["total_liabilities"]) / check["total_assets"] > 0.01]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "total_assets/total_liabilities", "BS imbalance > 1%", "WARNING")

    if not pl.empty and all(c in pl.columns for c in ["opm_percentage", "operating_profit", "sales", "company_id", "year"]):
        check = pl[pl["sales"] != 0].copy()
        check["computed_opm"] = check["operating_profit"] / check["sales"] * 100
        bad = check[abs(check["opm_percentage"] - check["computed_opm"]) > 1.0]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "opm_percentage", "OPM mismatch", "WARNING")

    if not pl.empty and "sales" in pl.columns:
        bad = pl[pl["sales"] <= 0]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "sales", "sales <= 0", "WARNING")

    if not cf.empty and all(c in cf.columns for c in ["operating_activity", "investing_activity", "financing_activity", "net_cash_flow"]):
        check = cf.dropna(subset=["operating_activity", "investing_activity", "financing_activity", "net_cash_flow"]).copy()
        check["computed_net"] = check["operating_activity"] + check["investing_activity"] + check["financing_activity"]
        bad = check[abs(check["net_cash_flow"] - check["computed_net"]) > 10]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "net_cash_flow", "Net cash mismatch > Rs10 Cr", "WARNING")

    if not bs.empty and "fixed_assets" in bs.columns:
        bad = bs[bs["fixed_assets"] < 0]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "fixed_assets", "fixed_assets < 0", "WARNING")

    if not pl.empty and "tax_percentage" in pl.columns:
        bad = pl[(pl["tax_percentage"] < 0) | (pl["tax_percentage"] > 60)]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "tax_percentage", "Tax rate out of range", "WARNING")

    if not pl.empty and "dividend_payout" in pl.columns:
        bad = pl[pl["dividend_payout"] > 200]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "dividend_payout", "Dividend payout > 200%", "WARNING")

    if not pl.empty and all(c in pl.columns for c in ["eps", "net_profit"]):
        bad = pl[(pl["net_profit"] > 0) & (pl["eps"] <= 0)]
        for _, row in bad.iterrows():
            _flag(row["company_id"], row["year"], "eps", "net_profit > 0 but eps <= 0", "WARNING")

    os.makedirs("output", exist_ok=True)
    out_path = os.path.join("output", "validation_failures.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company_id", "year", "field", "issue", "severity"])
        writer.writeheader()
        writer.writerows(FAILURES)

    critical = [x for x in FAILURES if x["severity"] == "CRITICAL"]
    logger.info(f"DQ complete: {len(FAILURES)} issues ({len(critical)} CRITICAL)")
    return FAILURES
