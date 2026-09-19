# US Macro Economic & Corporate Intelligence Observatory

A multi-page, enterprise-grade Streamlit-in-Snowflake analytics application that synthesizes US macroeconomic indicators (Bureau of Labor Statistics unemployment, CPI inflation categories, FHFA House Price Index) with a 2M+ corporate entity directory (SEC EDGAR / LEI / OpenFIGI), interactive ML forecasting, cross-domain statistical correlations, and personal watchlist tracking.

---

## 📋 Table of Contents

1. [System Architecture & Data Flow](#system-architecture--data-flow)
2. [Application Pages & Capabilities](#application-pages--capabilities)
3. [Prerequisites](#prerequisites)
4. [Complete Step-by-Step Setup Guide](#complete-step-by-step-setup-guide)
   - [Step 1: Acquire Free Public Data (Marketplace)](#step-1-acquire-free-public-data-marketplace)
   - [Step 2: Create Application Database & Tables (SQL)](#step-2-create-application-database--tables-sql)
   - [Step 3: Seed Sample Watchlist Data (SQL)](#step-3-seed-sample-watchlist-data-sql)
   - [Step 4: Verify Public Data Access (SQL)](#step-4-verify-public-data-access-sql)
   - [Step 5: Create Analytical Views (SQL)](#step-5-create-analytical-views-sql)
   - [Step 6: Deploy Application](#step-6-deploy-application)
5. [Machine Learning Forecasting Engine](#machine-learning-forecasting-engine)
6. [Snowflake Objects Reference](#snowflake-objects-reference)
7. [Configuration & Environment Variables](#configuration--environment-variables)
8. [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## System Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Streamlit Application (Snowpark / SPCS)                  │
│                              (streamlit_app.py)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Modular Views (app_pages/):                                                 │
│  ├── home.py               (Executive KPIs, z-scores, AI narrative)        │
│  ├── dashboard.py          (Multi-metric configurable chart canvas)         │
│  ├── labor.py              (50-state unemployment rankings & comparisons)   │
│  ├── inflation.py          (7-category CPI time series & YoY rates)         │
│  ├── housing.py            (FHFA purchase-only HPI trajectories)           │
│  ├── companies.py          (2M+ SEC EDGAR / LEI / OpenFIGI directory)       │
│  ├── correlations.py       (Pearson cross-correlation & lead-lag analysis)  │
│  ├── ai_advisor.py         (Grounded Cortex LLM chat advisor)               │
│  ├── sql_studio.py         (Sandboxed SELECT-only query environment)        │
│  ├── ml_training.py        (Scikit-learn recursive forecasting models)      │
│  └── watchlist.py          (Tracked entity CRUD manager)                    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │   Data Layer (utils/db.py)│
                         │    (@st.cache_data 1h TTL)│
                         └─────────────┬─────────────┘
                                       │
        ┌──────────────────────────────┴──────────────────────────────┐
        ▼                                                             ▼
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│ SNOWFLAKE_PUBLIC_DATA_FREE      │           │ HACKDAYS_APP_DB.APP_DATA        │
│ (Shared Read-Only Public Data)  │           │ (App-Owned Read-Write Database) │
├─────────────────────────────────┤           ├─────────────────────────────────┤
│ • BLS Employment Timeseries     │           │ • WATCHLIST                     │
│ • BLS Price Timeseries (CPI)    │           │ • CHAT_HISTORY                  │
│ • FHFA House Price Timeseries   │           │ • INSIGHTS_LOG                  │
│ • COMPANY_INDEX (2M+ entities)  │           │ • V_MONTHLY_UNEMPLOYMENT (View) │
│ • GEOGRAPHY_INDEX (Dim states)  │           │ • V_MONTHLY_CPI (View)          │
│ • FEMA Disaster Index           │           │ • V_MONTHLY_HPI (View)          │
└─────────────────────────────────┘           │ • V_MACRO_MONTHLY_SUMMARY (View)│
                                              └─────────────────────────────────┘
```

---

## Application Pages & Capabilities

| Page | File Path | Core Functionality |
|------|-----------|--------------------|
| **Executive Overview** | `app_pages/home.py` | Real-time KPI cards (Unemployment, CPI, HPI, Company Count), 12-month z-scores, percentile ranks, 6-month trend slope regressions, and an AI-generated economic briefing. |
| **Interactive Dashboard** | `app_pages/dashboard.py` | Configurable multi-series charting workbench allowing users to select indicators and date ranges. |
| **Labor & Employment** | `app_pages/labor.py` | 50-state unemployment league tables, multi-state comparative line charts, and historical recession comparisons. |
| **Inflation & CPI** | `app_pages/inflation.py` | Drilldown into 7 CPI categories (All Items, Food, Energy, Shelter, Medical, Transportation, Apparel) with YoY inflation percentages. |
| **Housing Market** | `app_pages/housing.py` | Federal Housing Finance Agency (FHFA) purchase-only home price index trends and real estate growth rates. |
| **Company Directory** | `app_pages/companies.py` | High-performance search and filter engine over 2M+ corporate entities with CIK, LEI, and OpenFIGI identifiers, including CSV export. |
| **Correlations & Lead-Lag** | `app_pages/correlations.py` | Dual-axis time series overlays, Pearson correlation matrices, and +/- 12 months cross-correlation lead-lag analysis. |
| **AI Economic Advisor** | `app_pages/ai_advisor.py` | Natural language chat grounded in current macroeconomic snapshots using Snowflake Cortex `llama3.1-70b`. |
| **SQL Studio** | `app_pages/sql_studio.py` | Safe, SELECT-only ad-hoc SQL sandbox with prebuilt query templates. |
| **ML Training & Forecast** | `app_pages/ml_training.py` | End-to-end macroeconomic indicator forecasting engine using Scikit-Learn (Linear, Ridge, Random Forest, Gradient Boosting) with recursive multi-step forecasting. |
| **My Watchlist** | `app_pages/watchlist.py` | Full Create, Read, Update, Delete (CRUD) persistence for monitoring target thresholds on states, stocks, and economic variables. |

---

## Prerequisites

- **Snowflake Account**: Free Trial or Standard Account with `ACCOUNTADMIN` role for initial setup.
- **`SNOWFLAKE_PUBLIC_DATA_FREE`**: Free database available in Snowflake Marketplace.
- **Compute Resources**: Virtual Warehouse (`COMPUTE_WH`) and Compute Pool (`SYSTEM_COMPUTE_POOL_CPU` for SPCS execution).
- **Cortex LLM**: Enabled in your account region (supports `llama3.1-70b`).

---

## Complete Step-by-Step Setup Guide

### Step 1: Acquire Free Public Data (Marketplace)

The application queries real-time public macroeconomic datasets provided free of charge by Snowflake.

1. Log in to [Snowsight](https://app.snowflake.com).
2. Navigate to **Data Products** > **Marketplace**.
3. Search for **"Snowflake Public Data Free"** (published by Snowflake).
4. Click **Get** and ensure the database name is set to `SNOWFLAKE_PUBLIC_DATA_FREE`.
5. Click **Get** to mount the database into your account.

---

### Step 2: Create Application Database & Tables (SQL)

Open a SQL Worksheet in Snowsight, set your role to `ACCOUNTADMIN`, and run:

```sql
-- sql/01_setup_database.sql

USE ROLE ACCOUNTADMIN;

-- 1. Create App Database and Schema
CREATE DATABASE IF NOT EXISTS HACKDAYS_APP_DB;
CREATE SCHEMA IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA;

USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

-- 2. Create Watchlist Table
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.WATCHLIST (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    ENTITY_TYPE    VARCHAR(30)   NOT NULL,
    ENTITY_NAME    VARCHAR(500)  NOT NULL,
    TARGET_VALUE   FLOAT,
    NOTES          VARCHAR(2000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 3. Create Chat Session History Table
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.CHAT_HISTORY (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    SESSION_ID     VARCHAR(100)  NOT NULL,
    ROLE           VARCHAR(20)   NOT NULL,
    CONTENT        VARCHAR(16000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- 4. Create Generated Insights Log Table
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.INSIGHTS_LOG (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    INSIGHT_TYPE   VARCHAR(50)   NOT NULL,
    INSIGHT_TEXT   VARCHAR(8000) NOT NULL,
    DATA_SNAPSHOT  VARIANT,
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

---

### Step 3: Seed Sample Watchlist Data (SQL)

Populate default tracked entities into the watchlist:

```sql
-- sql/02_seed_watchlist.sql

USE ROLE ACCOUNTADMIN;
USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

INSERT INTO WATCHLIST (ENTITY_TYPE, ENTITY_NAME, TARGET_VALUE, NOTES)
SELECT column1, column2, column3, column4
FROM VALUES
    ('State (Unemployment)', 'California',     4.50, 'Largest state economy'),
    ('State (Unemployment)', 'Texas',          3.80, 'Energy sector recovery indicator'),
    ('State (Unemployment)', 'New York',        4.00, 'Financial sector bellwether'),
    ('Company',              'APPLE INC',       NULL, 'Market cap leader'),
    ('Company',              'MICROSOFT CORP',  NULL, 'Enterprise tech demand signal'),
    ('Economic Indicator',   'CPI: All items',  3.00, 'Target: Fed 2% inflation goal'),
    ('Economic Indicator',   'HPI Index',     500.00, 'Housing affordability threshold')
WHERE NOT EXISTS (SELECT 1 FROM WATCHLIST LIMIT 1);
```

---

### Step 4: Verify Public Data Access (SQL)

Execute this health-check to confirm that all public tables are accessible and populated:

```sql
-- sql/03_verify_public_data.sql

USE ROLE ACCOUNTADMIN;

SHOW DATABASES LIKE 'SNOWFLAKE_PUBLIC_DATA_FREE';

SELECT 'EMPLOYMENT_TIMESERIES' AS DATASET, COUNT(*) AS ROW_COUNT
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

---

### Step 5: Create Analytical Views (SQL)

Create the pre-aggregated views used by the correlations and dashboard pages:

```sql
-- sql/04_analytical_views.sql

USE ROLE ACCOUNTADMIN;
USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

-- Monthly national unemployment summary
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

-- Monthly CPI metrics
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

-- Monthly House Price Index
CREATE OR REPLACE VIEW V_MONTHLY_HPI AS
SELECT
    DATE,
    VALUE AS HPI_INDEX
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
WHERE GEO_ID = 'country/USA'
  AND VARIABLE = 'FHFA_HPI_traditional_purchase-only_monthly_SA'
  AND VALUE IS NOT NULL;

-- Consolidated Cross-domain macro view
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

---

### Step 6: Deploy Application

#### Option A: Run in Snowflake Workspaces (Recommended)
1. Open **Snowsight** > **Projects** > **Workspaces**.
2. Navigate to `us_macroeconomics_dashboard/`.
3. Open `streamlit_app.py`.
4. Ensure warehouse `COMPUTE_WH` is selected.
5. Click **Run**.

#### Option B: Deploy using Snow CLI
```bash
cd us_macroeconomics_dashboard
snow streamlit deploy --replace
```

#### Option C: Run Locally via Streamlit
```bash
# 1. Setup Python Environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Dependencies
pip install --upgrade pip
pip install streamlit snowflake-connector-python scikit-learn pandas numpy plotly altair

# 3. Create .streamlit/secrets.toml
cat <<EOF > .streamlit/secrets.toml
[connections.snowflake]
account = "YOUR_ACCOUNT_IDENTIFIER"
user = "YOUR_USERNAME"
password = "YOUR_PASSWORD"
role = "ACCOUNTADMIN"
warehouse = "COMPUTE_WH"
database = "HACKDAYS_APP_DB"
schema = "APP_DATA"
EOF

# 4. Start Local Server
streamlit run streamlit_app.py
```

---

## Machine Learning Forecasting Engine

The **ML Training** page (`app_pages/ml_training.py`) implements an in-memory scikit-learn forecasting pipeline:

### Pipeline Specifications
- **Target Series**: Unemployment Rate (%), CPI Index, or Home Price Index (HPI).
- **Supported Models**:
  1. `LinearRegression` (Ordinary Least Squares)
  2. `RidgeRegression` (L2 Regularization)
  3. `RandomForestRegressor` (Ensemble bagging, 100 estimators)
  4. `GradientBoostingRegressor` (Ensemble boosting)
- **Engineered Features**:
  - Auto-generated lag values ($t-1, t-2, \dots, t-k$) configurable up to 12 months.
  - Rolling mean and rolling standard deviation over 3-month and 6-month windows.
  - Trigonometric seasonal encodings ($\sin(2\pi m/12), \cos(2\pi m/12)$).
- **Evaluation**: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and $R^2$ Score on holdout set.
- **Recursive Forecasting**: Generates forward-looking predictions (1 to 24 months into the future) with historical overlay and Cortex AI interpretation.

---

## Snowflake Objects Reference

| Object Name | Type | Access | Description |
|-------------|------|--------|-------------|
| `SNOWFLAKE_PUBLIC_DATA_FREE` | Database | Read-Only | Public Marketplace macro and corporate data |
| `HACKDAYS_APP_DB` | Database | Read-Write | Application container database |
| `HACKDAYS_APP_DB.APP_DATA` | Schema | Read-Write | Schema for tables, views, and Streamlit objects |
| `WATCHLIST` | Table | Read-Write | User-defined watchlist tracked entities |
| `CHAT_HISTORY` | Table | Read-Write | Session chat histories from AI Advisor |
| `INSIGHTS_LOG` | Table | Read-Write | Historical log of generated economic briefings |
| `V_MONTHLY_UNEMPLOYMENT` | View | Read-Only | State-averaged monthly unemployment view |
| `V_MONTHLY_CPI` | View | Read-Only | Pivot view of 4 primary CPI indicators |
| `V_MONTHLY_HPI` | View | Read-Only | Purchase-only FHFA House Price Index view |
| `V_MACRO_MONTHLY_SUMMARY` | View | Read-Only | Unified macro time series with YoY percentage rates |

---

## Configuration & Environment Variables

### `snowflake.yml` Manifest Reference
```yaml
definition_version: 2
entities:
  streamlit_app:
    type: streamlit
    main_file: streamlit_app.py
    artifacts:
      - pyproject.toml
      - streamlit_app.py
      - .streamlit/config.toml
      - utils/db.py
      - app_pages/home.py
      - app_pages/dashboard.py
      - app_pages/labor.py
      - app_pages/inflation.py
      - app_pages/housing.py
      - app_pages/companies.py
      - app_pages/watchlist.py
      - app_pages/sql_studio.py
      - app_pages/ai_advisor.py
      - app_pages/correlations.py
      - app_pages/ml_training.py
    identifier:
      database: HACKDAYS_APP_DB
      schema: APP_DATA
      name: HACKDAYSAHMEDABAD
    title: US Macro Economic Observatory
    query_warehouse: COMPUTE_WH
    compute_pool: SYSTEM_COMPUTE_POOL_CPU
    run_mode: SpcsOnly
    execute_as: OWNER
    artifact_repositories:
      - SNOWFLAKE.SNOWPARK.PYPI_SHARED_REPOSITORY
```

---

## Troubleshooting & FAQs

### 1. `Object SNOWFLAKE_PUBLIC_DATA_FREE does not exist`
* **Fix**: Ensure the Marketplace listing was mounted with the exact name `SNOWFLAKE_PUBLIC_DATA_FREE`. Follow [Step 1](#step-1-acquire-free-public-data-marketplace).

### 2. `Database HACKDAYS_APP_DB does not exist`
* **Fix**: Execute `sql/01_setup_database.sql` and `sql/04_analytical_views.sql` with the `ACCOUNTADMIN` role.

### 3. `Cortex COMPLETE() function failed or is not available`
* **Fix**: Verify your Snowflake account region supports Cortex LLMs. If needed, switch the model identifier in `utils/db.py` from `llama3.1-70b` to `llama3.1-8b` or `mistral-large2`.

---

## License

MIT License
