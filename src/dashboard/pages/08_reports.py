# -*- coding: utf-8 -*-
import streamlit as st
import sys, os
sys.path.insert(0, os.path.abspath('.'))
from src.dashboard.utils.db import get_companies, get_documents

st.set_page_config(page_title='Annual Reports', layout='wide')
st.title('📄 Annual Reports Repository')
st.markdown('Access BSE annual report PDFs for all companies')

companies = get_companies()
ticker = st.selectbox(
    'Select Company',
    companies['id'].tolist(),
    index=companies['id'].tolist().index('TCS')
    if 'TCS' in companies['id'].tolist() else 0
)

co_info = companies[companies['id'] == ticker]
if not co_info.empty:
    co = co_info.iloc[0]
    st.subheader(str(co.get('company_name', ticker)))
    if co.get('website') and str(co.get('website')) != 'nan':
        st.markdown('🌐 [Company Website](' + str(co['website']) + ')')

st.markdown('---')

docs = get_documents(ticker)

if docs.empty:
    st.warning('No annual reports found for ' + ticker)
    st.stop()

st.subheader('Available Annual Reports — ' + str(len(docs)) + ' reports')

for _, row in docs.iterrows():
    year = str(row.get('Year', 'N/A'))
    url  = row.get('Annual_Report', '')
    col1, col2, col3 = st.columns([1, 4, 2])
    with col1:
        st.write('📅 ' + year)
    with col2:
        if url and str(url) != 'nan':
            st.markdown('[📥 Download Annual Report](' + str(url) + ')')
        else:
            st.markdown(':red[Report unavailable]')
    with col3:
        if url and str(url) != 'nan':
            st.success('Available')
        else:
            st.error('Unavailable')