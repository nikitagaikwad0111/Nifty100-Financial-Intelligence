# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

DB_PATH = 'data/nifty100.db'

def load_data():
    conn = sqlite3.connect(DB_PATH)
    ratios = pd.read_sql('SELECT * FROM financial_ratios', conn)
    companies = pd.read_sql('SELECT * FROM companies', conn)
    sectors = pd.read_sql('SELECT * FROM sectors', conn)
    conn.close()
    return ratios, companies, sectors

def get_latest(ratios, company_id):
    co = ratios[ratios['company_id'] == company_id]
    co = co[co['year'].str.endswith('-03')]
    if co.empty:
        return None
    return co.sort_values('year').iloc[-1]

def get_history(ratios, company_id, n=5):
    co = ratios[ratios['company_id'] == company_id]
    co = co[co['year'].str.endswith('-03')]
    return co.sort_values('year').tail(n)

def safe_float(val):
    try:
        return float(val)
    except:
        return None

def check_sustained_roe(hist, threshold=20, years=3):
    vals = [safe_float(v) for v in hist['return_on_equity_pct']]
    vals = [v for v in vals if v is not None]
    if len(vals) >= years:
        return all(v > threshold for v in vals[-years:])
    return False

def check_consecutive_positive(series, years=5):
    vals = [safe_float(v) for v in series]
    vals = [v for v in vals if v is not None]
    if len(vals) >= years:
        return all(v > 0 for v in vals[-years:])
    return False

def check_improving(series, years=3):
    vals = [safe_float(v) for v in series]
    vals = [v for v in vals if v is not None]
    if len(vals) >= years:
        recent = vals[-years:]
        return all(recent[i] < recent[i+1]
                   for i in range(len(recent)-1))
    return False

def check_declining(series, years=3):
    vals = [safe_float(v) for v in series]
    vals = [v for v in vals if v is not None]
    if len(vals) >= years:
        recent = vals[-years:]
        return all(recent[i] > recent[i+1]
                   for i in range(len(recent)-1))
    return False

def generate_pros_cons(company_id, ratios, broad_sector):
    latest = get_latest(ratios, company_id)
    hist   = get_history(ratios, company_id, 5)
    hist3  = get_history(ratios, company_id, 3)
    results = []

    if latest is None:
        return results

    roe   = safe_float(latest.get('return_on_equity_pct'))
    roce  = safe_float(latest.get('return_on_capital_pct'))
    de    = safe_float(latest.get('debt_to_equity'))
    fcf   = safe_float(latest.get('free_cash_flow_cr'))
    opm   = safe_float(latest.get('operating_profit_margin_pct'))
    npm   = safe_float(latest.get('net_profit_margin_pct'))
    rev5  = safe_float(latest.get('revenue_cagr_5yr'))
    pat5  = safe_float(latest.get('pat_cagr_5yr'))
    eps5  = safe_float(latest.get('eps_cagr_5yr'))
    icr   = safe_float(latest.get('interest_coverage'))
    icr_l = str(latest.get('icr_label', ''))
    div_y = safe_float(latest.get('dividend_payout_ratio_pct'))
    borrow= safe_float(latest.get('total_debt_cr'))
    nd    = safe_float(latest.get('net_debt_cr'))
    ebitda= safe_float(latest.get('operating_profit_margin_pct'))

    # PRO RULES
    if check_sustained_roe(hist, 20, 3):
        results.append((
            'pro', 'PRO_01',
            'Consistently high return on equity above 20% demonstrates exceptional capital efficiency',
            90
        ))

    if check_consecutive_positive(hist['free_cash_flow_cr'], 5):
        results.append((
            'pro', 'PRO_02',
            'Strong free cash flow generation over 5 years signals healthy business fundamentals',
            95
        ))

    if de is not None and de == 0:
        results.append((
            'pro', 'PRO_03',
            'Debt-free balance sheet provides financial flexibility and eliminates interest burden',
            100
        ))

    if rev5 is not None and rev5 > 15:
        conf = min(100, int(70 + (rev5 - 15) * 2))
        results.append((
            'pro', 'PRO_04',
            'Revenue growing at above 15% CAGR over 5 years reflects strong business momentum',
            conf
        ))

    if opm is not None and opm > 25:
        conf = min(100, int(70 + (opm - 25) * 2))
        results.append((
            'pro', 'PRO_05',
            'Operating profit margin above 25% indicates strong pricing power and cost discipline',
            conf
        ))

    if pat5 is not None and pat5 > 20:
        conf = min(100, int(70 + (pat5 - 20) * 2))
        results.append((
            'pro', 'PRO_06',
            'Net profit compounding at above 20% over 5 years creates significant shareholder value',
            conf
        ))

    if icr_l == 'Debt Free' or (icr is not None and icr > 10):
        results.append((
            'pro', 'PRO_07',
            'Very high interest coverage ratio reflects negligible financial stress from debt servicing',
            90
        ))

    if (div_y is not None and div_y > 2 and
            fcf is not None and fcf > 0):
        results.append((
            'pro', 'PRO_08',
            'Consistent dividend yield above 2% backed by positive free cash flow',
            85
        ))

    if eps5 is not None and eps5 > 15:
        conf = min(100, int(70 + (eps5 - 15) * 2))
        results.append((
            'pro', 'PRO_09',
            'Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding',
            conf
        ))

    if check_improving(hist['return_on_equity_pct'], 3):
        results.append((
            'pro', 'PRO_10',
            'Return on equity improving for 3 consecutive years shows strengthening business quality',
            80
        ))

    if (rev5 is not None and pat5 is not None and
            pat5 > rev5 and rev5 > 0):
        results.append((
            'pro', 'PRO_11',
            'Revenue growing slower than profits shows improving operating leverage and scale benefits',
            75
        ))

    # CON RULES
    if (de is not None and de > 2.0 and
            broad_sector != 'Financials'):
        conf = min(100, int(70 + (de - 2.0) * 10))
        results.append((
            'con', 'CON_01',
            f'Debt-to-equity ratio of {round(de,1)} is elevated for a non-financial company and warrants monitoring',
            conf
        ))

    if check_consecutive_positive(
            [-v if v else None
             for v in hist['free_cash_flow_cr']], 3):
        results.append((
            'con', 'CON_02',
            'Free cash flow negative for 3 consecutive years raises concern about cash generation quality',
            90
        ))

    if check_declining(hist['operating_profit_margin_pct'], 3):
        results.append((
            'con', 'CON_03',
            'Operating margins declining for 3 consecutive years suggest pricing or cost pressure',
            85
        ))

    if npm is not None and npm < 0:
        results.append((
            'con', 'CON_04',
            'Company reported a net loss in the most recent financial year',
            100
        ))

    if check_declining(hist['revenue_cagr_5yr'], 2):
        results.append((
            'con', 'CON_05',
            'Revenue contraction over 2 consecutive years indicates demand weakness or market share loss',
            85
        ))

    if icr is not None and icr < 1.5:
        results.append((
            'con', 'CON_06',
            'Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations',
            95
        ))

    if div_y is not None and div_y > 100:
        results.append((
            'con', 'CON_07',
            'Dividend payout ratio above 100% means the company is paying dividends from reserves which is unsustainable',
            90
        ))

    if check_improving(hist['debt_to_equity'], 3):
        results.append((
            'con', 'CON_08',
            'Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk',
            80
        ))

    if check_declining(hist['earnings_per_share'], 3):
        results.append((
            'con', 'CON_09',
            'Earnings per share declining for 3 consecutive years reflects deteriorating profitability',
            85
        ))

    if roce is not None and roce < 10:
        results.append((
            'con', 'CON_10',
            'Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital',
            85
        ))

    if rev5 is not None and rev5 < 5:
        results.append((
            'con', 'CON_12',
            'Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum',
            80
        ))

    return results

