-- ============================================================
-- LLM Chat Lab — ML Feature Table Setup
-- Dataset: FEMA National Flood Insurance Program Claims
-- Source:  SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE
--         .FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX
-- Task:   Predict flood CAUSE_OF_DAMAGE from claim features
-- ============================================================

-- 1. Create database and schema
CREATE DATABASE IF NOT EXISTS LLM_CHAT_LAB_DB;
USE DATABASE LLM_CHAT_LAB_DB;
CREATE SCHEMA IF NOT EXISTS ML;
USE SCHEMA ML;

-- 2. Create the ML feature table (materialized from the free dataset)
--    We engineer features from the raw claim data and keep the top 4
--    damage causes (covers 90%+ of claims) as our classification target.
CREATE OR REPLACE TABLE FLOOD_CLAIM_FEATURES AS
WITH raw AS (
    SELECT
        CAUSE_OF_DAMAGE,
        OCCUPANCY_TYPE,
        NUMBER_OF_FLOORS,
        BUILDING_TYPE,
        FLOOD_WATER_DEPTH,
        FLOOD_WATER_DURATION_HOURS,
        BUILDING_PROPERTY_VALUE,
        BUILDING_DAMAGE_AMOUNT,
        CONTENTS_PROPERTY_VALUE,
        CONTENTS_DAMAGE_AMOUNT,
        TOTAL_BUILDING_INSURANCE_COVERAGE,
        TOTAL_CONTENTS_INSURANCE_COVERAGE,
        BUILDING_DEDUCTIBLE,
        CONTENTS_DEDUCTIBLE,
        REPLACEMENT_COST_BASIS,
        CURRENT_FLOOD_ZONE,
        BASEMENT_ENCLOSURE_CRAWLSPACE,
        DATE_OF_LOSS,
        ORIGINAL_CONSTRUCTION_DATE,
        LATITUDE,
        LONGITUDE,
        STATE_GEO_ID,
        ELEVATION_DIFFERENCE,
        BASE_FLOOD_ELEVATION
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE
         .FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX
    WHERE CAUSE_OF_DAMAGE IN (
        'Accumulation of rainfall or snowmelt',
        'Tidal water overflow',
        'Stream, river, or lake overflow',
        'Other causes'
    )
    AND BUILDING_DAMAGE_AMOUNT IS NOT NULL
    AND BUILDING_PROPERTY_VALUE IS NOT NULL
    AND BUILDING_PROPERTY_VALUE > 0
)
SELECT
    -- Target
    CAUSE_OF_DAMAGE                                          AS DAMAGE_CAUSE,

    -- Property features
    OCCUPANCY_TYPE,
    NUMBER_OF_FLOORS,
    BUILDING_TYPE,
    REPLACEMENT_COST_BASIS,
    CURRENT_FLOOD_ZONE,
    COALESCE(BASEMENT_ENCLOSURE_CRAWLSPACE, 'Unknown')       AS BASEMENT_TYPE,

    -- Numeric features
    COALESCE(FLOOD_WATER_DEPTH, 0)                           AS WATER_DEPTH_FT,
    COALESCE(FLOOD_WATER_DURATION_HOURS, 0)                  AS WATER_DURATION_HRS,
    BUILDING_PROPERTY_VALUE                                   AS PROPERTY_VALUE,
    BUILDING_DAMAGE_AMOUNT                                    AS DAMAGE_AMOUNT,
    COALESCE(CONTENTS_PROPERTY_VALUE, 0)                     AS CONTENTS_VALUE,
    COALESCE(CONTENTS_DAMAGE_AMOUNT, 0)                      AS CONTENTS_DAMAGE,
    COALESCE(TOTAL_BUILDING_INSURANCE_COVERAGE, 0)           AS INSURANCE_COVERAGE,
    COALESCE(TOTAL_CONTENTS_INSURANCE_COVERAGE, 0)           AS CONTENTS_COVERAGE,
    COALESCE(BUILDING_DEDUCTIBLE, 0)                         AS DEDUCTIBLE,
    COALESCE(ELEVATION_DIFFERENCE, 0)                        AS ELEVATION_DIFF,

    -- Derived ratios
    ROUND(BUILDING_DAMAGE_AMOUNT / NULLIF(BUILDING_PROPERTY_VALUE, 0), 4)
                                                              AS DAMAGE_RATIO,
    ROUND(COALESCE(TOTAL_BUILDING_INSURANCE_COVERAGE, 0)
          / NULLIF(BUILDING_PROPERTY_VALUE, 0), 4)           AS COVERAGE_RATIO,

    -- Geo features
    COALESCE(LATITUDE, 0)                                    AS LAT,
    COALESCE(LONGITUDE, 0)                                   AS LON,
    COALESCE(STATE_GEO_ID, 'Unknown')                        AS STATE_GEO,

    -- Temporal features
    EXTRACT(MONTH FROM DATE_OF_LOSS)                         AS LOSS_MONTH,
    EXTRACT(YEAR FROM DATE_OF_LOSS)                          AS LOSS_YEAR,
    DATEDIFF('year',
             COALESCE(ORIGINAL_CONSTRUCTION_DATE, DATE_OF_LOSS),
             DATE_OF_LOSS)                                   AS BUILDING_AGE_YRS

FROM raw
WHERE BUILDING_DAMAGE_AMOUNT >= 0
  AND DAMAGE_AMOUNT <= BUILDING_PROPERTY_VALUE * 5;

-- 3. Quick validation
SELECT DAMAGE_CAUSE, COUNT(*) AS cnt
FROM FLOOD_CLAIM_FEATURES
GROUP BY DAMAGE_CAUSE
ORDER BY cnt DESC;

SELECT COUNT(*) AS total_rows FROM FLOOD_CLAIM_FEATURES;
