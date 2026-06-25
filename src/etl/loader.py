import pandas as pd
import sqlite3
import logging
import os
import time
import csv
from datetime import datetime
from dotenv import load_dotenv
from src.etl.normaliser import normalize_year, normalize_ticker

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "data/nifty100.db")
logger = logging.getLogger(__name__)

CORE_FILES = {
    "companies":     ("data/raw/companies.xlsx",     1),
    "profitandloss": ("data/raw/profitandloss.xlsx", 1),
    "balancesheet":  ("data/raw/balancesheet.xlsx",  1),
    "cashflow":      ("data/raw/cashflow.xlsx",      1),
    "analysis":      ("data/raw/analysis.xlsx",      1),
    "documents":     ("data/raw/documents.xlsx",     1),
    "prosandcons":   ("data/raw/prosandcons.xlsx",   1),
}

SUPP_FILES = {
    "sectors":          ("data/supporting/sectors.xlsx",          0),
    "stock_prices":     ("data/supporting/stock_prices.xlsx",     0),
    "market_cap":       ("data/supporting/market_cap.xlsx",       0),
    "financial_ratios": ("data/supporting/financial_ratios.xlsx", 0),
    "peer_groups":      ("data/supporting/peer_groups.xlsx",      0),
}

TIME_SERIES = ["profitandloss", "balancesheet", "cashflow",
               "stock_prices", "market_cap", "financial_ratios"]


def load_excel(path: str, header_row: int) -> pd.DataFrame:
    """Load an Excel file into a DataFrame."""
    df = pd.read_excel(path, header=header_row, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def apply_normalisation(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Normalise ticker and year fields."""
    if table_name == "companies" and "id" in df.columns:
        df["id"] = df["id"].apply(normalize_ticker)
    if "company_id" in df.columns:
        df["company_id"] = df["company_id"].apply(normalize_ticker)
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)
        bad = df[df["year"] == "PARSE_ERROR"]
        if not bad.empty:
            logger.warning(f"{table_name}: {len(bad)} rows with unparseable year dropped")
        df = df[df["year"] != "PARSE_ERROR"]
    return df


def deduplicate(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows."""
    if table_name in TIME_SERIES and "company_id" in df.columns and "year" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["company_id", "year"], keep="last")
        dupes = before - len(df)
        if dupes:
            logger.warning(f"{table_name}: {dupes} duplicate rows removed")
    return df


def load_all_tables() -> dict:
    """Load all 12 Excel files. Returns dict of DataFrames."""
    all_files = {**CORE_FILES, **SUPP_FILES}
    tables = {}
    audit_rows = []

    for table_name, (path, header) in all_files.items():
        start = time.time()
        try:
            df = load_excel(path, header)
            rows_in = len(df)
            df = apply_normalisation(table_name, df)
            df = deduplicate(table_name, df)
            rows_out = len(df)
            rejected = rows_in - rows_out
            tables[table_name] = df
            runtime = round(time.time() - start, 2)
            audit_rows.append({
                "table": table_name, "rows_in": rows_in,
                "rows_out": rows_out, "rejected": rejected,
                "timestamp": datetime.now().isoformat(),
                "runtime_s": runtime, "status": "OK"
            })
            logger.info(f"Loaded {table_name}: {rows_out} rows in {runtime}s")
        except Exception as e:
            logger.error(f"FAILED to load {table_name}: {e}")
            audit_rows.append({
                "table": table_name, "rows_in": 0, "rows_out": 0,
                "rejected": 0, "timestamp": datetime.now().isoformat(),
                "runtime_s": 0, "status": f"ERROR: {e}"
            })

    os.makedirs("output", exist_ok=True)
    with open("output/load_audit.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["table", "rows_in",
                                "rows_out", "rejected",
                                "timestamp", "runtime_s", "status"])
        writer.writeheader()
        writer.writerows(audit_rows)

    return tables


def write_to_sqlite(tables: dict) -> None:
    """Write all DataFrames into SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for table_name, df in tables.items():
            df.to_sql(table_name, conn,
                      if_exists="replace", index=False)
            logger.info(f"Written: {table_name} ({len(df)} rows)")
        conn.commit()
    logger.info(f"Database saved to {DB_PATH}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    tables = load_all_tables()
    write_to_sqlite(tables)
    print("ETL complete. Check output/load_audit.csv")