def run_generator():
    print('Loading data...')
    ratios, companies, sectors = load_data()
    sector_map = dict(zip(sectors['company_id'],
                          sectors['broad_sector']))

    all_rows = []
    company_ids = companies['id'].tolist()
    print(f'Generating pros/cons for {len(company_ids)} companies...')

    for company_id in company_ids:
        broad_sector = sector_map.get(company_id, '')
        results = generate_pros_cons(
            company_id, ratios, broad_sector)

        # Filter by confidence > 60
        results = [r for r in results if r[3] > 60]

        # Ensure at least 1 pro and 1 con
        pros = [r for r in results if r[0] == 'pro']
        cons = [r for r in results if r[0] == 'con']

        # Fallback pro
        if not pros:
            pros = [('pro', 'PRO_FB',
                     'Company is part of Nifty 100 index reflecting large-cap market significance',
                     65)]

        # Fallback con
        if not cons:
            cons = [('con', 'CON_FB',
                     'Limited financial history available for comprehensive analysis',
                     65)]

        for item in pros + cons:
            all_rows.append({
                'company_id':    company_id,
                'type':          item[0],
                'rule_id':       item[1],
                'text':          item[2],
                'confidence_pct': item[3],
            })

    df = pd.DataFrame(all_rows)
    os.makedirs('output', exist_ok=True)
    df.to_csv('output/pros_cons_generated.csv', index=False)
    print(f'Total rows: {len(df)}')
    print(f'Companies covered: {df["company_id"].nunique()}')

    # Verify every company has at least 1 pro and 1 con
    pros_count = df[df['type']=='pro']['company_id'].nunique()
    cons_count = df[df['type']=='con']['company_id'].nunique()
    print(f'Companies with pros: {pros_count}')
    print(f'Companies with cons: {cons_count}')

    # Sample output
    print('\nSample — TCS:')
    print(df[df['company_id']=='TCS'][
        ['type','rule_id','text','confidence_pct']
    ].to_string())
    return df

if __name__ == '__main__':
    df = run_generator()
    print('\nDone! output/pros_cons_generated.csv saved.')