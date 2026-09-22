import sqlite3

conn = sqlite3.connect('data/nifty100.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('All tables:')
for t in tables:
    print(' -', t)
print()
print('financial_ratios columns:')
cur.execute("PRAGMA table_info(financial_ratios)")
for c in cur.fetchall():
    print(' -', c[1])
conn.close()