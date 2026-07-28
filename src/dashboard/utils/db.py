# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import os
import streamlit as st

DB_PATH = os.getenv('DB_PATH', 'data/nifty100.db')

@st.cache_data(ttl=600)
def get_companies():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM companies', conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_all_ratios():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('''
        SELECT fr.*, s.broad_sector, s.sub_sector,
               c.company_name, mc.pe_ratio, mc.pb_ratio,
               mc.dividend_yield_pct, mc.market_cap_crore,
               mc.ev_ebitda, mc.enterprise_value_crore
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id
            AND mc.year = fr.year
    ''', conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    conn = sqlite3.connect(DB_PATH)
    if year:
        df = pd.read_sql(
            'SELECT * FROM financial_ratios WHERE company_id=? AND year=?',
            conn, params=[ticker, year])
    else:
        df = pd.read_sql(
            'SELECT * FROM financial_ratios WHERE company_id=? ORDER BY year',
            conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_pl(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        'SELECT * FROM profitandloss WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_bs(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        'SELECT * FROM balancesheet WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_cf(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        'SELECT * FROM cashflow WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_sectors():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        'SELECT * FROM sectors', conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        'SELECT * FROM peer_percentiles WHERE peer_group_name=?',
        conn, params=[group_name])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peer_groups():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM peer_groups', conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_valuation(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        'SELECT * FROM market_cap WHERE company_id=? ORDER BY year',
        conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_documents(ticker):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        'SELECT * FROM documents WHERE company_id=? ORDER BY Year DESC',
        conn, params=[ticker])
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_latest_ratios():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('''
        SELECT fr.*, s.broad_sector, s.sub_sector,
               c.company_name, mc.pe_ratio, mc.pb_ratio,
               mc.dividend_yield_pct, mc.market_cap_crore
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN market_cap mc ON fr.company_id = mc.company_id
            AND mc.year = fr.year
        WHERE fr.year = (
            SELECT MAX(year) FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id
            AND fr2.year LIKE
            "'%-03'"
        )
    ''', conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_capital_allocation():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('''
        SELECT fr.company_id, c.company_name,
               fr.capital_allocation_pattern,
               fr.free_cash_flow_cr, fr.year,
               s.broad_sector
        FROM financial_ratios fr
        JOIN companies c ON fr.company_id = c.id
        JOIN sectors s ON fr.company_id = s.company_id
        WHERE fr.year = (
            SELECT MAX(year) FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id
            AND fr2.year LIKE
            "'%-03'"
        )
    ''', conn)
    conn.close()
    return df