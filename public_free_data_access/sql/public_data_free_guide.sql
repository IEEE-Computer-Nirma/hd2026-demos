-- Reference guide for SNOWFLAKE_PUBLIC_DATA_FREE: listing and querying public datasets
-- Co-authored with CoCo

-- ============================================================
-- 1. LIST ALL DATASETS (deduplicated, no _PIT / _ATTRIBUTES noise)
-- ============================================================
SELECT DISTINCT
    TABLE_NAME,
    LEFT(COMMENT, 120)  AS DESCRIPTION
FROM SNOWFLAKE_PUBLIC_DATA_FREE.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC_DATA_FREE'
  AND TABLE_NAME NOT LIKE '%_PIT'
  AND TABLE_NAME NOT LIKE '%_ATTRIBUTES'
ORDER BY TABLE_NAME;

-- ============================================================
-- 2. DATASET CATALOGUE (grouped by category)
-- ============================================================
/*
AVIATION
  AIRCRAFT_CARRIER_INDEX        Airline carrier codes and names
  AIRCRAFT_INDEX                Aircraft models and cabin configs
  AIRPORT_INDEX                 US airports (DOT/IATA codes)
  AWC_METAR_TIMESERIES          Hourly airport weather observations (METAR)
  AWC_TAF_TIMESERIES            Airport weather forecasts (TAF)
  US_DOT_DOMESTIC_SEGMENT_*     US domestic flight segments

CLIMATE / ENVIRONMENT
  CLIMATE_WATCH_TIMESERIES      Country-level GHG emissions & future scenarios
  EPA_CAM_TIMESERIES            Power-plant SO2/NOx/CO2 emissions (hourly & quarterly)
  EUROPEAN_COMMISSION_EDGAR_TIMESERIES  Global CO2/CH4/N2O/F-gas emissions

COMPANY / MARKETS
  COMPANY_INDEX                 ~100k public & private companies (CIK, EIN, LEI, PermID)
  COMPANY_CHARACTERISTICS       Company attributes with date ranges
  COMPANY_RELATIONSHIPS         Parent/subsidiary hierarchy
  COMPANY_SECURITY_RELATIONSHIPS  Company-to-security mapping (OpenFIGI, PermID)
  COMPANY_DOMAIN_RELATIONSHIPS  Company-to-website/domain mapping
  COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES  Earnings call transcripts (JSON)
  SEC_*                         SEC filings (EDGAR), financial statements
  XBRL_TAXONOMY_INDEX           XBRL element definitions used in SEC filings

ECONOMICS / FINANCE
  FEDERAL_RESERVE_TIMESERIES    Fed data: consumer credit, industrial production, etc.
  BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES  BIS: property prices, policy rates
  EUROPEAN_CENTRAL_BANK_TIMESERIES  ECB: CPI, property prices/valuations (Europe)
  WORLD_BANK_TIMESERIES         World development indicators
  WORLD_TRADE_ORGANIZATION_TIMESERIES  WTO trade flows & tariff data
  FDIC_SUMMARY_OF_DEPOSITS_TIMESERIES  FDIC bank branch deposits (annual)
  FDIC_BRANCH_LOCATIONS_INDEX   FDIC bank branch locations
  FINANCIAL_BRANCH_ENTITIES     FFIEC US bank branch locations
  FINANCIAL_CFPB_COMPLAINT      CFPB consumer financial complaints

US GOVERNMENT / DEMOGRAPHIC
  AMERICAN_COMMUNITY_SURVEY_TIMESERIES  US Census ACS (demographics, housing, income)
  BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES  BLS employment/unemployment
  BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES  BLS CPI & average prices
  DATACOMMONS_TIMESERIES        Google Data Commons (demographics, environment)
  FBI_CRIME_TIMESERIES          US FBI crime statistics (1979+)
  FEMA_DISASTER_DECLARATION_INDEX  Federally declared disasters & funding
  FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_*  NFIP flood insurance policies & claims

HOUSING / REAL ESTATE
  FHFA_HOUSE_PRICE_TIMESERIES   Single-family HPI since 1975 (Fannie/Freddie)
  FHFA_MORTGAGE_PERFORMANCE_TIMESERIES  Mortgage originations & delinquency
  FHFA_UNIFORM_APPRAISAL_TIMESERIES  Home appraisal trends since 2013

ENERGY
  EIA_ENERGY_TIMESERIES         US EIA: natural gas, electricity, petroleum, coal

CANADA
  CANADA_STATCAN_TIMESERIES     Statistics Canada: GDP, CPI, labor, census data

REFERENCE / LOOKUP
  CALENDAR_INDEX                Common calendar periods (day/week/month/quarter/year)
  GEOGRAPHY_INDEX               Geographic entities (joinable key for timeseries tables)
*/

