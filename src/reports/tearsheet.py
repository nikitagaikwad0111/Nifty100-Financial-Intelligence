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
    Spacer, Table, TableStyle, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

DB_PATH = 'data/nifty100.db'
OUTPUT_DIR = 'reports/tearsheets'
PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm
UW = PAGE_W - 2 * MARGIN

NAVY  = colors.HexColor('#1A237E')
GREEN = colors.HexColor('#2E7D32')
RED   = colors.HexColor('#C62828')
LGREY = colors.HexColor('#F5F5F5')
WHITE = colors.white

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', fontSize=14, leading=16, textColor=WHITE,
    fontName='Helvetica-Bold', alignment=TA_LEFT)
H2 = ParagraphStyle('H2', fontSize=12, textColor=NAVY,
    fontName='Helvetica-Bold', spaceAfter=6)
BODY = ParagraphStyle('BODY', fontSize=9, textColor=colors.black,
    fontName='Helvetica', spaceAfter=4)
SMALL = ParagraphStyle('SMALL', fontSize=8, textColor=colors.grey)
KPI_LABEL = ParagraphStyle('KPI_LABEL', fontSize=8,
    textColor=colors.grey, fontName='Helvetica', alignment=TA_CENTER)
KPI_VALUE = ParagraphStyle('KPI_VALUE', fontSize=14,
    textColor=NAVY, fontName='Helvetica-Bold', alignment=TA_CENTER)

def load_company_data(ticker):
    conn = sqlite3.connect(DB_PATH)
    co = pd.read_sql(
        'SELECT * FROM companies WHERE id=?',
        conn, params=[ticker])
    pl = pd.read_sql(
        'SELECT * FROM profitandloss WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    bs = pd.read_sql(
        'SELECT * FROM balancesheet WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    cf = pd.read_sql(
        'SELECT * FROM cashflow WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    fr = pd.read_sql(
        'SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    sec = pd.read_sql(
        'SELECT * FROM sectors WHERE company_id=?',
        conn, params=[ticker])
    conn.close()
    return co, pl, bs, cf, fr, sec

def fmt(val, suffix='', decimals=2):
    try:
        return str(round(float(val), decimals)) + suffix
    except:
        return 'N/A'

def make_header(ticker, company_name, sector):
    header_data = [[
        Paragraph(company_name + ' | ' + ticker + ' | ' + sector, H1),
    ]]
    t = Table(header_data, colWidths=[UW])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [NAVY]),
    ]))
    return t

def make_kpi_tiles(fr_latest):
    kpis = [
        ('ROE %',      fmt(fr_latest.get('return_on_equity_pct'), '%')),
        ('ROCE %',     fmt(fr_latest.get('return_on_capital_pct'), '%')),
        ('NPM %',      fmt(fr_latest.get('net_profit_margin_pct'), '%')),
        ('D/E',        fmt(fr_latest.get('debt_to_equity'))),
        ('Rev CAGR 5yr', fmt(fr_latest.get('revenue_cagr_5yr'), '%')),
        ('FCF (Cr)',   fmt(fr_latest.get('free_cash_flow_cr'))),
    ]
    row1 = []
    for label, value in kpis:
        cell = [
            Paragraph(label, KPI_LABEL),
            Paragraph(value, KPI_VALUE),
        ]
        row1.append(cell)
    col_w = UW / 6
    t = Table([row1], colWidths=[col_w]*6)
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,-1), LGREY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    return t

def make_pl_table(pl):
    pl_march = pl[pl['year'].str.endswith('-03')].tail(8)
    if pl_march.empty:
        pl_march = pl.tail(8)
    headers = ['Year', 'Sales', 'Op Profit', 'Net Profit', 'OPM%', 'EPS']
    rows = [headers]
    for _, row in pl_march.iterrows():
        rows.append([
            str(row.get('year', ''))[:7],
            fmt(row.get('sales')),
            fmt(row.get('operating_profit')),
            fmt(row.get('net_profit')),
            fmt(row.get('opm_percentage'), '%'),
            fmt(row.get('eps')),
        ])
    col_w = UW / len(headers)
    t = Table(rows, colWidths=[col_w]*len(headers))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGREY]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('WORDWRAP', (0,0), (-1,-1), True),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def make_bs_table(bs):
    bs_march = bs[bs['year'].str.endswith('-03')].tail(6)
    if bs_march.empty:
        bs_march = bs.tail(6)
    headers = ['Year', 'Equity', 'Reserves', 'Borrowings', 'Total Assets']
    rows = [headers]
    for _, row in bs_march.iterrows():
        rows.append([
            str(row.get('year', ''))[:7],
            fmt(row.get('equity_capital')),
            fmt(row.get('reserves')),
            fmt(row.get('borrowings')),
            fmt(row.get('total_assets')),
        ])
    col_w = UW / len(headers)
    t = Table(rows, colWidths=[col_w]*len(headers))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGREY]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('WORDWRAP', (0,0), (-1,-1), True),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def make_cf_table(cf):
    cf_latest = cf.sort_values('year').tail(3)
    headers = ['Year', 'CFO', 'CFI', 'CFF', 'Net Cash']
    rows = [headers]
    for _, row in cf_latest.iterrows():
        rows.append([
            str(row.get('year', ''))[:7],
            fmt(row.get('operating_activity')),
            fmt(row.get('investing_activity')),
            fmt(row.get('financing_activity')),
            fmt(row.get('net_cash_flow')),
        ])
    col_w = UW / len(headers)
    t = Table(rows, colWidths=[col_w]*len(headers))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGREY]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('WORDWRAP', (0,0), (-1,-1), True),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def make_pros_cons(ticker):
    try:
        df = pd.read_csv('output/pros_cons_generated.csv')
        co_df = df[df['company_id'] == ticker]
        pros = co_df[co_df['type'] == 'pro']['text'].tolist()
        cons = co_df[co_df['type'] == 'con']['text'].tolist()
    except:
        pros = []
        cons = []
    elements = []
    elements.append(Paragraph('Strengths', H2))
    for p in pros[:4]:
        txt = str(p)[:200]
        elements.append(Paragraph('+ ' + txt, ParagraphStyle(
            'pro', fontSize=8, textColor=GREEN,
            fontName='Helvetica', spaceAfter=3)))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph('Concerns', H2))
    for c in cons[:4]:
        txt = str(c)[:200]
        elements.append(Paragraph('- ' + txt, ParagraphStyle(
            'con', fontSize=8, textColor=RED,
            fontName='Helvetica', spaceAfter=3)))
    return elements

