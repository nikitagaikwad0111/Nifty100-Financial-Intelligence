# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import get_latest_ratios
from src.screener.engine import compute_composite_score

st.set_page_config(page_title='Sector Analysis', layout='wide')
st.title('🏭 Sector Analysis')

df = get_latest_ratios()
if 'composite_quality_score' not in df.columns:
    df['composite_quality_score'] = compute_composite_score(df)

sectors = df['broad_sector'].dropna().unique().tolist()
selected_sector = st.selectbox('Select Sector', ['All Sectors'] + sectors)

if selected_sector != 'All Sectors':
    plot_df = df[df['broad_sector'] == selected_sector].copy()
else:
    plot_df = df.copy()

plot_df = plot_df.dropna(subset=['revenue_cagr_5yr',
    'return_on_equity_pct'])

st.subheader('Bubble Chart — Revenue vs ROE')
fig = px.scatter(
    plot_df,
    x='revenue_cagr_5yr',
    y='return_on_equity_pct',
    size='market_cap_crore',
    color='broad_sector',
    hover_name='company_id',
    hover_data=['company_name', 'net_profit_margin_pct'],
    labels={
        'revenue_cagr_5yr': 'Revenue CAGR 5yr %',
        'return_on_equity_pct': 'ROE %',
        'market_cap_crore': 'Market Cap (Cr)'
    },
    size_max=60,
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# Sector median KPI bar chart
st.subheader('Sector Median KPIs')
sector_medians = df.groupby('broad_sector').agg({
    'return_on_equity_pct': 'median',
    'net_profit_margin_pct': 'median',
    'debt_to_equity': 'median',
    'revenue_cagr_5yr': 'median',
}).reset_index()
sector_medians.columns = [
    'Sector', 'Median ROE%', 'Median NPM%',
    'Median D/E', 'Median Rev CAGR'
]

metric_choice = st.selectbox(
    'Select Metric',
    ['Median ROE%', 'Median NPM%',
     'Median D/E', 'Median Rev CAGR']
)
fig2 = px.bar(
    sector_medians.sort_values(metric_choice, ascending=False),
    x='Sector', y=metric_choice,
    color='Sector',
    color_discrete_sequence=px.colors.qualitative.Set3
)
fig2.update_layout(height=400, showlegend=False)
st.plotly_chart(fig2, use_container_width=True)