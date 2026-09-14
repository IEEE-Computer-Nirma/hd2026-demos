-- ================================================================
-- 03 ADVANCED: Cross-Dataset Analysis & Composite Indicators
-- ================================================================
-- Skills: Multi-source JOINs, GEOGRAPHY_INDEX linking, CTEs,
--         PIVOT, composite scoring, macro correlations,
--         temporal alignment across different frequencies
-- ================================================================

-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION A: Macro Dashboard – Unemployment + Inflation + House Prices
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- A1. Monthly macro snapshot: unemployment rate, CPI inflation, and house prices
--     Three different datasets joined by date
WITH unemployment AS (
    SELECT t.DATE, t.VALUE AS UNEMPLOYMENT_RATE
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%unemployment rate%'
      AND a.VARIABLE_NAME ILIKE '%seasonally adjusted%'
      AND t.DATE >= '2015-01-01'
),
cpi_raw AS (
    SELECT t.DATE, t.VALUE AS CPI_INDEX
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%all items%'
      AND a.VARIABLE_NAME ILIKE '%not seasonally adjusted%'
),
cpi AS (
    SELECT
        c.DATE,
        c.CPI_INDEX,
        ROUND((c.CPI_INDEX - prev.CPI_INDEX) / NULLIF(prev.CPI_INDEX, 0) * 100, 2)
            AS YOY_INFLATION_PCT
    FROM cpi_raw c
    JOIN cpi_raw prev ON prev.DATE = DATEADD('year', -1, c.DATE)
    WHERE c.DATE >= '2015-01-01'
),
house_prices AS (
    SELECT t.DATE, t.VALUE AS HPI
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%purchase-only%'
      AND a.VARIABLE_NAME ILIKE '%nation%'
)
SELECT
    u.DATE,
    u.UNEMPLOYMENT_RATE,
    c.YOY_INFLATION_PCT,
    h.HPI AS HOUSE_PRICE_INDEX
FROM unemployment u
LEFT JOIN cpi c ON c.DATE = u.DATE
LEFT JOIN house_prices h ON h.DATE = u.DATE
ORDER BY u.DATE DESC
LIMIT 100;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION B: Fed Policy Impact – Interest Rates vs Economy
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- B1. Combine Fed Funds rate proxies with unemployment and CPI
WITH fed AS (
    SELECT t.DATE, t.VALUE AS FED_VALUE, a.VARIABLE_NAME
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEDERAL_RESERVE_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEDERAL_RESERVE_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%interest%'
      AND t.DATE >= '2015-01-01'
),
unemployment AS (
    SELECT t.DATE, t.VALUE AS UNEMPLOYMENT_RATE
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%unemployment rate%'
      AND a.VARIABLE_NAME ILIKE '%seasonally adjusted%'
)
SELECT
    u.DATE,
    u.UNEMPLOYMENT_RATE,
    f.FED_VALUE,
    f.VARIABLE_NAME AS FED_METRIC
FROM unemployment u
JOIN fed f ON f.DATE = u.DATE
ORDER BY u.DATE DESC
LIMIT 100;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION C: Geographic Enrichment – Join via GEOGRAPHY_INDEX
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- C1. Enrich BLS employment data with geographic names
SELECT
    g.GEO_NAME,
    g.ISO_ALPHA2,
    a.VARIABLE_NAME,
    t.DATE,
    t.VALUE,
    t.UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES a
    USING (VARIABLE_ID)
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX g
    ON t.GEO_ID = g.GEO_ID
WHERE a.VARIABLE_NAME ILIKE '%unemployment rate%'
  AND t.DATE >= DATEADD('month', -6, CURRENT_DATE())
ORDER BY g.GEO_NAME, t.DATE DESC
LIMIT 100;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION D: Global Comparison – CO2 Emissions vs GDP
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- D1. Per-country CO2 emissions alongside World Bank GDP
WITH co2 AS (
    SELECT
        t.GEO_ID,
        YEAR(t.DATE) AS YEAR,
        SUM(t.VALUE) AS TOTAL_CO2
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CLIMATE_WATCH_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CLIMATE_WATCH_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%CO2%'
    GROUP BY t.GEO_ID, YEAR(t.DATE)
),
gdp AS (
    SELECT
        t.GEO_ID,
        YEAR(t.DATE) AS YEAR,
        t.VALUE AS GDP
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.WORLD_BANK_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.WORLD_BANK_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%GDP%current US%'
)
SELECT
    g.GEO_NAME,
    co2.YEAR,
    co2.TOTAL_CO2,
    gdp.GDP,
    CASE WHEN gdp.GDP > 0
        THEN ROUND(co2.TOTAL_CO2 / (gdp.GDP / 1000000), 4)
        ELSE NULL
    END AS CO2_PER_MILLION_GDP
FROM co2
JOIN gdp ON co2.GEO_ID = gdp.GEO_ID AND co2.YEAR = gdp.YEAR
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX g
    ON co2.GEO_ID = g.GEO_ID
