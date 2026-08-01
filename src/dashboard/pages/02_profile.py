# -*- coding: utf-8 -*-
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import (
    get_companies, get_pl, get_bs, get_cf,
    get_ratios, get_valuation
)

st.set_page_config(page_title='Company Profile', layout='wide')
st.title('🏢 Company Profile')

companies = get_companies()
company_list = companies['id'].tolist()

# Search box
ticker = st.selectbox(
    'Search by Ticker or Company Name',
    options=company_list,
    index=company_list.index('TCS') if 'TCS' in company_list else 0
)

if not ticker:
    st.warning('Please select a company')
    st.stop()

co_info = companies[companies['id'] == ticker]
if co_info.empty:
    st.error('Ticker not found - please try another')
    st.stop()

co = co_info.iloc[0]

# Company Card
st.markdown('---')
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader(str(co.get('company_name', ticker)))
    st.caption('NSE Ticker: ' + str(ticker))
    about = co.get('about_company', '')
    if about and str(about) != 'nan':
        st.write(str(about)[:500])

with col2:
    st.metric('Book Value', str(co.get('book_value', 'N/A')))
    st.metric('Face Value', str(co.get('face_value', 'N/A')))

st.markdown('---')

# KPI Tiles from financial_ratios
ratios = get_ratios(ticker)
if ratios.empty:
    st.warning('No financial ratio data found for ' + ticker)
else:
    latest = ratios.sort_values('year').iloc[-1]
    st.subheader('Latest KPIs (' + str(latest['year']) + ')')
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    def fmt(val, suffix=''):
        try:
            return str(round(float(val), 2)) + suffix
        except:
            return 'N/A'
    k1.metric('ROE %',         fmt(latest.get('return_on_equity_pct'), '%'))
    k2.metric('ROCE %',        fmt(latest.get('return_on_capital_pct'), '%'))
    k3.metric('NPM %',         fmt(latest.get('net_profit_margin_pct'), '%'))
    k4.metric('D/E',           fmt(latest.get('debt_to_equity')))
    k5.metric('Rev CAGR 5yr', fmt(latest.get('revenue_cagr_5yr'), '%'))
    k6.metric('FCF (Cr)',      fmt(latest.get('free_cash_flow_cr')))

st.markdown('---')

# P&L Charts
pl = get_pl(ticker)
if not pl.empty:
    st.subheader('Revenue & Net Profit (10 Year)')
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pl['year'], y=pl['sales'],
        name='Revenue', marker_color='#1A237E'
    ))
    fig.add_trace(go.Bar(
        x=pl['year'], y=pl['net_profit'],
        name='Net Profit', marker_color='#4CAF50'
    ))
    fig.update_layout(
        barmode='group', height=400,
        xaxis_title='Year', yaxis_title='Rs. Crore'
    )
    st.plotly_chart(fig, use_container_width=True)

# ROE & ROCE Line Chart
if not ratios.empty:
    st.subheader('ROE & ROCE Trend')
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=ratios['year'],
        y=ratios['return_on_equity_pct'],
        name='ROE %', line=dict(color='#1A237E', width=2)
    ))
    fig2.add_trace(go.Scatter(
        x=ratios['year'],
        y=ratios['return_on_capital_pct'],
        name='ROCE %', line=dict(color='#C62828', width=2)
    ))
    fig2.update_layout(height=350, xaxis_title='Year', yaxis_title='%')
    st.plotly_chart(fig2, use_container_width=True)