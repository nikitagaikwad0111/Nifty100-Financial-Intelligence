import sqlite3

conn = sqlite3.connect('data/nifty100.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(companies)")
cols = cur.fetchall()
print('companies columns:')
for c in cols:
    print(' -', c[1])
conn.close()