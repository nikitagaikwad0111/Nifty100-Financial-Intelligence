import sqlite3

conn = sqlite3.connect('data/nifty100.db')

# 5 random companies to spot check
companies = ['TCS', 'HDFCBANK', 'RELIANCE', 'SUNPHARMA', 'MARUTI']

for company in companies:
    print(f"\n{'='*60}")
    print(f"COMPANY: {company}")
    print('='*60)

    # P&L latest year
    pl = conn.execute("""
        SELECT year, sales, net_profit, eps, opm_percentage
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year DESC LIMIT 3
    """, (company,)).fetchall()
    print(f"\nP&L (latest 3 years):")
    print(f"{'Year':<12} {'Sales':>12} {'Net Profit':>12} {'EPS':>8} {'OPM%':>8}")
    for row in pl:
        print(f"{row[0]:<12} {str(row[1]):>12} {str(row[2]):>12} {str(row[3]):>8} {str(row[4]):>8}")

    # Balance sheet latest year
    bs = conn.execute("""
        SELECT year, total_assets, total_liabilities, borrowings, reserves
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year DESC LIMIT 1
    """, (company,)).fetchone()
    print(f"\nBalance Sheet (latest):")
    if bs:
        print(f"Year: {bs[0]}, Assets: {bs[1]}, Liabilities: {bs[2]}, Borrowings: {bs[3]}, Reserves: {bs[4]}")

    # Cash flow latest year
    cf = conn.execute("""
        SELECT year, operating_activity, investing_activity,
               financing_activity, net_cash_flow
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year DESC LIMIT 1
    """, (company,)).fetchone()
    print(f"\nCash Flow (latest):")
    if cf:
        print(f"Year: {cf[0]}, CFO: {cf[1]}, CFI: {cf[2]}, CFF: {cf[3]}, Net: {cf[4]}")

    # Years available
    yr_count = conn.execute("""
        SELECT COUNT(DISTINCT year) FROM profitandloss WHERE company_id = ?
    """, (company,)).fetchone()[0]
    print(f"\nYears of P&L data: {yr_count}")

conn.close()
print("\n=== Day 6 Manual Review Complete ===")