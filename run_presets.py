import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.screener.engine import run_screener

presets = [
    "quality_compounder",
    "value_pick",
    "growth_accelerator",
    "dividend_champion",
    "debt_free_blue_chip",
    "turnaround_watch"
]

print("=" * 70)
print("SPRINT 3 DAY 16 — ALL 6 PRESET SCREENERS")
print("Exit criteria: each must return 5-50 companies")
print("=" * 70)

all_pass = True

for preset in presets:
    print(f"\n{'=' * 70}")
    print(f"PRESET: {preset.upper()}")
    print("=" * 70)

    try:
        results = run_screener(preset_name=preset)
        count = len(results)
        status = "PASS ✅" if 5 <= count <= 50 else "FAIL ❌"
        if not (5 <= count <= 50):
            all_pass = False

        print(f"Companies found: {count} — {status}")
        print(f"\nTop 10 results:")
        cols = ["company_id", "company_name",
                "broad_sector", "composite_quality_score"]

        # Add relevant columns per preset
        if preset == "quality_compounder":
            cols += ["return_on_equity_pct",
                     "debt_to_equity", "free_cash_flow_cr",
                     "revenue_cagr_5yr"]
        elif preset == "value_pick":
            cols += ["pe_ratio", "pb_ratio",
                     "debt_to_equity", "dividend_yield_pct"]
        elif preset == "growth_accelerator":
            cols += ["revenue_cagr_5yr",
                     "pat_cagr_5yr", "debt_to_equity"]
        elif preset == "dividend_champion":
            cols += ["dividend_yield_pct",
                     "dividend_payout_ratio_pct", "free_cash_flow_cr"]
        elif preset == "debt_free_blue_chip":
            cols += ["debt_to_equity",
                     "return_on_equity_pct"]
        elif preset == "turnaround_watch":
            cols += ["revenue_cagr_3yr",
                     "free_cash_flow_cr", "debt_to_equity"]

        available = [c for c in cols if c in results.columns]
        print(results[available].head(10).to_string())

    except Exception as e:
        print(f"ERROR: {e}")
        all_pass = False

print(f"\n{'=' * 70}")
print("SUMMARY")
print("=" * 70)
print(f"Overall status: {'ALL PASS ✅' if all_pass else 'SOME FAILED ❌'}")