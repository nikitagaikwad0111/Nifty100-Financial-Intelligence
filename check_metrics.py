import sqlite3

conn = sqlite3.connect('data/nifty100.db')
cur = conn.cursor()
cur.execute("SELECT DISTINCT metric FROM peer_percentiles ORDER BY metric")
rows = cur.fetchall()
print(f'{len(rows)} distinct metrics in peer_percentiles:')
for r in rows:
    print(' -', r[0])
conn.close()