-- ================================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
-- Exploratory Queries -- Sprint 1 Day 5
-- ================================================================

-- Q1: Row counts for all 12 tables
SELECT 'companies' as table_name, COUNT(*) as rows FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- Q2: Year coverage per company in P&L (sorted ascending)
SELECT company_id,
       COUNT(DISTINCT year) as years_available,
       MIN(year) as earliest,
       MAX(year) as latest
FROM profitandloss
GROUP BY company_id
ORDER BY years_available ASC;

-- Q3: Companies with less than 5 years of P&L data
SELECT company_id, COUNT(DISTINCT year) as yr_count
FROM profitandloss
GROUP BY company_id
HAVING yr_count < 5
ORDER BY yr_count ASC;

-- Q4: Null check on key P&L fields
SELECT
    COUNT(*) as total_rows,
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) as null_sales,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) as null_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) as null_eps
FROM profitandloss;

-- Q5: Sector distribution of all 92 companies
SELECT broad_sector,
       COUNT(*) as company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;

-- Q6: Top 10 companies by latest year sales
SELECT p.company_id,
       c.company_name,
       p.year,
       p.sales
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
WHERE p.year = (SELECT MAX(year) FROM profitandloss)
ORDER BY p.sales DESC
LIMIT 10;

-- Q7: Companies with no cash flow data
SELECT c.id, c.company_name
FROM companies c
LEFT JOIN cashflow cf ON c.id = cf.company_id
WHERE cf.company_id IS NULL;

-- Q8: Year range in each time series table
SELECT 'profitandloss' as tbl, MIN(year) as min_yr, MAX(year) as max_yr FROM profitandloss
UNION ALL SELECT 'balancesheet', MIN(year), MAX(year) FROM balancesheet
UNION ALL SELECT 'cashflow', MIN(year), MAX(year) FROM cashflow
UNION ALL SELECT 'financial_ratios', MIN(year), MAX(year) FROM financial_ratios;

-- Q9: Peer group distribution
SELECT peer_group_name,
       COUNT(*) as members,
       SUM(is_benchmark) as has_benchmark
FROM peer_groups
GROUP BY peer_group_name
ORDER BY members DESC;

-- Q10: Balance sheet null check
SELECT
    COUNT(*) as total_rows,
    SUM(CASE WHEN total_assets IS NULL THEN 1 ELSE 0 END) as null_assets,
    SUM(CASE WHEN borrowings IS NULL THEN 1 ELSE 0 END) as null_borrowings,
    SUM(CASE WHEN reserves IS NULL THEN 1 ELSE 0 END) as null_reserves
FROM balancesheet;
