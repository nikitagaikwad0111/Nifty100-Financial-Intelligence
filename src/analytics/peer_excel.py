# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

DB_PATH = 'data/nifty100.db'

GREEN  = PatternFill('solid', fgColor='C8E6C9')
YELLOW = PatternFill('solid', fgColor='FFF9C4')
RED    = PatternFill('solid', fgColor='FFCDD2')
GOLD   = PatternFill('solid', fgColor='FFD54F')
HEADER = PatternFill('solid', fgColor='1A237E')
HEADER_FONT = Font(bold=True, color='FFFFFF', size=10)
TITLE_FONT  = Font(bold=True, size=13, color='1A237E')
BENCH_FONT  = Font(bold=True, size=10, color='1A237E')
NORMAL_FONT = Font(size=10)
THIN = Border(
    left=Side(style='thin'), right=Side(style='thin'),
    top=Side(style='thin'), bottom=Side(style='thin')
)

METRICS = [
    ('return_on_equity_pct',  'ROE %',        8),
    ('return_on_capital_pct', 'ROCE %',       8),
    ('net_profit_margin_pct', 'NPM %',        8),
    ('debt_to_equity',        'D/E',          8),
    ('free_cash_flow_cr',     'FCF (Cr)',    12),
    ('pat_cagr_5yr',          'PAT CAGR 5yr',12),
    ('revenue_cagr_5yr',      'Rev CAGR 5yr',12),
    ('eps_cagr_5yr',          'EPS CAGR 5yr',12),
    ('interest_coverage',     'ICR',          8),
    ('asset_turnover',        'Asset T/O',   10),
]

def pct_fill(rank):
    if rank is None:
        return YELLOW
    try:
        r = float(rank)
    except (TypeError, ValueError):
        return YELLOW
    if r >= 0.75:
        return GREEN
    elif r >= 0.25:
        return YELLOW
    else:
        return RED

def load_data():
    conn = sqlite3.connect(DB_PATH)
    peer_groups = pd.read_sql('SELECT * FROM peer_groups', conn)
    percentiles = pd.read_sql('SELECT * FROM peer_percentiles', conn)
    ratios = pd.read_sql('''
        SELECT fr.company_id, c.company_name, fr.year,
               fr.return_on_equity_pct, fr.return_on_capital_pct,
               fr.net_profit_margin_pct, fr.debt_to_equity,
               fr.free_cash_flow_cr, fr.pat_cagr_5yr,
               fr.revenue_cagr_5yr, fr.eps_cagr_5yr,
               fr.interest_coverage, fr.asset_turnover
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        WHERE fr.year = (
            SELECT MAX(year) FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id
            AND fr2.year LIKE
            "'%-03'"
        )
    ''', conn)
    conn.close()
    return peer_groups, percentiles, ratios

