# US Macro Economic & Corporate Intelligence Observatory

A multi-page Streamlit-in-Snowflake application that combines US macroeconomic data (unemployment, CPI inflation, housing prices) with a 2M+ corporate entity directory, AI-powered analysis, and personal watchlist tracking.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup Guide](#setup-guide)
  - [Step 1 -- Get the Free Public Data](#step-1----get-the-free-public-data)
  - [Step 2 -- Create the Application Database](#step-2----create-the-application-database)
  - [Step 3 -- Seed Sample Data (Optional)](#step-3----seed-sample-data-optional)
  - [Step 4 -- Verify Data Access](#step-4----verify-data-access)
  - [Step 5 -- Create Analytical Views](#step-5----create-analytical-views)
  - [Step 6 -- Deploy the Streamlit App](#step-6----deploy-the-streamlit-app)
- [Project Structure](#project-structure)
- [Page Reference](#page-reference)
- [Snowflake Objects Reference](#snowflake-objects-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Features

| Page | Description |
|------|-------------|
| **Home / Overview** | KPI cards (unemployment, CPI, HPI, company count) with MoM/YoY deltas, z-scores, percentile ranks, trend slopes, and an AI-generated narrative summary |
| **Labor & Employment** | State-level unemployment rankings and multi-state comparative line charts |
| **Inflation & CPI** | CPI breakdown across 7 categories with YoY inflation rate charts |
| **Housing Market** | FHFA House Price Index trajectory and key metrics |
| **Company Directory** | Searchable/filterable browser over 2M+ SEC EDGAR / LEI / OpenFIGI entities with CSV export |
| **Cross-Domain Correlations** | Dual-axis comparison, Pearson correlation matrix, lead-lag analysis (+/-12 months), and YoY change overlays |
| **AI Economic Advisor** | Chat interface powered by Snowflake Cortex LLM with live data context injection |
| **SQL Studio** | Ad-hoc SELECT-only SQL explorer with 3 prebuilt query templates |
| **ML Training** | Train and evaluate forecasting models (Linear, Ridge, Random Forest, Gradient Boosting) on macro indicators with feature engineering, evaluation metrics, and AI-interpreted results |
| **My Watchlist** | Full CRUD to track states, companies, and indicators with notes and target values |

---

## Architecture

```
+----------------------------------------------------------+
|                STREAMLIT APP (SPCS)                       |
|                                                          |
|  streamlit_app.py  (entry point, nav, sidebar)           |
|       |                                                  |
|       +-- app_pages/home.py           \                  |
|       +-- app_pages/labor.py           |                 |
|       +-- app_pages/inflation.py       | Read-only       |
|       +-- app_pages/housing.py         | queries         |
|       +-- app_pages/companies.py       |                 |
|       +-- app_pages/correlations.py   /                  |
|       |                                                  |
|       +-- app_pages/ai_advisor.py --> CORTEX.COMPLETE()  |
|       +-- app_pages/sql_studio.py --> SELECT-only sandbox|
|       +-- app_pages/ml_training.py -> scikit-learn models |
|       +-- app_pages/watchlist.py  --> CRUD operations     |
|       |                                                  |
|       +-- utils/db.py  (all SQL, caching, Cortex wrapper)|
+----------+-----------------------------------+-----------+
           |                                   |
           v                                   v
+-------------------------+     +----------------------------+
| SNOWFLAKE_PUBLIC_DATA_  |     | HACKDAYS_APP_DB.APP_DATA   |
| FREE.PUBLIC_DATA_FREE   |     | (App-Owned, Read-Write)    |
| (Shared, Read-Only)     |     |                            |
|                         |     | - WATCHLIST                |
| - BLS Employment TS     |     | - CHAT_HISTORY             |
| - BLS Price TS (CPI)    |     | - INSIGHTS_LOG             |
| - FHFA House Price TS   |     | - V_MONTHLY_UNEMPLOYMENT   |
| - COMPANY_INDEX         |     | - V_MONTHLY_CPI            |
| - GEOGRAPHY_INDEX       |     | - V_MONTHLY_HPI            |
| - FEMA Disaster Index   |     | - V_MACRO_MONTHLY_SUMMARY  |
+-------------------------+     +----------------------------+
```

**Data flow:**

1. On startup, the app auto-creates the `HACKDAYS_APP_DB` database, schema, and tables if they don't exist.
2. Read-only pages query the free public data catalog through cached loaders (1-hour TTL).
3. The Home page computes statistical indicators in Python, then sends them to Cortex `llama3.1-70b` for narrative generation.
4. The AI Advisor injects live data snapshots into a system prompt and streams conversation through Cortex COMPLETE().
5. The Watchlist page performs full CRUD against `HACKDAYS_APP_DB.APP_DATA.WATCHLIST`.

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Snowflake account** | Any edition that supports Streamlit-in-Snowflake with SPCS |
| **Role** | `ACCOUNTADMIN` (for initial setup). The app itself runs as `OWNER`. |
| **Warehouse** | `COMPUTE_WH` (or change in `snowflake.yml`) |
| **Compute pool** | `SYSTEM_COMPUTE_POOL_CPU` (default SPCS pool) |
| **Cortex LLM access** | The account must have Snowflake Cortex AI functions enabled (uses `llama3.1-70b`) |
| **Free public data** | `SNOWFLAKE_PUBLIC_DATA_FREE` database (see Step 1 below) |

---

## Setup Guide

### Step 1 -- Get the Free Public Data

The app reads from `SNOWFLAKE_PUBLIC_DATA_FREE`, a free shared database provided by Snowflake.

1. Log in to [Snowsight](https://app.snowflake.com).
2. Go to **Data Products > Marketplace**.
3. Search for **"Snowflake Public Data Free"** (published by Snowflake).
4. Click **Get** and accept the terms. This creates the `SNOWFLAKE_PUBLIC_DATA_FREE` database in your account.

If the database already exists, skip this step.

### Step 2 -- Create the Application Database

Open a SQL worksheet in Snowsight and run:

```sql
-- sql/01_setup_database.sql

USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS HACKDAYS_APP_DB;
CREATE SCHEMA IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA;

CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.WATCHLIST (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    ENTITY_TYPE    VARCHAR(30)   NOT NULL,
    ENTITY_NAME    VARCHAR(500)  NOT NULL,
    TARGET_VALUE   FLOAT,
    NOTES          VARCHAR(2000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.CHAT_HISTORY (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    SESSION_ID     VARCHAR(100)  NOT NULL,
    ROLE           VARCHAR(20)   NOT NULL,
    CONTENT        VARCHAR(16000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.INSIGHTS_LOG (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    INSIGHT_TYPE   VARCHAR(50)   NOT NULL,
    INSIGHT_TEXT   VARCHAR(8000) NOT NULL,
    DATA_SNAPSHOT  VARIANT,
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

> **Note:** The app also auto-creates these tables on first launch via `ensure_watchlist_table()` in `utils/db.py`, but running the SQL manually ensures everything is clean before deployment.

### Step 3 -- Seed Sample Data (Optional)

Pre-populate the watchlist so the app isn't empty on first launch:

```sql
-- sql/02_seed_watchlist.sql

USE ROLE ACCOUNTADMIN;
USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

INSERT INTO WATCHLIST (ENTITY_TYPE, ENTITY_NAME, TARGET_VALUE, NOTES)
SELECT column1, column2, column3, column4
FROM VALUES
    ('State (Unemployment)', 'California',     4.50, 'Largest state economy'),
    ('State (Unemployment)', 'Texas',           3.80, 'Energy sector recovery indicator'),
    ('State (Unemployment)', 'New York',         4.00, 'Financial sector bellwether'),
    ('Company',              'APPLE INC',        NULL, 'Market cap leader'),
    ('Company',              'MICROSOFT CORP',   NULL, 'Enterprise tech demand signal'),
    ('Economic Indicator',   'CPI: All items',   3.00, 'Target: Fed 2% goal'),
    ('Economic Indicator',   'HPI Index',      500.00, 'Housing affordability threshold')
WHERE NOT EXISTS (SELECT 1 FROM WATCHLIST LIMIT 1);
```

### Step 4 -- Verify Data Access

Run the health-check script to confirm all public datasets are reachable and fresh:

```sql
-- sql/03_verify_public_data.sql

SHOW DATABASES LIKE 'SNOWFLAKE_PUBLIC_DATA_FREE';

SELECT 'EMPLOYMENT_TIMESERIES' AS SOURCE, COUNT(*) AS ROW_COUNT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES
UNION ALL
SELECT 'PRICE_TIMESERIES', COUNT(*)
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
UNION ALL
SELECT 'HOUSE_PRICE_TIMESERIES', COUNT(*)
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
UNION ALL
SELECT 'COMPANY_INDEX', COUNT(*)
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX
UNION ALL
SELECT 'GEOGRAPHY_INDEX', COUNT(*)
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX;
```

All five tables should return non-zero row counts. If any return an error, go back to Step 1 and ensure the Marketplace listing is installed.

### Step 5 -- Create Analytical Views

These views pre-aggregate data for the correlations page and macro summary:

```sql
-- sql/04_analytical_views.sql

USE ROLE ACCOUNTADMIN;
USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

-- Monthly national unemployment average
CREATE OR REPLACE VIEW V_MONTHLY_UNEMPLOYMENT AS
SELECT
    t.DATE,
    ROUND(AVG(t.VALUE * 100), 2)  AS AVG_UNEMPLOYMENT_RATE,
    COUNT(DISTINCT g.GEO_NAME)    AS STATES_REPORTING,
    ROUND(MAX(t.VALUE * 100), 2)  AS MAX_STATE_RATE,
    ROUND(MIN(t.VALUE * 100), 2)  AS MIN_STATE_RATE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX g
  ON t.GEO_ID = g.GEO_ID
WHERE g.LEVEL = 'State'
  AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
  AND t.VALUE IS NOT NULL
GROUP BY t.DATE;

-- Monthly CPI headline + categories
CREATE OR REPLACE VIEW V_MONTHLY_CPI AS
SELECT
    DATE,
    MAX(CASE WHEN VARIABLE = 'CPI:_All_items,_Seasonally_adjusted,_Monthly' THEN VALUE END) AS CPI_ALL_ITEMS,
    MAX(CASE WHEN VARIABLE = 'CPI:_Food,_Seasonally_adjusted,_Monthly'      THEN VALUE END) AS CPI_FOOD,
    MAX(CASE WHEN VARIABLE = 'CPI:_Energy,_Seasonally_adjusted,_Monthly'    THEN VALUE END) AS CPI_ENERGY,
    MAX(CASE WHEN VARIABLE = 'CPI:_Shelter,_Seasonally_adjusted,_Monthly'   THEN VALUE END) AS CPI_SHELTER
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
WHERE GEO_ID = 'country/USA'
  AND VALUE IS NOT NULL
GROUP BY DATE;

-- Monthly HPI
CREATE OR REPLACE VIEW V_MONTHLY_HPI AS
SELECT
    DATE,
    VALUE AS HPI_INDEX
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
WHERE GEO_ID = 'country/USA'
  AND VARIABLE = 'FHFA_HPI_traditional_purchase-only_monthly_SA'
  AND VALUE IS NOT NULL;

-- Cross-domain monthly macro summary
CREATE OR REPLACE VIEW V_MACRO_MONTHLY_SUMMARY AS
SELECT
    u.DATE,
    u.AVG_UNEMPLOYMENT_RATE,
    u.MAX_STATE_RATE   AS WORST_STATE_UNEMPLOYMENT,
    u.MIN_STATE_RATE   AS BEST_STATE_UNEMPLOYMENT,
    c.CPI_ALL_ITEMS,
    c.CPI_FOOD,
    c.CPI_ENERGY,
    c.CPI_SHELTER,
    h.HPI_INDEX,
    ROUND(((c.CPI_ALL_ITEMS - LAG(c.CPI_ALL_ITEMS, 12) OVER (ORDER BY u.DATE))
        / NULLIF(LAG(c.CPI_ALL_ITEMS, 12) OVER (ORDER BY u.DATE), 0)) * 100, 2)
        AS CPI_YOY_PCT,
    ROUND(((h.HPI_INDEX - LAG(h.HPI_INDEX, 12) OVER (ORDER BY u.DATE))
        / NULLIF(LAG(h.HPI_INDEX, 12) OVER (ORDER BY u.DATE), 0)) * 100, 2)
        AS HPI_YOY_PCT
FROM V_MONTHLY_UNEMPLOYMENT u
LEFT JOIN V_MONTHLY_CPI c ON u.DATE = c.DATE
LEFT JOIN V_MONTHLY_HPI h ON u.DATE = h.DATE
ORDER BY u.DATE;
```

### Step 6 -- Deploy the Streamlit App

**Option A: Deploy from Snowsight Workspaces (recommended)**

1. In Snowsight, go to **Projects > Workspaces**.
2. Open or create a workspace and upload the entire `HackDaysAhmedabad/` folder.
3. The `snowflake.yml` file auto-configures the deployment. Click **Run** in the Streamlit editor.

**Option B: Deploy with Snow CLI**

```bash
cd HackDaysAhmedabad/
snow streamlit deploy --replace
```

This reads `snowflake.yml` and deploys the app to `HACKDAYS_APP_DB.APP_DATA.HACKDAYSAHMEDABAD`.

**Option C: Manual upload**

1. Create a Streamlit app in Snowsight under `HACKDAYS_APP_DB.APP_DATA`.
2. Set warehouse to `COMPUTE_WH` and compute pool to `SYSTEM_COMPUTE_POOL_CPU`.
3. Upload all `.py` files preserving the directory structure (`app_pages/`, `utils/`).
4. Upload `pyproject.toml` and `.streamlit/config.toml`.

---

## Project Structure

```
HackDaysAhmedabad/
|-- streamlit_app.py          # Entry point: page config, sidebar, navigation
|-- snowflake.yml             # Snowflake deployment manifest
|-- pyproject.toml            # Python dependencies
|-- .streamlit/
|   +-- config.toml           # Streamlit theme config
|-- app_pages/
|   |-- home.py               # Overview dashboard with KPIs and AI narrative
|   |-- labor.py              # State-level unemployment analysis
|   |-- inflation.py          # CPI category breakdowns
|   |-- housing.py            # FHFA House Price Index
|   |-- companies.py          # Corporate entity browser
|   |-- correlations.py       # Cross-domain statistical analysis
|   |-- ai_advisor.py         # Cortex LLM chat interface
|   |-- sql_studio.py         # Ad-hoc SQL explorer
|   |-- ml_training.py        # ML model training & forecasting
|   +-- watchlist.py          # Personal watchlist CRUD
|-- utils/
|   +-- db.py                 # Data access layer: SQL queries, caching, Cortex
|-- sql/
|   |-- 01_setup_database.sql # Database, schema, and table DDL
|   |-- 02_seed_watchlist.sql # Sample watchlist data
|   |-- 03_verify_public_data.sql  # Data access health check
|   +-- 04_analytical_views.sql    # Pre-aggregated analytical views
+-- README.md
```

---

## Page Reference

### Home / Overview (`app_pages/home.py`)

Displays four KPI cards with month-over-month and year-over-year deltas. Computes trailing 12-month z-scores, percentile ranks, and 6-month linear trend slopes for unemployment, CPI, and HPI. Sends the statistical snapshot to Cortex `llama3.1-70b` to generate a plain-English narrative. Includes sparkline charts for each indicator.

### Labor & Employment (`app_pages/labor.py`)

Ranks all US states by unemployment rate (seasonally adjusted). Supports multi-state selection for comparative line charts over the selected timeframe.

### Inflation & CPI (`app_pages/inflation.py`)

Breaks down Consumer Price Index across 7 categories: All Items, Food, Energy, Shelter, Medical Care, Transportation, and Apparel. Shows YoY inflation rate charts.

### Housing Market (`app_pages/housing.py`)

Plots the FHFA House Price Index (purchase-only, seasonally adjusted) for the US. Displays key metrics and trajectory.

### Company Directory (`app_pages/companies.py`)

Searchable browser over 2M+ corporate entities sourced from SEC EDGAR, LEI, and OpenFIGI. Supports filtering by name and category. Includes CSV export.

### Cross-Domain Correlations (`app_pages/correlations.py`)

Dual-axis overlay of any two macro series. Computes Pearson correlation matrix across unemployment, CPI, and HPI. Performs lead-lag analysis from -12 to +12 months. YoY change overlay comparison.

### AI Economic Advisor (`app_pages/ai_advisor.py`)

Chat interface that injects a live data context snapshot (latest unemployment, CPI, HPI values) into the system prompt. Powered by Snowflake Cortex `COMPLETE()` with `llama3.1-70b`. Includes suggestion chips for common questions.

### SQL Studio (`app_pages/sql_studio.py`)

Sandboxed SQL explorer that only permits `SELECT` statements. Comes with 3 prebuilt query templates: macro summary, state comparison, and FEMA disaster impact.

### ML Training (`app_pages/ml_training.py`)

Train and evaluate machine learning models to forecast macroeconomic indicators. Reuses the shared `load_macro_history()` data loader from `utils/db.py` (monthly unemployment, CPI, and HPI data from 2010 onward). Features:

- **Target selection:** Unemployment Rate, CPI Index, or Home Price Index
- **Algorithm selection:** Linear Regression, Ridge Regression, Random Forest, or Gradient Boosting (scikit-learn)
- **Automatic feature engineering:** Configurable lag features (1-12 months), rolling mean/std, and month-of-year seasonality encoding (sin/cos)
- **Train/test split:** User-configurable test set percentage (10-40%)
- **Evaluation:** MAE, RMSE, and R-squared on the holdout set with actual vs predicted chart
- **Feature importance:** Bar chart for tree-based models (Random Forest, Gradient Boosting)
- **Future forecast:** Recursive N-month-ahead forecast (1-24 months) with historical context chart
- **AI interpretation:** Cortex LLM generates a plain-English summary of model quality and forecast direction

### My Watchlist (`app_pages/watchlist.py`)

Full CRUD interface for tracking states, companies, and economic indicators. Supports notes and target values. State entries are enriched with live unemployment data.

---

## Snowflake Objects Reference

### Databases

| Database | Access | Purpose |
|----------|--------|---------|
| `SNOWFLAKE_PUBLIC_DATA_FREE` | Read-only (shared) | Free public economic and corporate data |
| `HACKDAYS_APP_DB` | Read-write (app-owned) | Application tables, views, and Streamlit app |

### Public Data Tables (read-only)

| Fully Qualified Name | Domain |
|---------------------|--------|
| `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES` | State-level unemployment rates |
| `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES` | Consumer Price Index (CPI) |
| `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES` | FHFA House Price Index |
| `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX` | 2M+ corporate entities |
| `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX` | Geographic dimension table |
| `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_INDEX` | FEMA disaster declarations |

### App-Owned Tables

| Table | Purpose |
|-------|---------|
| `HACKDAYS_APP_DB.APP_DATA.WATCHLIST` | User-created tracked entities |
| `HACKDAYS_APP_DB.APP_DATA.CHAT_HISTORY` | AI chat session persistence |
| `HACKDAYS_APP_DB.APP_DATA.INSIGHTS_LOG` | Generated insights audit trail |

### Analytical Views

| View | Purpose |
|------|---------|
| `HACKDAYS_APP_DB.APP_DATA.V_MONTHLY_UNEMPLOYMENT` | National avg/min/max unemployment by month |
| `HACKDAYS_APP_DB.APP_DATA.V_MONTHLY_CPI` | Monthly CPI (headline + Food/Energy/Shelter) |
| `HACKDAYS_APP_DB.APP_DATA.V_MONTHLY_HPI` | Monthly house price index |
| `HACKDAYS_APP_DB.APP_DATA.V_MACRO_MONTHLY_SUMMARY` | Cross-domain join with YoY calculations |

### Snowflake Functions Used

| Function | Model | Used By |
|----------|-------|---------|
| `SNOWFLAKE.CORTEX.COMPLETE()` | `llama3.1-70b` | AI Advisor, Home page narrative |

---

## Configuration

### `snowflake.yml`

| Field | Value | Notes |
|-------|-------|-------|
| `database` | `HACKDAYS_APP_DB` | Change if using a different database |
| `schema` | `APP_DATA` | Must match SQL setup scripts |
| `query_warehouse` | `COMPUTE_WH` | Any warehouse with sufficient credits |
| `compute_pool` | `SYSTEM_COMPUTE_POOL_CPU` | Default SPCS compute pool |
| `run_mode` | `SpcsOnly` | Runs on Snowpark Container Services, not warehouse-based SiS |
| `execute_as` | `OWNER` | App runs with owner's privileges |

### Changing the Warehouse

Update both `snowflake.yml` and ensure the warehouse exists:

```yaml
# snowflake.yml
query_warehouse: YOUR_WAREHOUSE_NAME
```

### Changing the LLM Model

In `utils/db.py`, find the `cortex_complete()` function and change the model parameter:

```python
# Current: llama3.1-70b
# Options: llama3.1-8b, mistral-large2, etc.
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **`SNOWFLAKE_PUBLIC_DATA_FREE` not found** | Go to Marketplace and install the "Snowflake Public Data Free" listing. See [Step 1](#step-1----get-the-free-public-data). |
| **`HACKDAYS_APP_DB` does not exist** | Run `sql/01_setup_database.sql` with `ACCOUNTADMIN` role. |
| **Cortex COMPLETE() fails** | Ensure your account region supports Cortex AI functions and the `llama3.1-70b` model is available. Check [Snowflake Cortex region availability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability). |
| **Empty watchlist page** | Run `sql/02_seed_watchlist.sql` or add entries manually through the app. |
| **Stale data on charts** | Cached data refreshes every 60 minutes. Refresh the browser or wait for the cache TTL to expire. |
| **SQL Studio returns errors** | Only `SELECT` queries are allowed. `INSERT`, `UPDATE`, `DELETE`, and DDL are blocked. |
| **Compute pool errors** | Verify `SYSTEM_COMPUTE_POOL_CPU` exists: `SHOW COMPUTE POOLS;`. If using a custom pool, update `snowflake.yml`. |
| **Permission denied errors** | Ensure the deploying role has `CREATE STREAMLIT` on the schema and `USAGE` on the warehouse and compute pool. |
