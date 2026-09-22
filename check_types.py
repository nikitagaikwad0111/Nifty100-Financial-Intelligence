import sqlite3

conn = sqlite3.connect('data/nifty100.db')
cur = conn.cursor()

print('Sample financial_ratios rows (company_id, year):')
cur.execute("SELECT company_id, year FROM financial_ratios LIMIT 5")
for r in cur.fetchall():
    print(' ', r)

print()
print('Sample companies rows (id, company_name):')
cur.execute("SELECT id, company_name FROM companies LIMIT 5")
for r in cur.fetchall():
    print(' ', r)

print()
print('companies table full column list again, check for ticker-like column:')
cur.execute("PRAGMA table_info(companies)")
for c in cur.fetchall():
    print(' -', c[1], '|', c[2])

conn.close()