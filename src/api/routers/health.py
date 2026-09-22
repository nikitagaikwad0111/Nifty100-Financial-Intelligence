# src/api/routers/health.py
#
# GET /api/v1/health - reports app status, live row counts for every
# table in the DB (queried dynamically via sqlite_master, so it never
# goes stale as tables get added), uptime, and API version.

import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

DB_PATH = Path("data/nifty100.db")
APP_VERSION = "1.0.0"
START_TIME = time.time()


@router.get("/health")
def health_check():
    """Return API status, per-table row counts, uptime, and version."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]

        db_row_counts = {}
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            db_row_counts[table] = cur.fetchone()[0]
    finally:
        conn.close()

    return {
        "status": "ok",
        "db_row_counts": db_row_counts,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": APP_VERSION,
    }