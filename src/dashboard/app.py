# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(
    page_title='Nifty 100 Analytics',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.title('📊 Nifty 100 Financial Intelligence Platform')
st.markdown('---')

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric('Companies', '91')
with col2:
    st.metric('KPIs Computed', '50+')
with col3:
    st.metric('Years of Data', '10-13')
with col4:
    st.metric('Peer Groups', '11')

st.markdown('---')
st.markdown('''
### Navigate using the sidebar
- **Home** - Market overview and top companies
- **Company Profile** - Deep dive into any company
- **Screener** - Filter companies by financial metrics
- **Peer Comparison** - Compare within peer groups
- **Trend Analysis** - 10-year trend charts
- **Sector Analysis** - Sector-level insights
- **Capital Allocation** - How companies deploy cash
- **Annual Reports** - Access BSE annual report links
''')