def write_group_sheet(wb, group_name, members_df,
                      percentiles, ratios):
    sheet_title = group_name[:31]
    ws = wb.create_sheet(title=sheet_title)
    ws.merge_cells('A1:X1')
    ws['A1'] = group_name
    ws['A1'].font = TITLE_FONT
    ws['A1'].alignment = Alignment(horizontal='center')
    ws.row_dimensions[1].height = 25
    ws.merge_cells('A2:X2')
    ws['A2'] = 'Green >= 75th percentile | Yellow 25th-75th | Red <= 25th | Gold = Benchmark'
    ws['A2'].font = Font(italic=True, size=9, color='455A64')
    ws['A2'].alignment = Alignment(horizontal='center')
    headers = ['Ticker', 'Company Name', 'Benchmark']
    widths  = [10, 28, 10]
    for metric_key, metric_label, col_width in METRICS:
        headers.append(metric_label)
        widths.append(col_width)
        headers.append('Pct Rank')
        widths.append(9)
    for col_idx, (header, width) in enumerate(zip(headers, widths), start=1):
        cell = ws.cell(row=4, column=col_idx, value=header)
        cell.fill = HEADER
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal='center', wrap_text=True)
        cell.border = THIN
        ws.column_dimensions[get_column_letter(col_idx)].width = width
    ws.row_dimensions[4].height = 30
    member_ids = members_df['company_id'].tolist()
    benchmark_ids = members_df[members_df['is_benchmark'] == 1]['company_id'].tolist()
    company_ratios = ratios[ratios['company_id'].isin(member_ids)]
    group_pct = percentiles[percentiles['peer_group_name'] == group_name]
    median_row_data = {}
    for row_idx, company_id in enumerate(member_ids, start=5):
        co_ratios = company_ratios[company_ratios['company_id'] == company_id]
        if co_ratios.empty:
            continue
        co_data = co_ratios.iloc[0]
        is_bench = company_id in benchmark_ids
        col = 1
        cell = ws.cell(row=row_idx, column=col, value=company_id)
        cell.font = BENCH_FONT if is_bench else NORMAL_FONT
        cell.fill = GOLD if is_bench else PatternFill()
        cell.border = THIN
        cell.alignment = Alignment(horizontal='center')
        col += 1
        cell = ws.cell(row=row_idx, column=col, value=co_data.get('company_name', ''))
        cell.font = BENCH_FONT if is_bench else NORMAL_FONT
        cell.fill = GOLD if is_bench else PatternFill()
        cell.border = THIN
        col += 1
        cell = ws.cell(row=row_idx, column=col, value='YES' if is_bench else '')
        cell.font = BENCH_FONT if is_bench else NORMAL_FONT
        cell.fill = GOLD if is_bench else PatternFill()
        cell.border = THIN
        cell.alignment = Alignment(horizontal='center')
        col += 1
        for metric_key, metric_label, _ in METRICS:
            raw_val = co_data.get(metric_key)
            display_val = round(float(raw_val), 2) if raw_val is not None else None
            co_pct_row = group_pct[
                (group_pct['company_id'] == company_id) &
                (group_pct['metric'] == metric_key)
            ]
            pct_rank = co_pct_row['percentile_rank'].values[0] if not co_pct_row.empty else None
            if metric_key not in median_row_data:
                median_row_data[metric_key] = []
            if display_val is not None:
                median_row_data[metric_key].append(display_val)
            val_cell = ws.cell(row=row_idx, column=col, value=display_val)
            val_cell.font = BENCH_FONT if is_bench else NORMAL_FONT
            val_cell.fill = GOLD if is_bench else PatternFill()
            val_cell.border = THIN
            val_cell.alignment = Alignment(horizontal='center')
            col += 1
            pct_cell = ws.cell(row=row_idx, column=col,
                value=round(float(pct_rank), 2) if pct_rank is not None else None)
            pct_cell.font = BENCH_FONT if is_bench else NORMAL_FONT
            pct_cell.fill = pct_fill(pct_rank) if not is_bench else GOLD
            pct_cell.border = THIN
            pct_cell.alignment = Alignment(horizontal='center')
            col += 1
        ws.row_dimensions[row_idx].height = 18
    median_row = len(member_ids) + 6
    ws.merge_cells('A' + str(median_row) + ':C' + str(median_row))
    ws.cell(row=median_row, column=1, value='PEER GROUP MEDIAN').font = Font(bold=True, size=10)
    col = 4
    for metric_key, _, _ in METRICS:
        vals = median_row_data.get(metric_key, [])
        median_val = round(pd.Series(vals).median(), 2) if vals else None
        med_cell = ws.cell(row=median_row, column=col, value=median_val)
        med_cell.font = Font(bold=True, size=10)
        med_cell.fill = PatternFill('solid', fgColor='E3F2FD')
        med_cell.border = THIN
        med_cell.alignment = Alignment(horizontal='center')
        col += 2
    ws.freeze_panes = 'A5'

def generate_peer_excel():
    peer_groups, percentiles, ratios = load_data()
    wb = Workbook()
    wb.remove(wb.active)
    for group_name in peer_groups['peer_group_name'].unique():
        members = peer_groups[peer_groups['peer_group_name'] == group_name]
        print('Writing sheet: ' + group_name)
        write_group_sheet(wb, group_name, members, percentiles, ratios)
    os.makedirs('output', exist_ok=True)
    out_path = 'output/peer_comparison.xlsx'
    wb.save(out_path)
    print('Saved: ' + out_path)
    return out_path

if __name__ == '__main__':
    path = generate_peer_excel()
    print('Done! Open ' + path + ' to view.')