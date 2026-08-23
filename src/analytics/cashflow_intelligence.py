# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

DB_PATH = 'data/nifty100.db'

def load_data():
    conn = sqlite3.connect(DB_PATH)
    cf = pd.read_sql('SELECT * FROM cashflow', conn)
    pl = pd.read_sql('SELECT * FROM profitandloss', conn)
    bs = pd.read_sql('SELECT * FROM balancesheet', conn)
    fr = pd.read_sql('SELECT * FROM financial_ratios', conn)
    sectors = pd.read_sql('SELECT * FROM sectors', conn)
    companies = pd.read_sql('SELECT id FROM companies', conn)
    conn.close()
    return cf, pl, bs, fr, sectors, companies

def compute_cfo_quality(cf_co, pl_co):
    merged = cf_co.merge(
        pl_co[['company_id','year','net_profit']],
        on=['company_id','year'], how='inner'
    ).sort_values('year').tail(5)
    ratios = []
    for _, row in merged.iterrows():
        cfo = row.get('operating_activity')
        pat = row.get('net_profit')
        try:
            if pat and float(pat) != 0:
                ratios.append(float(cfo) / float(pat))
        except:
            pass
    if not ratios:
        return None, None
    avg = round(sum(ratios) / len(ratios), 2)
    if avg > 1.0:
        label = 'High Quality'
    elif avg >= 0.5:
        label = 'Moderate'
    else:
        label = 'Accrual Risk'
    return avg, label

def compute_capex_intensity(cf_co, pl_co):
    latest_cf = cf_co.sort_values('year').tail(1)
    if latest_cf.empty:
        return None, None
    year = latest_cf.iloc[0]['year']
    latest_pl = pl_co[pl_co['year'] == year]
    if latest_pl.empty:
        return None, None
    cfi = latest_cf.iloc[0].get('investing_activity')
    sales = latest_pl.iloc[0].get('sales')
    try:
        intensity = abs(float(cfi)) / float(sales) * 100
        intensity = round(intensity, 2)
    except:
        return None, None
    if intensity < 3:
        label = 'Asset Light'
    elif intensity <= 8:
        label = 'Moderate'
    else:
        label = 'Capital Intensive'
    return intensity, label

def detect_distress(cf_co):
    latest = cf_co.sort_values('year').tail(1)
    if latest.empty:
        return False
    row = latest.iloc[0]
    try:
        cfo = float(row.get('operating_activity', 0))
        cff = float(row.get('financing_activity', 0))
        return cfo < 0 and cff > 0
    except:
        return False

def detect_deleveraging(cf_co, bs_co):
    latest_cf = cf_co.sort_values('year').tail(1)
    if latest_cf.empty:
        return False
    try:
        cff = float(latest_cf.iloc[0].get('financing_activity', 0))
        bs_sorted = bs_co.sort_values('year')
        if len(bs_sorted) < 2:
            return False
        latest_debt = float(bs_sorted.iloc[-1].get('borrowings', 0) or 0)
        prior_debt  = float(bs_sorted.iloc[-2].get('borrowings', 0) or 0)
        return cff < 0 and latest_debt < prior_debt
    except:
        return False

def compute_fcf_cagr(fr_co):
    col = 'free_cash_flow_cr'
    if col not in fr_co.columns:
        return None
    fr_sorted = fr_co.sort_values('year')
    if len(fr_sorted) < 6:
        return None
    try:
        start = float(fr_sorted.iloc[-6][col])
        end   = float(fr_sorted.iloc[-1][col])
        if start <= 0 or end <= 0:
            return None
        cagr = ((end / start) ** (1/5) - 1) * 100
        return round(cagr, 2)
    except:
        return None

def run_cashflow_intelligence():
    print('Loading data...')
    cf, pl, bs, fr, sectors, companies = load_data()
    sector_map = dict(zip(sectors['company_id'],
                          sectors['broad_sector']))

    rows = []
    distress_rows = []
    company_ids = companies['id'].tolist()
    print(f'Processing {len(company_ids)} companies...')

    for company_id in company_ids:
        cf_co  = cf[cf['company_id'] == company_id]
        pl_co  = pl[pl['company_id'] == company_id]
        bs_co  = bs[bs['company_id'] == company_id]
        fr_co  = fr[fr['company_id'] == company_id]

        cfo_score, cfo_label = compute_cfo_quality(cf_co, pl_co)
        capex_pct, capex_label = compute_capex_intensity(cf_co, pl_co)
        distress = detect_distress(cf_co)
        delever  = detect_deleveraging(cf_co, bs_co)
        fcf_cagr = compute_fcf_cagr(fr_co)

        latest_fr = fr_co.sort_values('year').tail(1)
        if not latest_fr.empty:
            cap_alloc = latest_fr.iloc[0].get(
                'capital_allocation_pattern', 'Unknown')
            fcf_conv = latest_fr.iloc[0].get(
                'fcf_conversion_rate', None)
        else:
            cap_alloc = 'Unknown'
            fcf_conv = None

        rows.append({
            'company_id':          company_id,
            'sector':              sector_map.get(company_id, ''),
            'cfo_quality_score':   cfo_score,
            'cfo_quality_label':   cfo_label,
            'capex_intensity_pct': capex_pct,
            'capex_label':         capex_label,
            'fcf_cagr_5yr':        fcf_cagr,
            'fcf_conversion_pct':  fcf_conv,
            'distress_flag':       distress,
            'deleveraging_flag':   delever,
            'capital_allocation_label': cap_alloc,
        })

        if distress:
            latest_cf = cf_co.sort_values('year').tail(1)
            latest_pl = pl_co.sort_values('year').tail(1)
            distress_rows.append({
                'company_id': company_id,
                'sector':     sector_map.get(company_id, ''),
                'cfo':        latest_cf.iloc[0].get('operating_activity') if not latest_cf.empty else None,
                'cff':        latest_cf.iloc[0].get('financing_activity') if not latest_cf.empty else None,
                'net_profit': latest_pl.iloc[0].get('net_profit') if not latest_pl.empty else None,
            })

    df = pd.DataFrame(rows)
    distress_df = pd.DataFrame(distress_rows)

    os.makedirs('output', exist_ok=True)
    df.to_excel('output/cashflow_intelligence.xlsx', index=False)
    distress_df.to_csv('output/distress_alerts.csv', index=False)

    print(f'cashflow_intelligence.xlsx: {len(df)} rows')
    print(f'distress_alerts.csv: {len(distress_df)} companies flagged')
    print('\nCFO Quality distribution:')
    print(df['cfo_quality_label'].value_counts())
    print('\nCapEx Intensity distribution:')
    print(df['capex_label'].value_counts())
    print('\nDistress flags:', distress_df['company_id'].tolist())
    return df, distress_df

if __name__ == '__main__':
    df, distress_df = run_cashflow_intelligence()
    print('\nDone!')