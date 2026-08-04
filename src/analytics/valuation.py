# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

DB_PATH = 'data/nifty100.db'

def load_valuation_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('''
        SELECT mc.company_id, c.company_name,
               s.broad_sector, mc.year,
               mc.pe_ratio, mc.pb_ratio,
               mc.ev_ebitda, mc.market_cap_crore,
               mc.enterprise_value_crore,
               mc.dividend_yield_pct,
               fr.free_cash_flow_cr
        FROM market_cap mc
        JOIN companies c ON mc.company_id = c.id
        JOIN sectors s ON mc.company_id = s.company_id
        LEFT JOIN financial_ratios fr
            ON mc.company_id = fr.company_id
            AND fr.year LIKE mc.year || "-%%"
    ''', conn)
    conn.close()
    return df

def compute_fcf_yield(df):
    df = df.copy()
    df['fcf_yield_pct'] = None
    mask = (
        df['market_cap_crore'].notna() &
        df['free_cash_flow_cr'].notna() &
        (df['market_cap_crore'] > 0)
    )
    df.loc[mask, 'fcf_yield_pct'] = (
        df.loc[mask, 'free_cash_flow_cr'] /
        df.loc[mask, 'market_cap_crore'] * 100
    ).round(2)
    return df

def compute_sector_median_pe(df):
    latest = df[df['year'] == df['year'].max()].copy()
    sector_pe = latest.groupby('broad_sector')['pe_ratio'].median()
    return sector_pe

def apply_valuation_flags(df, sector_pe):
    df = df.copy()
    df['sector_median_pe'] = df['broad_sector'].map(sector_pe)
    df['pe_vs_sector_pct'] = None
    df['flag'] = 'Fair'
    mask = (
        df['pe_ratio'].notna() &
        df['sector_median_pe'].notna() &
        (df['sector_median_pe'] > 0)
    )
    df.loc[mask, 'pe_vs_sector_pct'] = (
        (df.loc[mask, 'pe_ratio'] -
         df.loc[mask, 'sector_median_pe']) /
        df.loc[mask, 'sector_median_pe'] * 100
    ).round(2)
    caution_mask = mask & (
        df['pe_ratio'] > df['sector_median_pe'] * 1.5
    )
    discount_mask = mask & (
        df['pe_ratio'] < df['sector_median_pe'] * 0.7
    )
    df.loc[caution_mask, 'flag'] = 'Caution'
    df.loc[discount_mask, 'flag'] = 'Discount'
    return df

def compute_5yr_median_pe(df):
    median_pe = df.groupby('company_id')['pe_ratio'].median()
    return median_pe.rename('pe_5yr_median')

def generate_valuation_summary():
    print('Loading data...')
    df = load_valuation_data()
    print(f'Loaded {len(df)} rows')

    print('Computing FCF yield...')
    df = compute_fcf_yield(df)

    print('Computing sector median P/E...')
    sector_pe = compute_sector_median_pe(df)
    print('Sector P/E medians:')
    print(sector_pe)

    print('Applying valuation flags...')
    latest_year = df['year'].max()
    latest = df[df['year'] == latest_year].copy()
    latest = apply_valuation_flags(latest, sector_pe)

    print('Computing 5yr median P/E...')
    pe_5yr = compute_5yr_median_pe(df)
    latest = latest.merge(
        pe_5yr, on='company_id', how='left')

    output = latest[[
        'company_id', 'company_name', 'broad_sector',
        'pe_ratio', 'pb_ratio', 'ev_ebitda',
        'fcf_yield_pct', 'pe_5yr_median',
        'sector_median_pe', 'pe_vs_sector_pct', 'flag'
    ]].copy()
    output.columns = [
        'company_id', 'company_name', 'sector',
        'P/E', 'P/B', 'EV/EBITDA',
        'FCF_yield_pct', '5yr_median_PE',
        'sector_median_PE', 'PE_vs_sector_pct', 'flag'
    ]

    os.makedirs('output', exist_ok=True)
    output.to_excel(
        'output/valuation_summary.xlsx',
        index=False
    )
    print(f'valuation_summary.xlsx saved: {len(output)} rows')

    flags = output[output['flag'].isin(['Caution', 'Discount'])]
    flags.to_csv('output/valuation_flags.csv', index=False)
    print(f'valuation_flags.csv saved: {len(flags)} flagged companies')

    print('\nFlag distribution:')
    print(output['flag'].value_counts())

    return output

if __name__ == '__main__':
    result = generate_valuation_summary()
    print('\nSample output:')
    print(result[['company_id', 'P/E', 'flag',
                   'PE_vs_sector_pct']].head(10).to_string())
    print('\nDone!')