WHERE co2.YEAR >= 2010
ORDER BY co2.YEAR DESC, co2.TOTAL_CO2 DESC
LIMIT 50;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION E: US State Composite Risk Score
--            (disasters + crime + flood claims)
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- E1. Build a composite risk score per US state
WITH disasters AS (
    SELECT STATE, COUNT(*) AS DISASTER_COUNT
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX
    WHERE DECLARATION_DATE >= DATEADD('year', -10, CURRENT_DATE())
    GROUP BY STATE
),
crime AS (
    SELECT
        t.GEO_ID,
        AVG(t.VALUE) AS AVG_CRIME_RATE
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FBI_CRIME_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FBI_CRIME_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%violent%'
      AND t.DATE >= DATEADD('year', -5, CURRENT_DATE())
    GROUP BY t.GEO_ID
),
geo AS (
    SELECT GEO_ID, GEO_NAME
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX
)
SELECT
    d.STATE,
    d.DISASTER_COUNT,
    c.AVG_CRIME_RATE,
    -- Normalized composite score (higher = more risk)
    ROUND(
        (d.DISASTER_COUNT / NULLIF(MAX(d.DISASTER_COUNT) OVER (), 0)) * 50 +
        (c.AVG_CRIME_RATE / NULLIF(MAX(c.AVG_CRIME_RATE) OVER (), 0)) * 50
    , 1) AS COMPOSITE_RISK_SCORE
FROM disasters d
LEFT JOIN geo g ON g.GEO_NAME ILIKE '%' || d.STATE || '%'
LEFT JOIN crime c ON c.GEO_ID = g.GEO_ID
WHERE d.STATE IS NOT NULL
ORDER BY COMPOSITE_RISK_SCORE DESC NULLS LAST
LIMIT 25;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION F: Aviation + Weather – Flight Corridors & Conditions
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- F1. Join airport locations with weather observations
SELECT
    ap.AIRPORT_NAME,
    ap.STATE,
    ap.LATITUDE,
    ap.LONGITUDE,
    a.VARIABLE_NAME AS WEATHER_METRIC,
    t.DATE,
    t.VALUE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AWC_METAR_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AWC_METAR_ATTRIBUTES a
    USING (VARIABLE_ID)
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX ap
    ON t.GEO_ID = ap.GEO_ID
WHERE a.VARIABLE_NAME ILIKE '%temperature%'
  AND t.DATE >= DATEADD('day', -7, CURRENT_DATE())
ORDER BY t.DATE DESC
LIMIT 100;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION G: International Trade + Emissions Correlation
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- G1. Does trade growth correlate with emissions growth?
WITH trade AS (
    SELECT
        t.GEO_ID,
        YEAR(t.DATE) AS YEAR,
        SUM(t.VALUE) AS TRADE_VALUE
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.WORLD_TRADE_ORGANIZATION_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.WORLD_TRADE_ORGANIZATION_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%export%'
    GROUP BY t.GEO_ID, YEAR(t.DATE)
),
emissions AS (
    SELECT
        t.GEO_ID,
        YEAR(t.DATE) AS YEAR,
        SUM(t.VALUE) AS TOTAL_EMISSIONS
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.EUROPEAN_COMMISSION_EDGAR_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.EUROPEAN_COMMISSION_EDGAR_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%CO2%'
    GROUP BY t.GEO_ID, YEAR(t.DATE)
)
SELECT
    g.GEO_NAME,
    tr.YEAR,
    tr.TRADE_VALUE,
    em.TOTAL_EMISSIONS,
    ROUND(em.TOTAL_EMISSIONS / NULLIF(tr.TRADE_VALUE, 0) * 1000, 4)
        AS EMISSIONS_PER_TRADE_UNIT
FROM trade tr
JOIN emissions em ON tr.GEO_ID = em.GEO_ID AND tr.YEAR = em.YEAR
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX g
    ON tr.GEO_ID = g.GEO_ID
WHERE tr.YEAR >= 2010
ORDER BY tr.YEAR DESC, tr.TRADE_VALUE DESC
LIMIT 50;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION H: Housing + Banking – Mortgage Performance vs House Prices
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- H1. Overlay house prices with mortgage delinquency trends
WITH hpi AS (
    SELECT t.DATE, t.VALUE AS HPI
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%purchase-only%'
      AND a.VARIABLE_NAME ILIKE '%nation%'
),
mortgage AS (
    SELECT t.DATE, t.VALUE AS MORTGAGE_METRIC, a.VARIABLE_NAME
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_MORTGAGE_PERFORMANCE_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_MORTGAGE_PERFORMANCE_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%delinquen%'
)
SELECT
    h.DATE,
    h.HPI,
    m.MORTGAGE_METRIC,
    m.VARIABLE_NAME AS DELINQUENCY_METRIC
FROM hpi h
JOIN mortgage m ON m.DATE = h.DATE
WHERE h.DATE >= '2005-01-01'
ORDER BY h.DATE DESC
LIMIT 100;


-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- SECTION I: Energy + Climate – Power Plant Emissions vs Energy Production
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-- I1. Compare EIA energy production with EPA power plant emissions
WITH energy AS (
    SELECT
        YEAR(t.DATE) AS YEAR,
        a.VARIABLE_NAME,
        AVG(t.VALUE) AS AVG_PRODUCTION
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.EIA_ENERGY_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.EIA_ENERGY_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%electricity%generation%'
    GROUP BY YEAR(t.DATE), a.VARIABLE_NAME
),
epa AS (
    SELECT
        YEAR(t.DATE) AS YEAR,
        a.VARIABLE_NAME,
        SUM(t.VALUE) AS TOTAL_EMISSIONS
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.EPA_CAM_TIMESERIES t
    JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.EPA_CAM_ATTRIBUTES a
        USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%CO2%'
    GROUP BY YEAR(t.DATE), a.VARIABLE_NAME
)
SELECT
    e.YEAR,
    e.VARIABLE_NAME AS ENERGY_METRIC,
    e.AVG_PRODUCTION,
    p.TOTAL_EMISSIONS AS POWER_PLANT_CO2,
    p.VARIABLE_NAME AS EMISSIONS_METRIC
FROM energy e
JOIN epa p ON e.YEAR = p.YEAR
WHERE e.YEAR >= 2010
ORDER BY e.YEAR DESC
LIMIT 50;
