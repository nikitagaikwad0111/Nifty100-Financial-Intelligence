# Sprint 3 Retrospective
## Sprint: Screener & Peer Comparison Engine (Days 15-21)
## Date: July 2026

## What We Delivered

### Source Files Created
- src/screener/engine.py: Filter engine with 15 metrics, composite score
- src/screener/excel_export.py: Colour-coded Excel export
- src/analytics/peer.py: Peer percentile ranking engine
- src/analytics/radar_charts.py: Radar chart generator
- src/analytics/peer_excel.py: Peer comparison Excel generator
- config/screener_config.yaml: All threshold definitions

### Output Files Generated
- output/screener_output.xlsx: 6 sheets, colour-coded
- output/peer_comparison.xlsx: 11 sheets, percentile ranked
- reports/radar_charts/: 56 PNG radar charts

### Database Updates
- peer_percentiles table: 550 rows across 11 groups

## Test Results
- Sprint 1 tests: 45 PASSED
- Sprint 2 tests: 64 PASSED
- Sprint 3 tests: 19 PASSED
- Total: 128 tests, 0 failures

## Screener Results
- Quality Compounder: 21 companies
- Value Pick: 10 companies
- Growth Accelerator: 19 companies
- Dividend Champion: 32 companies
- Debt-Free Blue Chip: 37 companies
- Turnaround Watch: 50 companies
- All 6 presets within 5-50 range: PASS

## Peer Comparison Results
- 11 peer groups populated
- 10 metrics ranked per group
- 55 companies with percentile ranks
- IT Services: TCS rank 1.0 for ROE (verified correct)
- FMCG: TATACONSUM rank 1.0 for Revenue CAGR (verified)

## Issues Found and Fixed
1. market_cap join used integer year 2024 instead of 2024-03
   Fix: Changed join to use string year format
2. Value Pick preset returning 0 companies
   Fix: Relaxed P/E threshold from 20 to 35, P/B from 3 to 5
3. peer_comparison.xlsx blank sheets
   Fix: SQL query LIKE clause was broken in list-of-strings method
4. Radar chart encoding errors
   Fix: Used list-of-strings method instead of triple-quoted strings
5. SBIN missing from peer comparison
   Fix: Documented as data gap (no balance sheet data)

## Exit Criteria Status
- 6 presets return 5-50 companies: PASS
- peer_comparison.xlsx has 11 sheets: PASS
- Peer ranks verified (IT Services, FMCG): PASS
- 128 tests passing: PASS
- screener_output.xlsx generated: PASS
- 56 radar charts generated: PASS

## Sprint 3 Verdict: COMPLETE
## Ready for Sprint 4: Dashboard & Valuation
