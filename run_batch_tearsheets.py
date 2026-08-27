# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import sys
import csv
sys.path.insert(0, os.path.abspath('.'))
from src.reports.tearsheet import generate_tearsheet

DB_PATH = 'data/nifty100.db'

def run_batch_tearsheets():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql('SELECT id FROM companies', conn)
    pl_counts = pd.read_sql(
        'SELECT company_id, COUNT(*) as cnt FROM profitandloss GROUP BY company_id',
        conn)
    conn.close()

    count_map = dict(zip(pl_counts['company_id'], pl_counts['cnt']))
    company_ids = companies['id'].tolist()

    generated = []
    skipped = []

    print(f'Generating tearsheets for {len(company_ids)} companies...')
    print('-' * 50)

    for i, ticker in enumerate(company_ids, 1):
        years = count_map.get(ticker, 0)
        if years < 3:
            print(f'SKIP {ticker} — only {years} years of data')
            skipped.append({'company_id': ticker, 'reason': f'Only {years} years'})
            continue
        try:
            size_kb = generate_tearsheet(ticker)
            generated.append({'company_id': ticker, 'size_kb': size_kb})
            if i % 10 == 0:
                print(f'Progress: {i}/{len(company_ids)} done...')
        except Exception as e:
            print(f'ERROR {ticker}: {e}')
            skipped.append({'company_id': ticker, 'reason': str(e)})

    os.makedirs('output', exist_ok=True)
    skip_df = pd.DataFrame(skipped)
    skip_df.to_csv('output/skipped_tearsheets.csv', index=False)

    total = len(generated)
    print(f'\nGenerated: {total} tearsheets')
    print(f'Skipped:   {len(skipped)} companies')

    # Verify count
    pdf_count = len([
        f for f in os.listdir('reports/tearsheets')
        if f.endswith('.pdf')
    ])
    print(f'PDF files in reports/tearsheets/: {pdf_count}')

    # Size check
    sizes = [r['size_kb'] for r in generated if r['size_kb']]
    if sizes:
        print(f'Min size: {min(sizes)} KB')
        print(f'Max size: {max(sizes)} KB')
        print(f'Avg size: {round(sum(sizes)/len(sizes), 1)} KB')
        small = [r for r in generated if r['size_kb'] and r['size_kb'] < 30]
        print(f'PDFs under 30KB: {len(small)}')

    return generated, skipped

if __name__ == '__main__':
    generated, skipped = run_batch_tearsheets()
    print('\nDone! All tearsheets saved to reports/tearsheets/')