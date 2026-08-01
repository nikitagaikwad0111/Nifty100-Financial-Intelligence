# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import get_latest_ratios
from src.screener.engine import (
    run_screener, compute_composite_score
)

st.set_page_config(page_title='Screener', layout='wide')
st.title('🔍 Financial Screener')

# Preset buttons
st.subheader('Quick Presets')
p1,p2,p3,p4,p5,p6 = st.columns(6)
preset = None
if p1.button('⭐ Quality'):   preset = 'quality_compounder'
if p2.button('💰 Value'):     preset = 'value_pick'
if p3.button('🚀 Growth'):    preset = 'growth_accelerator'
if p4.button('💸 Dividend'):  preset = 'dividend_champion'
if p5.button('🏦 Debt-Free'): preset = 'debt_free_blue_chip'
if p6.button('🔄 Turnaround'):preset = 'turnaround_watch'

st.markdown('---')

# Sidebar sliders
st.sidebar.header('Custom Filters')
min_roe   = st.sidebar.slider('Min ROE %',        0.0, 50.0, 0.0)
max_de    = st.sidebar.slider('Max D/E',          0.0, 10.0, 10.0)
min_fcf   = st.sidebar.slider('Min FCF (Cr)',     -50000.0, 50000.0, -50000.0)
min_rev   = st.sidebar.slider('Min Rev CAGR 5yr', -20.0, 40.0, -20.0)
min_pat   = st.sidebar.slider('Min PAT CAGR 5yr', -20.0, 40.0, -20.0)
min_opm   = st.sidebar.slider('Min OPM %',        0.0, 40.0, 0.0)
max_pe    = st.sidebar.slider('Max P/E',          0.0, 100.0, 100.0)
max_pb    = st.sidebar.slider('Max P/B',          0.0, 20.0, 20.0)
min_div   = st.sidebar.slider('Min Div Yield %',  0.0, 5.0, 0.0)
min_icr   = st.sidebar.slider('Min ICR',          0.0, 10.0, 0.0)

# Build filters
if preset:
    results = run_screener(preset_name=preset)
else:
    filters = {}
    if min_roe  > 0:    filters['min_roe']            = min_roe
    if max_de   < 10:   filters['max_de']             = max_de
    if min_fcf  > -50000: filters['min_fcf']          = min_fcf
    if min_rev  > -20:  filters['min_revenue_cagr_5yr'] = min_rev
    if min_pat  > -20:  filters['min_pat_cagr_5yr']   = min_pat
    if min_opm  > 0:    filters['min_opm']            = min_opm
    if max_pe   < 100:  filters['max_pe']             = max_pe
    if max_pb   < 20:   filters['max_pb']             = max_pb
    if min_div  > 0:    filters['min_dividend_yield'] = min_div
    if min_icr  > 0:    filters['min_icr']            = min_icr
    results = run_screener(filters=filters)

if 'composite_quality_score' not in results.columns:
    results['composite_quality_score'] = compute_composite_score(results)

# Results
st.subheader(str(len(results)) + ' companies match your filters')

display_cols = [
    'company_id', 'company_name', 'broad_sector',
    'composite_quality_score',
    'return_on_equity_pct', 'debt_to_equity',
    'free_cash_flow_cr', 'revenue_cagr_5yr',
    'net_profit_margin_pct', 'pe_ratio',
    'dividend_yield_pct'
]
available = [c for c in display_cols if c in results.columns]
display_df = results[available].reset_index(drop=True)
display_df.columns = [
    c.replace('_', ' ').title() for c in display_df.columns
]

st.dataframe(display_df, use_container_width=True, height=400)

# CSV Download
csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label='📥 Download CSV',
    data=csv,
    file_name='screener_results.csv',
    mime='text/csv'
)