# -*- coding: utf-8 -*-
import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import get_companies, get_ratios

st.set_page_config(page_title='Trend Analysis', layout='wide')
st.title('📈 Trend Analysis')

companies = get_companies()
ticker = st.selectbox('Select Company',
    companies['id'].tolist(),
    index=companies['id'].tolist().index('TCS')
    if 'TCS' in companies['id'].tolist() else 0)

METRICS = {
    'ROE %':           'return_on_equity_pct',
    'ROCE %':          'return_on_capital_pct',
    'Net Profit Margin': 'net_profit_margin_pct',
    'D/E Ratio':       'debt_to_equity',
    'Revenue CAGR 5yr': 'revenue_cagr_5yr',
    'PAT CAGR 5yr':    'pat_cagr_5yr',
    'FCF (Cr)':        'free_cash_flow_cr',
    'Asset Turnover':  'asset_turnover',
}

selected_metrics = st.multiselect(
    'Select Metrics (up to 3)',
    list(METRICS.keys()),
    default=['ROE %', 'ROCE %']
)

if len(selected_metrics) > 3:
    st.warning('Please select maximum 3 metrics')
    selected_metrics = selected_metrics[:3]

ratios = get_ratios(ticker)

if ratios.empty:
    st.warning('No data found for ' + ticker)
    st.stop()

ratios = ratios.sort_values('year')

if selected_metrics:
    st.subheader('10-Year Trend — ' + ticker)
    fig = go.Figure()
    colors = ['#1A237E', '#C62828', '#2E7D32']
    for i, metric_label in enumerate(selected_metrics):
        col = METRICS[metric_label]
        if col not in ratios.columns:
            continue
        y_vals = ratios[col].tolist()
        x_vals = ratios['year'].tolist()
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            name=metric_label,
            line=dict(color=colors[i], width=2),
            mode='lines+markers+text',
        ))
    fig.update_layout(
        height=450,
        xaxis_title='Year',
        yaxis_title='Value',
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

# YoY change table
st.subheader('Year-on-Year Changes')
if selected_metrics:
    yoy_data = ratios[['year']].copy()
    for metric_label in selected_metrics:
        col = METRICS[metric_label]
        if col in ratios.columns:
            yoy_data[metric_label] = ratios[col].values
            yoy_data[metric_label + ' YoY%'] = ratios[col].pct_change() * 100
    st.dataframe(yoy_data.tail(10).reset_index(drop=True),
                 use_container_width=True)