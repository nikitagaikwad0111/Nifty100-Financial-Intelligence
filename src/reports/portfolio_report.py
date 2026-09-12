# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph,
    Spacer, Table, TableStyle, PageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

DB_PATH = 'data/nifty100.db'
OUTPUT_DIR = 'reports/portfolio'
PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm
UW = PAGE_W - 2 * MARGIN

NAVY  = colors.HexColor('#1A237E')
GREEN = colors.HexColor('#2E7D32')
RED   = colors.HexColor('#C62828')
LGREY = colors.HexColor('#F5F5F5')
WHITE = colors.white

H1 = ParagraphStyle('H1', fontSize=14, leading= 16, textColor=WHITE,
    fontName='Helvetica-Bold')
H2 = ParagraphStyle('H2', fontSize=11, textColor=NAVY,
    fontName='Helvetica-Bold', spaceAfter=4)
BODY = ParagraphStyle('BODY', fontSize=9,
    fontName='Helvetica', spaceAfter=3)
KPI_L = ParagraphStyle('KPI_L', fontSize=8,
    textColor=colors.grey, alignment=TA_CENTER)
KPI_V = ParagraphStyle('KPI_V', fontSize=13,
    textColor=NAVY, fontName='Helvetica-Bold',
    alignment=TA_CENTER)

def fmt(val, suffix=''):
    try:
        return str(round(float(val), 2)) + suffix
    except:
        return 'N/A'

def trend_arrow(curr, prev):
    try:
        c = float(curr)
        p = float(prev)
        pct = abs(c - p) / abs(p) * 100 if p != 0 else 0
        if pct <= 2:
            return 'flat'
        return 'up' if c > p else 'down'
    except:
        return 'flat'

def arrow_symbol(direction):
    if direction == 'up':
        return ' ↑'
    elif direction == 'down':
        return ' ↓'
    return ' →'

def load_data():
    conn = sqlite3.connect(DB_PATH)
    companies = pd.read_sql(
        'SELECT * FROM companies ORDER BY id', conn)
    fr = pd.read_sql(
        'SELECT * FROM financial_ratios', conn)
    sectors = pd.read_sql(
        'SELECT * FROM sectors', conn)
    conn.close()
    return companies, fr, sectors

def make_company_page(ticker, company_name, sector,
                       fr_latest, fr_prev):
    elements = []

    header_data = [[Paragraph(
        ticker + ' | ' + str(company_name)[:60] +
        ' | ' + str(sector), H1)]]
    ht = Table(header_data, colWidths=[UW])
    ht.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(ht)
    elements.append(Spacer(1, 0.3*cm))

    kpis = [
        ('ROE %',       'return_on_equity_pct',       '%'),
        ('ROCE %',      'return_on_capital_pct',      '%'),
        ('NPM %',       'net_profit_margin_pct',      '%'),
        ('D/E',         'debt_to_equity',             ''),
        ('Rev CAGR 5yr','revenue_cagr_5yr',           '%'),
        ('FCF (Cr)',    'free_cash_flow_cr',          ''),
    ]

    row = []
    for label, col, suffix in kpis:
        curr_val = fr_latest.get(col)
        prev_val = fr_prev.get(col) if fr_prev else None
        arrow = trend_arrow(curr_val, prev_val)
        sym = arrow_symbol(arrow)
        value_str = fmt(curr_val, suffix) + sym
        row.append([
            Paragraph(label, KPI_L),
            Paragraph(value_str, KPI_V),
        ])

    col_w = UW / 6
    kt = Table([row], colWidths=[col_w]*6)
    kt.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,-1), LGREY),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(kt)
    elements.append(Spacer(1, 0.3*cm))

    # Ratio trend mini table
    elements.append(Paragraph('Key Ratios', H2))
    ratio_data = [
        ['Metric', 'Value', 'Trend'],
        ['Return on Equity',
         fmt(fr_latest.get('return_on_equity_pct'), '%'),
         arrow_symbol(trend_arrow(fr_latest.get('return_on_equity_pct'),
                      fr_prev.get('return_on_equity_pct') if fr_prev else None))],
        ['Return on Capital',
         fmt(fr_latest.get('return_on_capital_pct'), '%'),
         arrow_symbol(trend_arrow(fr_latest.get('return_on_capital_pct'),
                      fr_prev.get('return_on_capital_pct') if fr_prev else None))],
        ['Net Profit Margin',
         fmt(fr_latest.get('net_profit_margin_pct'), '%'),
         arrow_symbol(trend_arrow(fr_latest.get('net_profit_margin_pct'),
                      fr_prev.get('net_profit_margin_pct') if fr_prev else None))],
        ['Debt to Equity',
         fmt(fr_latest.get('debt_to_equity')),
         arrow_symbol(trend_arrow(fr_latest.get('debt_to_equity'),
                      fr_prev.get('debt_to_equity') if fr_prev else None))],
        ['Free Cash Flow (Cr)',
         fmt(fr_latest.get('free_cash_flow_cr')),
         arrow_symbol(trend_arrow(fr_latest.get('free_cash_flow_cr'),
                      fr_prev.get('free_cash_flow_cr') if fr_prev else None))],
        ['Revenue CAGR 5yr',
         fmt(fr_latest.get('revenue_cagr_5yr'), '%'),
         arrow_symbol(trend_arrow(fr_latest.get('revenue_cagr_5yr'),
                      fr_prev.get('revenue_cagr_5yr') if fr_prev else None))],
        ['Capital Allocation',
         str(fr_latest.get('capital_allocation_pattern', 'N/A'))[:20],
         ''],
    ]
    col_widths = [UW*0.45, UW*0.35, UW*0.20]
    rt = Table(ratio_data, colWidths=col_widths)
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGREY]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 5),
        ('WORDWRAP', (0,0), (-1,-1), True),
    ]))
    elements.append(rt)
    return elements

def generate_portfolio_pdf():
    companies, fr, sectors = load_data()
    sector_map = dict(zip(sectors['company_id'],
                          sectors['broad_sector']))

    fr_march = fr[fr['year'].str.endswith('-03')]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    from datetime import datetime
    date_str = datetime.now().strftime('%Y%m%d')
    out_path = os.path.join(
        OUTPUT_DIR,
        'portfolio_summary_' + date_str + '.pdf'
    )

    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN
    )

    all_elements = []
    company_ids = sorted(companies['id'].tolist())
    print(f'Generating portfolio PDF for {len(company_ids)} companies...')

    for i, ticker in enumerate(company_ids):
        co_fr = fr_march[fr_march['company_id'] == ticker]
        if co_fr.empty:
            continue
        co_fr = co_fr.sort_values('year')
        fr_latest = co_fr.iloc[-1].to_dict()
        fr_prev = co_fr.iloc[-2].to_dict() if len(co_fr) >= 2 else None

        co_info = companies[companies['id'] == ticker]
        company_name = co_info.iloc[0].get('company_name', ticker) if not co_info.empty else ticker
        sector = sector_map.get(ticker, '')

        page_elements = make_company_page(
            ticker, company_name, sector,
            fr_latest, fr_prev
        )
        all_elements.extend(page_elements)
        if i < len(company_ids) - 1:
            all_elements.append(PageBreak())

    doc.build(all_elements)
    size_kb = os.path.getsize(out_path) // 1024
    print(f'Portfolio PDF saved: {out_path}')
    print(f'Size: {size_kb} KB')
    print(f'Pages: ~{len(company_ids)}')
    return out_path

if __name__ == '__main__':
    path = generate_portfolio_pdf()
    print('Done!')