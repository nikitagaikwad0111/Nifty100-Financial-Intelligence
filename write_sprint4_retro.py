code = """# Sprint 4 Retrospective
## Sprint: Streamlit Dashboard & Valuation (Days 22-28)
## Date: July 2026

## What We Delivered

### Source Files Created
- src/dashboard/app.py: Main Streamlit entry point
- src/dashboard/pages/01_home.py: Market overview
- src/dashboard/pages/02_profile.py: Company deep dive
- src/dashboard/pages/03_screener.py: Filter engine UI
- src/dashboard/pages/04_peers.py: Peer comparison UI
- src/dashboard/pages/05_trends.py: 10-year trend charts
- src/dashboard/pages/06_sectors.py: Sector bubble chart
- src/dashboard/pages/07_capital.py: Capital allocation treemap
- src/dashboard/pages/08_reports.py: Annual report links
- src/dashboard/utils/db.py: Cached data loader
- src/analytics/valuation.py: FCF yield and P/E flags

### Output Files Generated
- output/valuation_summary.xlsx: 92 companies with flags
- output/valuation_flags.csv: 44 flagged companies

## Dashboard Features
- 8 screens all loading without errors
- All 10 test tickers working correctly
- Load times under 0.01 seconds (well under 3s target)
- CSV export working on screener screen
- Plotly interactive charts on all screens

## Valuation Results
- 92 companies analysed
- Fair: 48 companies
- Discount: 30 companies
- Caution: 14 companies
- ABB, NESTLEIND flagged as Caution (high P/E vs sector)

## Issues Found and Fixed
1. get_latest_ratios() SQL LIKE clause broken in list method
   Fix: Used two-step merge approach instead
2. composite_quality_score missing from financial_ratios table
   Fix: Computed on-the-fly in dashboard pages
3. Capital allocation treemap blank (negative FCF values)
   Fix: Used count=1 as size instead of FCF value
4. Streamlit welcome email prompt on first run
   Fix: Press Enter to skip (one-time only)

## QA Results
- 10 tickers tested across all sectors: ALL PASS
- Extreme screener values: No crash
- Partial data (JIOFIN 2yr): No crash
- All 19 deliverables exist: ALL EXIST
- Load times: All under 0.01s (target was 3s)

## Exit Criteria Status
- All 8 screens load without errors: PASS
- Profile screen loads under 3 seconds: PASS (0.006s)
- Screener CSV download works: PASS
- valuation_summary.xlsx has 92 rows: PASS
- README updated with run instructions: PASS

## Sprint 4 Verdict: COMPLETE
## Ready for Sprint 5: PDF Reports & Intelligence
"""

with open("docs/sprint4_retro.md", "w") as f:
    f.write(code)

print("Done! sprint4_retro.md written.")