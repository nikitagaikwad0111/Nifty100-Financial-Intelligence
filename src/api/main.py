# src/api/main.py
#
# Sprint 6 - Day 38: FastAPI server scaffold.
#
# Run with:
#   uvicorn src.api.main:app --port 8000
# Then visit http://127.0.0.1:8000/docs for the OpenAPI docs page.

import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    health,
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
)

DB_PATH = Path("data/nifty100.db")


def get_db_connection():
    """Open a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


app = FastAPI(
    title="Nifty100 Financial Intelligence API",
    version="1.0.0",
    description="REST API for the Nifty 100 Financial Intelligence Platform.",
)

# CORS - allow all origins. Internal/local use only, not public-facing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log method, path, status code, and response time for every request."""
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    print(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
    return response


app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(companies.router, prefix="/api/v1", tags=["companies"])
app.include_router(screener.router, prefix="/api/v1", tags=["screener"])
app.include_router(sectors.router, prefix="/api/v1", tags=["sectors"])
app.include_router(peers.router, prefix="/api/v1", tags=["peers"])
app.include_router(valuation.router, prefix="/api/v1", tags=["valuation"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["portfolio"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])