def generate_tearsheet(ticker):
    co, pl, bs, cf, fr, sec = load_company_data(ticker)
    if co.empty:
        print(f'No data for {ticker}')
        return False

    co_info = co.iloc[0]
    company_name = str(co_info.get('company_name', ticker))[:80]
    sector = sec.iloc[0].get('broad_sector', '') if not sec.empty else ''

    fr_march = fr[fr['year'].str.endswith('-03')]
    fr_latest = fr_march.sort_values('year').iloc[-1].to_dict() if not fr_march.empty else {}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, ticker + '_tearsheet.pdf')

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    elements = []

    # PAGE 1
    elements.append(make_header(ticker, company_name, sector))
    elements.append(Spacer(1, 0.3*cm))

    about = str(co_info.get('about_company', ''))[:400]
    if about and about != 'nan':
        elements.append(Paragraph(about, BODY))
    elements.append(Spacer(1, 0.3*cm))

    elements.append(Paragraph('Key Performance Indicators', H2))
    elements.append(make_kpi_tiles(fr_latest))
    elements.append(Spacer(1, 0.4*cm))

    elements.append(Paragraph('Profit & Loss Summary (Rs. Crore)', H2))
    if not pl.empty:
        elements.append(make_pl_table(pl))
    elements.append(Spacer(1, 0.4*cm))

    # Ratio trend table
    elements.append(Paragraph('Key Ratios Trend', H2))
    if not fr_march.empty:
        fr_tail = fr_march.tail(6)
        ratio_headers = ['Year', 'ROE%', 'ROCE%', 'D/E', 'FCF(Cr)', 'Rev CAGR']
        ratio_rows = [ratio_headers]
        for _, row in fr_tail.iterrows():
            ratio_rows.append([
                str(row.get('year', ''))[:7],
                fmt(row.get('return_on_equity_pct'), '%'),
                fmt(row.get('return_on_capital_pct'), '%'),
                fmt(row.get('debt_to_equity')),
                fmt(row.get('free_cash_flow_cr')),
                fmt(row.get('revenue_cagr_5yr'), '%'),
            ])
        col_w = UW / len(ratio_headers)
        rt = Table(ratio_rows, colWidths=[col_w]*len(ratio_headers))
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGREY]),
            ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(rt)

    # PAGE 2
    from reportlab.platypus import PageBreak
    elements.append(PageBreak())
    elements.append(make_header(ticker, company_name, sector))
    elements.append(Spacer(1, 0.3*cm))

    elements.append(Paragraph('Balance Sheet Summary (Rs. Crore)', H2))
    if not bs.empty:
        elements.append(make_bs_table(bs))
    elements.append(Spacer(1, 0.4*cm))

    elements.append(Paragraph('Cash Flow Statement (Rs. Crore)', H2))
    if not cf.empty:
        elements.append(make_cf_table(cf))
    elements.append(Spacer(1, 0.4*cm))

    # Capital Allocation Badge
    cap_alloc = fr_latest.get('capital_allocation_pattern', 'N/A')
    elements.append(Paragraph('Capital Allocation Pattern', H2))
    elements.append(Paragraph(str(cap_alloc), ParagraphStyle(
        'badge', fontSize=11, textColor=NAVY,
        fontName='Helvetica-Bold')))
    elements.append(Spacer(1, 0.4*cm))

    # Pros and Cons
    for el in make_pros_cons(ticker):
        elements.append(el)

    doc.build(elements)
    size_kb = os.path.getsize(out_path) // 1024
    return size_kb

if __name__ == '__main__':
    test_tickers = ['TCS', 'HDFCBANK', 'RELIANCE', 'SUNPHARMA', 'TATASTEEL']
    print('Testing tearsheet generation...')
    for ticker in test_tickers:
        size = generate_tearsheet(ticker)
        print(f'{ticker}: {size} KB')
    print('Done! Check reports/tearsheets/')