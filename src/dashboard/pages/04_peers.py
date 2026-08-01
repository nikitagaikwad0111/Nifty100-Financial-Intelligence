# -*- coding: utf-8 -*-
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import (
    get_peer_groups, get_peers, get_latest_ratios
)

st.set_page_config(page_title='Peer Comparison', layout='wide')
st.title('👥 Peer Comparison')

peer_groups = get_peer_groups()
group_names = peer_groups['peer_group_name'].unique().tolist()

# Group selector
selected_group = st.selectbox('Select Peer Group', group_names)

# Get members
members = peer_groups[peer_groups['peer_group_name'] == selected_group]
member_ids = members['company_id'].tolist()
benchmark = members[members['is_benchmark'] == 1]['company_id'].values
benchmark_id = benchmark[0] if len(benchmark) > 0 else member_ids[0]

# Company selector
selected_co = st.selectbox('Select Company', member_ids,
    index=member_ids.index(benchmark_id) if benchmark_id in member_ids else 0)

st.markdown('---')

# Radar Chart
percentiles = get_peers(selected_group)
RADAR_METRICS = [
    ('return_on_equity_pct',  'ROE'),
    ('return_on_capital_pct', 'ROCE'),
    ('net_profit_margin_pct', 'NPM'),
    ('debt_to_equity',        'D/E'),
    ('free_cash_flow_cr',     'FCF'),
    ('pat_cagr_5yr',          'PAT CAGR'),
    ('revenue_cagr_5yr',      'Rev CAGR'),
    ('asset_turnover',        'Asset T/O'),
]

labels = [m[1] for m in RADAR_METRICS]
metric_keys = [m[0] for m in RADAR_METRICS]

def get_vals(company_id):
    vals = []
    for mk in metric_keys:
        row = percentiles[
            (percentiles['company_id'] == company_id) &
            (percentiles['metric'] == mk)
        ]
        vals.append(float(row['percentile_rank'].values[0])
                    if not row.empty else 0.5)
    return vals

co_vals  = get_vals(selected_co)
avg_vals = []
for mk in metric_keys:
    rows = percentiles[percentiles['metric'] == mk]
    avg_vals.append(float(rows['percentile_rank'].mean())
                    if not rows.empty else 0.5)

col1, col2 = st.columns([1, 1])
with col1:
    st.subheader('Radar Chart — ' + selected_co + ' vs Peer Avg')
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=co_vals + [co_vals[0]],
        theta=labels + [labels[0]],
        fill='toself',
        name=selected_co,
        line_color='#1A237E'
    ))
    fig.add_trace(go.Scatterpolar(
        r=avg_vals + [avg_vals[0]],
        theta=labels + [labels[0]],
        fill='toself',
        name='Peer Average',
        line_color='#C62828',
        opacity=0.4
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader('Peer Group KPI Table')
    ratios = get_latest_ratios()
    peer_ratios = ratios[ratios['company_id'].isin(member_ids)][
        ['company_id', 'company_name',
         'return_on_equity_pct', 'return_on_capital_pct',
         'net_profit_margin_pct', 'debt_to_equity',
         'free_cash_flow_cr', 'revenue_cagr_5yr']
    ].reset_index(drop=True)
    peer_ratios.columns = [
        'Ticker', 'Company', 'ROE%', 'ROCE%',
        'NPM%', 'D/E', 'FCF', 'Rev CAGR'
    ]
    st.dataframe(
        peer_ratios.style.highlight_max(
            subset=['ROE%', 'ROCE%', 'NPM%', 'Rev CAGR'],
            color='#1A237E'
        ),
        use_container_width=True,
        height=400
    )