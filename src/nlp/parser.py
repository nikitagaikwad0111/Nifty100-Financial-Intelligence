# -*- coding: utf-8 -*-
import re
import pandas as pd
import sqlite3
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

DB_PATH = 'data/nifty100.db'

PATTERN = re.compile(
    r'(\d+)\s*Years?:?\s*([\d.]+)%',
    re.IGNORECASE
)

METRIC_MAP = {
    'compounded_sales_growth':   'revenue_cagr',
    'compounded_profit_growth':  'pat_cagr',
    'stock_price_cagr':          'price_cagr',
    'roe':                       'roe_history',
}

def parse_text_field(text):
    if not text or str(text).strip() == 'nan':
        return []
    results = []
    for match in PATTERN.finditer(str(text)):
        period = int(match.group(1))
        value  = float(match.group(2))
        results.append((period, value))
    return results

def parse_analysis_table():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM analysis', conn)
    conn.close()
    print(f'Loaded {len(df)} rows from analysis table')
    print(f'Columns: {df.columns.tolist()}')

    parsed_rows = []
    failure_rows = []

    for _, row in df.iterrows():
        company_id = row.get('company_id', '')
        for field, metric_type in METRIC_MAP.items():
            raw_text = row.get(field, '')
            matches = parse_text_field(raw_text)
            if matches:
                for period, value in matches:
                    parsed_rows.append({
                        'company_id':  company_id,
                        'metric_type': metric_type,
                        'period_years': period,
                        'value_pct':   value,
                        'raw_text':    str(raw_text)[:100],
                    })
            else:
                if raw_text and str(raw_text).strip() not in ['nan', '']:
                    failure_rows.append({
                        'company_id':  company_id,
                        'field':       field,
                        'raw_text':    str(raw_text)[:200],
                    })

    parsed_df = pd.DataFrame(parsed_rows)
    failure_df = pd.DataFrame(failure_rows)

    os.makedirs('output', exist_ok=True)
    parsed_df.to_csv('output/analysis_parsed.csv', index=False)
    failure_df.to_csv('output/parse_failures.csv', index=False)

    print(f'Parsed rows: {len(parsed_df)}')
    print(f'Parse failures: {len(failure_df)}')
    return parsed_df, failure_df

def cross_validate(parsed_df):
    conn = sqlite3.connect(DB_PATH)
    ratios = pd.read_sql(
        'SELECT * FROM financial_ratios', conn)
    conn.close()

    divergences = []
    revenue_parsed = parsed_df[
        parsed_df['metric_type'] == 'revenue_cagr'
    ]

    for _, row in revenue_parsed.iterrows():
        company_id = row['company_id']
        period = row['period_years']
        parsed_val = row['value_pct']

        col = f'revenue_cagr_{period}yr'
        if col not in ratios.columns:
            continue

        co_ratios = ratios[
            ratios['company_id'] == company_id
        ].sort_values('year')

        if co_ratios.empty:
            continue

        computed_val = co_ratios.iloc[-1].get(col)
        if computed_val is None or pd.isna(computed_val):
            continue

        diff = abs(float(parsed_val) - float(computed_val))
        if diff > 5:
            divergences.append({
                'company_id':   company_id,
                'period_years': period,
                'parsed_val':   parsed_val,
                'computed_val': round(float(computed_val), 2),
                'diff':         round(diff, 2),
            })

    div_df = pd.DataFrame(divergences)
    if not div_df.empty:
        div_df.to_csv('output/cagr_divergences.csv', index=False)
        print(f'CAGR divergences > 5%: {len(div_df)}')
        print(div_df.to_string())
    else:
        print('No CAGR divergences > 5% found')
    return div_df

if __name__ == '__main__':
    print('=== NLP Analysis Parser ===')
    parsed_df, failure_df = parse_analysis_table()
    print('\nSample parsed rows:')
    print(parsed_df.head(10).to_string())
    print('\nCross-validating CAGR values...')
    div_df = cross_validate(parsed_df)
    print('\nDone! Files saved to output/')