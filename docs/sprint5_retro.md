# Sprint 5 Retrospective
## Sprint: PDF Reports & Intelligence (Days 29-35)
## Date: August 2026

## What We Delivered

### Source Files Created
- src/nlp/parser.py: Analysis text parser using regex
- src/nlp/pros_cons_generator.py: 12 pro + 12 con rules
- src/analytics/cashflow_intelligence.py: CFO quality, CapEx intensity
- src/analytics/capital_allocation_report.py: Pattern change detection
- src/reports/tearsheet.py: 2-page company PDF tearsheet
- src/reports/portfolio_report.py: Portfolio summary PDF

### Output Files Generated
- output/analysis_parsed.csv: 63 rows parsed from analysis.xlsx
- output/parse_failures.csv: 17 unmatched entries logged
- output/cagr_divergences.csv: 1 divergence flagged (INFY 3yr)
- output/pros_cons_generated.csv: 560 rows for 92 companies
- output/cashflow_intelligence.xlsx: 92 rows
- output/distress_alerts.csv: 13 companies flagged
- output/pattern_changes.csv: 409 pattern changes across 84 companies
- output/skipped_tearsheets.csv: 1 company skipped (JIOFIN)
- reports/tearsheets/: 91 tearsheet PDFs
- reports/portfolio/: Portfolio summary PDF (150 KB, 92 pages)

## Key Results

### NLP Parser
- 63 rows successfully parsed from analysis.xlsx
- Regex pattern correctly extracts period and value
- 1 CAGR divergence found: INFY 3yr (parsed=5% vs computed=15.22%)
- Reason: analysis.xlsx data is older than our ratio engine data

### Pros/Cons Generator
- 560 total observations generated
- 92 companies with pros: ALL 92
- 92 companies with cons: ALL 92
- Fallback rules ensure every company has at least 1 pro and 1 con

### Cash Flow Intelligence
- CFO Quality: 62 High Quality, 17 Accrual Risk, 12 Moderate
- CapEx Intensity: 46 Capital Intensive, 24 Moderate, 21 Asset Light
- 13 distress signals (mostly banks/NBFCs - structurally normal)

### Capital Allocation
- 409 pattern changes detected across 84 companies
- Most common: Cash Accumulator to Reinvestor (83 times)
- 162 positive transitions to Reinvestor pattern

### PDF Reports
- 91 tearsheets generated (JIOFIN skipped - only 2 years data)
- Portfolio summary: 150 KB, 92 pages
- All tearsheets verified: no text overflow

## Issues Found and Fixed
1. cashflow_intelligence.py dangling if statement
   Fix: Restructured into proper if/else block
2. capital_allocation_report.py multi-line SQL string
   Fix: Rewrote entire file with single-line SQL
3. Tearsheet company name truncated at 50 chars
   Fix: Increased to 80 chars
4. Treemap blank due to negative FCF values
   Fix: Used count=1 as treemap size (Day 25 fix)

## Exit Criteria Status
- pros_cons_generated.csv has 1 pro + 1 con per company: PASS
- 91 tearsheets exist (92 minus JIOFIN): PASS
- Visual review confirmed no text overflow: PASS
- cashflow_intelligence.xlsx has 92 rows: PASS
- Portfolio PDF generated with 92 pages: PASS

## Sprint 5 Verdict: COMPLETE
## Ready for Sprint 6: API, ML & QA
