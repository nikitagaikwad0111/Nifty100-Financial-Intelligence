# Sprint 1 Retrospective
## Sprint: Data Foundation (Days 1-7)
## Date: June 2026

## What We Delivered
- Project scaffold: folders, venv, 20 libraries installed
- normaliser.py: normalize_year() and normalize_ticker() functions
- validator.py: 16 DQ rules implemented
- schema.sql: 10-table SQLite schema with FK constraints
- loader.py: ETL pipeline loading all 12 Excel files
- run_etl.py: Master ETL runner with DQ validation
- exploratory_queries.sql: 10 analytical SQL queries
- nifty100.db: Fully loaded database

## Test Results
- 35 normaliser tests: ALL PASSED
- 10 validator tests: ALL PASSED
- Total: 45 tests, 0 failures

## Database Stats
- Companies: 92
- P&L rows: 1161
- Balance Sheet rows: 1220
- Cash Flow rows: 1152
- Stock Prices: 5520
- Total records: ~11,000+
- FK violations: 0

## Issues Found & Fixed
- UNIONBANK in financial_ratios but missing from companies table
  Fix: Deleted 12 orphan rows from financial_ratios
- jupyter>=7.0 not available on Python 3.13
  Fix: Installed jupyter without version constraint
- ModuleNotFoundError when running scripts directly
  Fix: Added conftest.py and run_etl.py at root level

## Exit Criteria Status
- 92 companies loaded: PASS
- 0 CRITICAL DQ violations: PASS
- 45 ETL unit tests passing: PASS
- load_audit.csv generated: PASS
- FK integrity check: PASS
- Manual review of 5 companies: PASS

## Sprint 1 Verdict: COMPLETE
## Ready for Sprint 2: Financial Ratio Engine
