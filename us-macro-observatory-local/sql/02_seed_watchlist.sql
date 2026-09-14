-- =============================================================
-- 02_seed_watchlist.sql
-- Optional: pre-populate the watchlist with sample entries
-- so the app is not empty on first launch.
-- =============================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

-- Only insert if the table is empty (idempotent seed)
INSERT INTO WATCHLIST (ENTITY_TYPE, ENTITY_NAME, TARGET_VALUE, NOTES)
SELECT column1, column2, column3, column4
FROM VALUES
    ('State (Unemployment)', 'California',       4.50,  'Largest state economy — watch for tech layoff impact'),
    ('State (Unemployment)', 'Texas',             3.80,  'Energy sector recovery indicator'),
    ('State (Unemployment)', 'New York',           4.00,  'Financial sector bellwether'),
    ('Company',              'APPLE INC',          NULL,  'Market cap leader — consumer spending proxy'),
    ('Company',              'MICROSOFT CORP',     NULL,  'Enterprise tech demand signal'),
    ('Economic Indicator',   'CPI: All items',     3.00,  'Target: Fed 2% goal — currently above'),
    ('Economic Indicator',   'HPI Index',        500.00,  'Tracking housing affordability threshold')
WHERE NOT EXISTS (SELECT 1 FROM WATCHLIST LIMIT 1);
