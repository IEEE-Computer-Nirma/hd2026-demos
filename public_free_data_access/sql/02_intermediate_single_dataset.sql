-- ================================================================
-- 02 INTERMEDIATE: Single-Dataset Deep Dives
-- ================================================================
-- Skills: JOINs, GROUP BY, HAVING, date functions, CASE,
--         window functions (LAG, RANK, running totals), CTEs
-- Each section works within one dataset domain.
-- ================================================================

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION A: BLS Employment Data (JOIN + time series)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- A1. US unemployment rate - last 5 years
SELECT
    a.VARIABLE_NAME,
    t.DATE,
    t.VALUE,
    t.UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%unemployment rate%'
  AND t.DATE >= DATEADD('year', -5, CURRENT_DATE())
ORDER BY t.DATE DESC
LIMIT 100;

-- A2. Month-over-month change in unemployment (LAG window function)
WITH unemployment AS (
    SELECT
        t.DATE,
        t.VALUE AS RATE
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%unemployment rate%'
      AND a.VARIABLE_NAME ILIKE '%seasonally adjusted%'
      AND t.DATE >= '2020-01-01'
)
SELECT
    DATE,
    RATE,
    LAG(RATE) OVER (ORDER BY DATE) AS PREV_MONTH_RATE,
    RATE - LAG(RATE) OVER (ORDER BY DATE) AS MOM_CHANGE
FROM unemployment
ORDER BY DATE DESC
LIMIT 60;

-- A3. Annual average unemployment rate
SELECT
    YEAR(t.DATE) AS YEAR,
    ROUND(AVG(t.VALUE), 2) AS AVG_UNEMPLOYMENT_RATE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%unemployment rate%'
  AND a.VARIABLE_NAME ILIKE '%seasonally adjusted%'
GROUP BY YEAR(t.DATE)
HAVING COUNT(*) >= 6  -- at least 6 months of data
ORDER BY YEAR DESC;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION B: CPI / Inflation (aggregations + YoY comparison)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- B1. CPI All Items - monthly values
SELECT
    a.VARIABLE_NAME,
    t.DATE,
    t.VALUE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_ATTRIBUTES a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%all items%'
  AND a.VARIABLE_NAME ILIKE '%not seasonally adjusted%'
  AND t.DATE >= '2019-01-01'
ORDER BY t.DATE DESC
LIMIT 100;

-- B2. Year-over-year CPI inflation rate (calculated from index)
WITH cpi AS (
    SELECT
        t.DATE,
        t.VALUE AS CPI_INDEX
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%all items%'
      AND a.VARIABLE_NAME ILIKE '%not seasonally adjusted%'
)
SELECT
    c.DATE,
    c.CPI_INDEX,
    prev.CPI_INDEX AS CPI_INDEX_YEAR_AGO,
    ROUND((c.CPI_INDEX - prev.CPI_INDEX) / prev.CPI_INDEX * 100, 2) AS YOY_INFLATION_PCT
FROM cpi c
JOIN cpi prev ON prev.DATE = DATEADD('year', -1, c.DATE)
WHERE c.DATE >= '2015-01-01'
ORDER BY c.DATE DESC;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION C: House Prices (CASE statements + ranking)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- C1. National house price index with market regime classification
SELECT
    t.DATE,
    t.VALUE AS HPI,
    LAG(t.VALUE) OVER (ORDER BY t.DATE) AS PREV_HPI,
    ROUND((t.VALUE - LAG(t.VALUE) OVER (ORDER BY t.DATE))
        / NULLIF(LAG(t.VALUE) OVER (ORDER BY t.DATE), 0) * 100, 2) AS QOQ_CHANGE_PCT,
    CASE
        WHEN (t.VALUE - LAG(t.VALUE) OVER (ORDER BY t.DATE))
            / NULLIF(LAG(t.VALUE) OVER (ORDER BY t.DATE), 0) * 100 > 3 THEN 'HOT'
        WHEN (t.VALUE - LAG(t.VALUE) OVER (ORDER BY t.DATE))
            / NULLIF(LAG(t.VALUE) OVER (ORDER BY t.DATE), 0) * 100 > 0 THEN 'WARMING'
        WHEN (t.VALUE - LAG(t.VALUE) OVER (ORDER BY t.DATE))
            / NULLIF(LAG(t.VALUE) OVER (ORDER BY t.DATE), 0) * 100 > -2 THEN 'COOLING'
        ELSE 'DECLINING'
    END AS MARKET_REGIME
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_ATTRIBUTES a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%purchase-only%'
  AND a.VARIABLE_NAME ILIKE '%nation%'
  AND t.DATE >= '2000-01-01'
