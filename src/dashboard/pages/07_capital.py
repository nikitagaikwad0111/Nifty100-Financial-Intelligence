# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import get_capital_allocation

st.set_page_config(page_title='Capital Allocation', layout='wide')
st.title('💰 Capital Allocation Map')
st.markdown('How do Nifty 100 companies deploy their cash?')

df = get_capital_allocation()

if df.empty:
    st.warning('No capital allocation data found')
    st.stop()

# Use count instead of FCF for treemap size
df['count'] = 1

# Treemap
st.subheader('Capital Allocation Treemap')
fig = px.treemap(
    df,
    path=['capital_allocation_pattern', 'company_id'],
    values='count',
    color='capital_allocation_pattern',
    hover_data=['company_name', 'broad_sector',
                'free_cash_flow_cr'],
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig.update_layout(height=500)
fig.update_traces(textinfo='label')
st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

# Pattern selector
patterns = df['capital_allocation_pattern'].unique().tolist()
selected_pattern = st.selectbox(
    'Select Pattern to see companies',
    patterns
)

filtered = df[
    df['capital_allocation_pattern'] == selected_pattern
][['company_id', 'company_name', 'broad_sector',
   'free_cash_flow_cr']].reset_index(drop=True)
filtered.columns = ['Ticker', 'Company', 'Sector', 'FCF (Cr)']

st.subheader(selected_pattern + ' — ' + str(len(filtered)) + ' companies')
st.dataframe(filtered, use_container_width=True)

explanations = {
    'Reinvestor': 'CFO>0, CFI<0, CFF<0 — Profitable, investing in growth, paying down debt',
    'Cash Accumulator': 'CFO>0, CFI<0, CFF>0 — Profitable but also raising more funds',
    'Liquidating Assets': 'CFO>0, CFI>0, CFF<0 — Selling assets to pay down debt',
    'Distress Signal': 'CFO<0, CFI>0, CFF>0 — Selling assets AND raising funds to survive',
    'Growth Funded by Debt': 'CFO<0, CFI<0, CFF>0 — Borrowing to invest while losing money',
    'Pre-Revenue': 'CFO<0, CFI<0, CFF<0 — Burning cash everywhere',
    'Mixed': 'Unusual combination — needs analyst review',
    'Unclassified': 'Missing or incomplete cash flow data',
}
if selected_pattern in explanations:
    st.info(explanations[selected_pattern])