-- ============================================================
-- 3. HOW TIMESERIES DATASETS WORK
-- ============================================================
/*
Most datasets follow this 3-table pattern:

  *_TIMESERIES    – the actual data rows (variable_id, geo_id, date, value)
  *_ATTRIBUTES    – variable metadata (what each variable_id means)
  *_PIT           – point-in-time history (use for audit/backfill; NULLs on current rows)

A typical join:

    SELECT
        a.VARIABLE_NAME,
        t.DATE,
        t.VALUE,
        t.UNIT
    FROM <source>_TIMESERIES  t
    JOIN <source>_ATTRIBUTES  a  USING (VARIABLE_ID)
    WHERE a.VARIABLE_NAME ILIKE '%unemployment%'
    ORDER BY t.DATE DESC
    LIMIT 100;
*/

-- ============================================================
-- 4. EXAMPLE QUERIES
-- ============================================================

-- A) US Unemployment Rate (BLS) – last 24 months
SELECT
    a.VARIABLE_NAME,
    t.DATE,
    t.VALUE,
    t.UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES  t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%unemployment rate%'
  AND t.DATE >= DATEADD('month', -24, CURRENT_DATE())
ORDER BY t.DATE DESC
LIMIT 100;

-- B) US CPI (All Items, not seasonally adjusted) – last 12 months
SELECT
    a.VARIABLE_NAME,
    t.DATE,
    t.VALUE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES   t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_ATTRIBUTES   a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%all items%'
  AND t.DATE >= DATEADD('month', -12, CURRENT_DATE())
ORDER BY t.DATE DESC
LIMIT 50;

-- C) US House Price Index – national, purchase-only, quarterly
SELECT
    a.VARIABLE_NAME,
    t.DATE,
    t.VALUE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES   t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_ATTRIBUTES   a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%purchase-only%'
  AND t.DATE >= '2015-01-01'
ORDER BY t.DATE DESC
LIMIT 100;

-- D) Country-level CO2 emissions (Climate Watch) – top 10 emitters latest year
SELECT
    t.GEO_ID,
    MAX(t.DATE)  AS LATEST_DATE,
    SUM(t.VALUE) AS TOTAL_CO2
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CLIMATE_WATCH_TIMESERIES  t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CLIMATE_WATCH_ATTRIBUTES  a
    USING (VARIABLE_ID)
WHERE a.VARIABLE_NAME ILIKE '%CO2%'
GROUP BY t.GEO_ID
ORDER BY TOTAL_CO2 DESC
LIMIT 10;

-- E) Federally declared disasters by state (FEMA) – last 5 years
SELECT
    STATE,
    INCIDENT_TYPE,
    COUNT(*) AS DISASTER_COUNT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX
WHERE DECLARATION_DATE >= DATEADD('year', -5, CURRENT_DATE())
GROUP BY STATE, INCIDENT_TYPE
ORDER BY DISASTER_COUNT DESC
LIMIT 50;

-- F) S&P 500 / company lookup – find a company by name
SELECT *
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX
WHERE COMPANY_NAME ILIKE '%apple%'
LIMIT 10;

-- G) Browse available BLS employment variables
SELECT VARIABLE_ID, VARIABLE_NAME, REPORT, SEASONAL_ADJUSTMENT, INDUSTRY, UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_ATTRIBUTES
LIMIT 50;

-- H) Preview any table – quick sample
SELECT * FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CALENDAR_INDEX         LIMIT 5;
SELECT * FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX          LIMIT 5;
SELECT * FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FDIC_BRANCH_LOCATIONS_INDEX LIMIT 5;
