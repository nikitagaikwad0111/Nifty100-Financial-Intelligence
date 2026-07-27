# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

DB_PATH = 'data/nifty100.db'
OUTPUT_DIR = 'reports/radar_charts'

RADAR_METRICS = [
    ('return_on_equity_pct',  'ROE %'),
    ('return_on_capital_pct', 'ROCE %'),
    ('net_profit_margin_pct', 'NPM %'),
    ('debt_to_equity',        'D/E'),
    ('free_cash_flow_cr',     'FCF'),
    ('pat_cagr_5yr',          'PAT CAGR'),
    ('revenue_cagr_5yr',      'Rev CAGR'),
    ('asset_turnover',        'Asset T/O'),
]

def load_peer_percentiles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM peer_percentiles', conn)
    conn.close()
    return df

def load_peer_groups():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT * FROM peer_groups', conn)
    conn.close()
    return df

def get_radar_data(company_id, group_name, percentiles):
    metric_keys = [m[0] for m in RADAR_METRICS]
    labels = [m[1] for m in RADAR_METRICS]
    group_data = percentiles[percentiles['peer_group_name'] == group_name]
    company_vals = []
    group_avg_vals = []
    for metric in metric_keys:
        metric_data = group_data[group_data['metric'] == metric]
        co_row = metric_data[metric_data['company_id'] == company_id]
        co_val = co_row['percentile_rank'].values[0] if not co_row.empty else 0.5
        company_vals.append(float(co_val) if co_val is not None else 0.5)
        avg_val = metric_data['percentile_rank'].mean()
        group_avg_vals.append(float(avg_val) if not np.isnan(avg_val) else 0.5)
    return company_vals, group_avg_vals, labels

def draw_radar(company_id, group_name, company_vals,
               group_avg_vals, labels, is_benchmark=False):
    N = len(labels)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    company_vals_plot = company_vals + [company_vals[0]]
    group_avg_plot = group_avg_vals + [group_avg_vals[0]]
    angles_plot = angles + [angles[0]]
    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    ax.plot(angles_plot, company_vals_plot, color='#1A237E', linewidth=2)
    ax.fill(angles_plot, company_vals_plot, color='#1A237E', alpha=0.25)
    ax.plot(angles_plot, group_avg_plot, color='#C62828', linewidth=1.5, linestyle='dashed')
    ax.fill(angles_plot, group_avg_plot, color='#C62828', alpha=0.08)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, size=9, fontweight='bold')
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25th', '50th', '75th', '100th'], size=7, color='grey')
    ax.grid(color='grey', linestyle='--', linewidth=0.5, alpha=0.5)
    bench_tag = ' (Benchmark)' if is_benchmark else ''
    title = company_id + bench_tag + chr(10) + group_name
    ax.set_title(title, size=12, fontweight='bold', pad=20, color='#1A237E')
    co_patch = mpatches.Patch(color='#1A237E', alpha=0.5, label=company_id)
    avg_patch = mpatches.Patch(color='#C62828', alpha=0.3, label='Peer Group Avg')
    ax.legend(handles=[co_patch, avg_patch], loc='upper right',
              bbox_to_anchor=(1.3, 1.1), fontsize=8)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = company_id + '_radar.png'
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    return filepath

def generate_all_radar_charts():
    percentiles = load_peer_percentiles()
    peer_groups = load_peer_groups()
    charts_generated = 0
    for group_name in peer_groups['peer_group_name'].unique():
        group_members = peer_groups[peer_groups['peer_group_name'] == group_name]
        print('Generating charts for: ' + group_name)
        for _, member in group_members.iterrows():
            company_id = member['company_id']
            is_benchmark = member['is_benchmark'] == 1
            company_vals, group_avg_vals, labels = get_radar_data(
                company_id, group_name, percentiles)
            filepath = draw_radar(company_id, group_name,
                company_vals, group_avg_vals, labels, is_benchmark)
            charts_generated += 1
            print('  ' + company_id + ' -> ' + filepath)
    print('Total charts: ' + str(charts_generated))
    return charts_generated

if __name__ == '__main__':
    print('Generating radar charts...')
    count = generate_all_radar_charts()
    print('Done! ' + str(count) + ' charts saved to ' + OUTPUT_DIR)