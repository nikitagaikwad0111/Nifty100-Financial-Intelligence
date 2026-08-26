# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

DB_PATH = 'data/nifty100.db'

def run_capital_allocation_report():
    conn = sqlite3.connect(DB_PATH)
    sql1 = 'SELECT company_id, year, capital_allocation_pattern FROM financial_ratios ORDER BY company_id, year'
    fr = pd.read_sql(sql1, conn)
    sectors = pd.read_sql('SELECT * FROM sectors', conn)
    companies = pd.read_sql('SELECT id, company_name FROM companies', conn)
    conn.close()

    sector_map = dict(zip(sectors['company_id'], sectors['broad_sector']))
    name_map = dict(zip(companies['id'], companies['company_name']))

    cap_csv = pd.read_csv('output/capital_allocation.csv')
    print(f'capital_allocation.csv rows: {len(cap_csv)}')
    print(f'Companies covered: {cap_csv["company_id"].nunique()}')

    latest_year = fr[fr['year'].str.endswith('-03')]['year'].max()
    print(f'Latest year: {latest_year}')

    latest = fr[fr['year'] == latest_year]
    print('Capital Allocation Distribution (latest year):')
    dist = latest['capital_allocation_pattern'].value_counts()
    print(dist)

    march_years = fr[fr['year'].str.endswith('-03')]
    march_years = march_years.sort_values(['company_id', 'year'])

    changes = []
    for company_id, group in march_years.groupby('company_id'):
        group = group.sort_values('year')
        if len(group) < 2:
            continue
        for i in range(1, len(group)):
            prev = group.iloc[i-1]
            curr = group.iloc[i]
            if prev['capital_allocation_pattern'] != curr['capital_allocation_pattern']:
                changes.append({
                    'company_id':   company_id,
                    'company_name': name_map.get(company_id, ''),
                    'sector':       sector_map.get(company_id, ''),
                    'from_year':    prev['year'],
                    'to_year':      curr['year'],
                    'from_pattern': prev['capital_allocation_pattern'],
                    'to_pattern':   curr['capital_allocation_pattern'],
                })

    changes_df = pd.DataFrame(changes)
    os.makedirs('output', exist_ok=True)
    changes_df.to_csv('output/pattern_changes.csv', index=False)
    print(f'Pattern changes detected: {len(changes_df)}')
    print(f'Companies with changes: {changes_df["company_id"].nunique()}')

    if not changes_df.empty:
        print('Top 10 most common pattern transitions:')
        transitions = changes_df.groupby(['from_pattern', 'to_pattern']).size().reset_index(name='count')
        transitions = transitions.sort_values('count', ascending=False)
        print(transitions.head(10).to_string())

    if not changes_df.empty:
        print('Worrying transitions (to Distress Signal):')
        distress = changes_df[changes_df['to_pattern'] == 'Distress Signal']
        if not distress.empty:
            print(distress[['company_id', 'from_year', 'to_year', 'from_pattern']].to_string())
        else:
            print('None found')

    if not changes_df.empty:
        positive = changes_df[changes_df['to_pattern'] == 'Reinvestor']
        print(f'Positive transitions to Reinvestor: {len(positive)}')

    print('Done! output/pattern_changes.csv saved.')
    return changes_df

if __name__ == '__main__':
    df = run_capital_allocation_report()