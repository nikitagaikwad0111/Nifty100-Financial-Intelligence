# src/api/routers/companies.py
#
# Sprint 6 - Day 39: Company Data endpoints.
#
# GET /api/v1/companies                - list all, with filters
# GET /api/v1/companies/{ticker}        - full company profile
# GET /api/v1/companies/{ticker}/pl     - P&L history

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

DB_PATH = Path("data/nifty100.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/companies")
def list_companies(
    sector: Optional[str] = Query(None, description="Filter by broad_sector, exact match"),
    market_cap_category: Optional[str] = Query(None, description="Filter by market_cap_category, exact match"),
    search: Optional[str] = Query(None, description="Partial match on company_name or ticker"),
):
    """List all companies with id, company_name, broad_sector, sub_sector, roe_percentage, roce_percentage. Supports optional sector, market_cap_category, and search filters."""
    conn = get_conn()
    try:
        query = """
            SELECT c.id, c.company_name, s.broad_sector, s.sub_sector,
                   s.market_cap_category, c.roe_percentage, c.roce_percentage
            FROM companies c
            INNER JOIN sectors s ON c.id = s.company_id
            WHERE 1=1
        """
        params = []

        if sector:
            query += " AND s.broad_sector = ?"
            params.append(sector)
        if market_cap_category:
            query += " AND s.market_cap_category = ?"
            params.append(market_cap_category)
        if search:
            query += " AND (c.company_name LIKE ? OR c.id LIKE ?)"
            like_term = f"%{search}%"
            params.extend([like_term, like_term])

        query += " ORDER BY c.company_name"

        cur = conn.cursor()
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    return {"count": len(rows), "companies": rows}


@router.get("/companies/{ticker}")
def get_company(ticker: str):
    """Return full company profile: companies fields + sector data + latest year KPIs. 404 if ticker not found."""
    ticker = ticker.upper()
    conn = get_conn()
    try:
        cur = conn.cursor()

        cur.execute("SELECT * FROM companies WHERE id = ?", (ticker,))
        company_row = cur.fetchone()
        if company_row is None:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")
        company = dict(company_row)

        cur.execute("SELECT broad_sector, sub_sector, index_weight_pct, market_cap_category FROM sectors WHERE company_id = ?", (ticker,))
        sector_row = cur.fetchone()
        if sector_row:
            company.update(dict(sector_row))

        cur.execute(
            """
            SELECT * FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (ticker,),
        )
        ratios_row = cur.fetchone()
        if ratios_row:
            company["latest_year_kpis"] = dict(ratios_row)
        else:
            company["latest_year_kpis"] = None
    finally:
        conn.close()

    return company


@router.get("/companies/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: Optional[str] = Query(None, description="YYYY-MM, inclusive"),
    to_year: Optional[str] = Query(None, description="YYYY-MM, inclusive"),
):
    """Return P&L history array for a company. Supports from_year/to_year filtering in YYYY-MM format. 404 if ticker not found."""
    ticker = ticker.upper()
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM companies WHERE id = ?", (ticker,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found")

        query = "SELECT * FROM profitandloss WHERE company_id = ?"
        params = [ticker]
        if from_year:
            query += " AND year >= ?"
            params.append(from_year)
        if to_year:
            query += " AND year <= ?"
            params.append(to_year)
        query += " ORDER BY year"

        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

    return {"ticker": ticker, "count": len(rows), "pl_history": rows}