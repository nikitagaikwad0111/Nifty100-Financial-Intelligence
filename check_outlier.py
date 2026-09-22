import sqlite3

conn = sqlite3.connect('data/nifty100.db')
cur = conn.cursor()
cur.execute("SELECT company_id, year, return_on_equity_pct, book_value_per_share FROM financial_ratios WHERE company_id IN ('BEL', 'HAL') ORDER BY company_id, year DESC LIMIT 6")
for r in cur.fetchall():
    print(r)
conn.close()