ORDER BY t.DATE DESC;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION D: FEMA Disasters (multi-level aggregation)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- D1. Disasters per state per year, ranked
WITH yearly AS (
    SELECT
        STATE,
        YEAR(DECLARATION_DATE) AS YEAR,
        COUNT(*) AS DISASTER_COUNT
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX
    WHERE DECLARATION_DATE >= '2015-01-01'
    GROUP BY STATE, YEAR(DECLARATION_DATE)
)
SELECT
    STATE,
    YEAR,
    DISASTER_COUNT,
    RANK() OVER (PARTITION BY YEAR ORDER BY DISASTER_COUNT DESC) AS RANK_IN_YEAR
FROM yearly
QUALIFY RANK_IN_YEAR <= 5
ORDER BY YEAR DESC, RANK_IN_YEAR;

-- D2. Most common disaster types per decade
SELECT
    FLOOR(YEAR(DECLARATION_DATE) / 10) * 10 AS DECADE,
    INCIDENT_TYPE,
    COUNT(*) AS COUNT,
    RANK() OVER (PARTITION BY DECADE ORDER BY COUNT(*) DESC) AS RANK
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX
GROUP BY DECADE, INCIDENT_TYPE
QUALIFY RANK <= 5
ORDER BY DECADE DESC, RANK;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION E: Climate / Emissions (running totals + pivoting)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- E1. Top 10 CO2 emitters with cumulative share
WITH latest_emissions AS (
    SELECT
        t.GEO_ID,
        SUM(t.VALUE) AS TOTAL_CO2
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CLIMATE_WATCH_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CLIMATE_WATCH_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%CO2%'
      AND t.DATE >= '2018-01-01'
    GROUP BY t.GEO_ID
)
SELECT
    GEO_ID,
    TOTAL_CO2,
    ROUND(TOTAL_CO2 / SUM(TOTAL_CO2) OVER () * 100, 2) AS PCT_OF_GLOBAL,
    ROUND(SUM(TOTAL_CO2) OVER (ORDER BY TOTAL_CO2 DESC
        ROWS UNBOUNDED PRECEDING) / SUM(TOTAL_CO2) OVER () * 100, 2) AS CUMULATIVE_PCT
FROM latest_emissions
ORDER BY TOTAL_CO2 DESC
LIMIT 15;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION F: Company Data (self-joins + hierarchy)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- F1. Find a company and its subsidiaries
SELECT
    p.COMPANY_NAME AS PARENT_COMPANY,
    c.COMPANY_NAME AS SUBSIDIARY
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_RELATIONSHIPS r
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX p
    ON r.RELATED_COMPANY_ID = p.COMPANY_ID
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX c
    ON r.COMPANY_ID = c.COMPANY_ID
WHERE p.COMPANY_NAME ILIKE '%alphabet%'
LIMIT 30;

-- F2. Companies with the most subsidiaries
SELECT
    p.COMPANY_NAME,
    COUNT(*) AS SUBSIDIARY_COUNT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_RELATIONSHIPS r
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX p
    ON r.RELATED_COMPANY_ID = p.COMPANY_ID
GROUP BY p.COMPANY_NAME
ORDER BY SUBSIDIARY_COUNT DESC
LIMIT 20;

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION G: Federal Reserve (multiple metrics comparison)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- G1. Browse Fed variables to find interesting ones
SELECT VARIABLE_ID, VARIABLE_NAME, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEDERAL_RESERVE_ATTRIBUTES
WHERE VARIABLE_NAME ILIKE '%interest%'
   OR VARIABLE_NAME ILIKE '%consumer credit%'
LIMIT 30;

-- G2. Consumer credit trend with rolling 12-month average
WITH credit AS (
    SELECT
        t.DATE,
        t.VALUE
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEDERAL_RESERVE_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEDERAL_RESERVE_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%consumer credit%'
      AND t.DATE >= '2010-01-01'
)
SELECT
    DATE,
    VALUE,
    ROUND(AVG(VALUE) OVER (ORDER BY DATE ROWS BETWEEN 11 PRECEDING AND CURRENT ROW), 2)
        AS ROLLING_12M_AVG
FROM credit
ORDER BY DATE DESC
LIMIT 100;
