import sqlite3

conn = sqlite3.connect('data/nifty100.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(peer_percentiles)")
cols = cur.fetchall()
print('peer_percentiles columns:')
for c in cols:
    print(' -', c[1])
conn.close()