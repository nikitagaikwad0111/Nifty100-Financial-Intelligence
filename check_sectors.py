import sqlite3

conn = sqlite3.connect('data/nifty100.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info(sectors)")
print('sectors columns:')
for c in cur.fetchall():
    print(' -', c[1])
print()
cur.execute("SELECT * FROM sectors LIMIT 5")
print('sample rows:')
for r in cur.fetchall():
    print(' ', r)
conn.close()