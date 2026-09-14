-- ================================================================
-- 01 BEGINNER: Exploring & Discovering Datasets
-- ================================================================
-- Skills: SHOW, SELECT, LIMIT, WHERE, ILIKE, ORDER BY, COUNT
-- No JOINs required. Each query is self-contained.
-- ================================================================

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION A: What databases and tables exist?
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- A1. List all databases you can access
SHOW DATABASES;

-- A2. List all tables in the public free data
SELECT TABLE_NAME, LEFT(COMMENT, 100) AS DESCRIPTION
FROM SNOWFLAKE_PUBLIC_DATA_FREE.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC_DATA_FREE'
  AND TABLE_NAME NOT LIKE '%_PIT'         -- exclude audit tables
  AND TABLE_NAME NOT LIKE '%_ATTRIBUTES'  -- exclude metadata tables
ORDER BY TABLE_NAME;

-- A3. Count how many datasets are available
SELECT COUNT(DISTINCT TABLE_NAME) AS DATASET_COUNT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC_DATA_FREE'
  AND TABLE_NAME NOT LIKE '%_PIT'
  AND TABLE_NAME NOT LIKE '%_ATTRIBUTES';

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION B: Peeking at data (SELECT + LIMIT)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- B1. Preview the calendar reference table
SELECT * FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CALENDAR_INDEX LIMIT 10;

-- B2. Preview airport data
SELECT * FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX LIMIT 10;

-- B3. Preview geographic reference
SELECT * FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX LIMIT 10;

-- B4. Preview company data
SELECT * FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX LIMIT 10;

-- B5. Preview TPC-H customer data (supply chain benchmark)
SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER LIMIT 10;

-- B6. Preview TPC-H orders
SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS LIMIT 10;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION C: Filtering with WHERE
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- C1. Find airports in California
SELECT *
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX
WHERE STATE = 'CA'
LIMIT 20;

-- C2. Find companies with "Tesla" in the name
SELECT *
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX
WHERE COMPANY_NAME ILIKE '%tesla%'
LIMIT 10;

-- C3. Find FEMA disasters in Texas in the last 5 years
SELECT *
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX
WHERE STATE = 'TX'
  AND DECLARATION_DATE >= DATEADD('year', -5, CURRENT_DATE())
LIMIT 20;

-- C4. Find high-priority orders (TPC-H)
SELECT O_ORDERKEY, O_CUSTKEY, O_ORDERSTATUS, O_TOTALPRICE, O_ORDERDATE, O_ORDERPRIORITY
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
WHERE O_ORDERPRIORITY = '1-URGENT'
  AND O_TOTALPRICE > 200000
LIMIT 20;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION D: Sorting with ORDER BY
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- D1. Most expensive orders
SELECT O_ORDERKEY, O_TOTALPRICE, O_ORDERDATE, O_ORDERPRIORITY
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
ORDER BY O_TOTALPRICE DESC
LIMIT 20;

-- D2. Most recent FEMA disaster declarations
SELECT *
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX
ORDER BY DECLARATION_DATE DESC
LIMIT 20;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION E: Basic counting and grouping
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- E1. Count airports by state
SELECT STATE, COUNT(*) AS AIRPORT_COUNT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX
GROUP BY STATE
ORDER BY AIRPORT_COUNT DESC
LIMIT 20;

-- E2. Count FEMA disasters by incident type
SELECT INCIDENT_TYPE, COUNT(*) AS COUNT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX
GROUP BY INCIDENT_TYPE
ORDER BY COUNT DESC;

-- E3. Count orders by status (TPC-H)
SELECT O_ORDERSTATUS, COUNT(*) AS ORDER_COUNT
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
GROUP BY O_ORDERSTATUS
ORDER BY ORDER_COUNT DESC;

-- E4. Count orders by priority (TPC-H)
SELECT O_ORDERPRIORITY, COUNT(*) AS ORDER_COUNT
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
GROUP BY O_ORDERPRIORITY
ORDER BY ORDER_COUNT DESC;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION F: Browsing variable catalogs (what metrics exist?)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- F1. What BLS employment variables are available?
SELECT VARIABLE_ID, VARIABLE_NAME, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES
LIMIT 30;

-- F2. What CPI/price variables exist?
SELECT VARIABLE_ID, VARIABLE_NAME, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_ATTRIBUTES
LIMIT 30;

-- F3. Search for unemployment-related variables
SELECT VARIABLE_ID, VARIABLE_NAME, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES
WHERE VARIABLE_NAME ILIKE '%unemployment%'
LIMIT 20;

-- F4. Search for GDP-related variables in World Bank data
SELECT VARIABLE_ID, VARIABLE_NAME, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.WORLD_BANK_ATTRIBUTES
WHERE VARIABLE_NAME ILIKE '%GDP%'
LIMIT 20;

-- F5. What energy variables does EIA track?
SELECT VARIABLE_ID, VARIABLE_NAME, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.EIA_ENERGY_ATTRIBUTES
WHERE VARIABLE_NAME ILIKE '%natural gas%'
LIMIT 20;

-- F6. What house price metrics exist?
SELECT VARIABLE_ID, VARIABLE_NAME, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_ATTRIBUTES
LIMIT 20;
