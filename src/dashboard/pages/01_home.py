# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import (
    get_latest_ratios, get_sectors, get_companies
)

st.set_page_config(page_title='Home', layout='wide')
st.title('📊 Nifty 100 — Market Overview')
st.markdown('---')

df = get_latest_ratios()
import sys
sys.path.insert(0, '.')
from src.screener.engine import compute_composite_score
if 'composite_quality_score' not in df.columns:
    df['composite_quality_score'] = compute_composite_score(df)
companies = get_companies()
sectors = get_sectors()

# Sidebar year selector
st.sidebar.header('Filters')
year = st.sidebar.selectbox(
    'Select Year',
    ['2024-03', '2023-03', '2022-03', '2021-03', '2020-03', '2019-03'],
    index=0
)

# KPI Tiles
st.subheader('Market Summary')
c1, c2, c3, c4, c5, c6 = st.columns(6)
avg_roe = df['return_on_equity_pct'].mean()
med_pe  = df['pe_ratio'].median()
med_de  = df['debt_to_equity'].median()
total   = len(df)
med_rev = df['revenue_cagr_5yr'].median()
debt_free = (df['debt_to_equity'] == 0).sum()

c1.metric('Avg ROE %',       f'{avg_roe:.1f}%')
c2.metric('Median P/E',      f'{med_pe:.1f}x'  if med_pe  == med_pe else 'N/A')
c3.metric('Median D/E',      f'{med_de:.2f}')
c4.metric('Companies',       str(total))
c5.metric('Median Rev CAGR', f'{med_rev:.1f}%' if med_rev == med_rev else 'N/A')
c6.metric('Debt-Free Cos',   str(int(debt_free)))

st.markdown('---')

# Sector Donut Chart
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader('Sector Distribution')
    sector_counts = df.groupby('broad_sector').size().reset_index(name='count')
    fig_donut = px.pie(
        sector_counts,
        names='broad_sector',
        values='count',
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_donut.update_layout(height=400, showlegend=True)
    st.plotly_chart(fig_donut, use_container_width=True)

with col2:
    st.subheader('Top 10 Companies by Quality Score')
    top10 = df.nlargest(10, 'composite_quality_score')[
        ['company_id', 'company_name', 'broad_sector',
         'composite_quality_score', 'return_on_equity_pct',
         'revenue_cagr_5yr']
    ].reset_index(drop=True)
    top10.columns = ['Ticker', 'Company', 'Sector',
                     'Score', 'ROE %', 'Rev CAGR 5yr']
    st.dataframe(top10, use_container_width=True, height=400)

st.markdown('---')

# Capital Allocation Summary
st.subheader('Capital Allocation Patterns')
if 'capital_allocation_pattern' in df.columns:
    cap_counts = df['capital_allocation_pattern'].value_counts().reset_index()
    cap_counts.columns = ['Pattern', 'Count']
    fig_bar = px.bar(
        cap_counts, x='Pattern', y='Count',
        color='Pattern',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_bar.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)