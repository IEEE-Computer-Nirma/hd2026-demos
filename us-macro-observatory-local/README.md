# US Macro Economic & Corporate Intelligence Observatory

A multi-page Streamlit application that combines US macroeconomic data (unemployment, CPI inflation, housing prices) with a 2M+ corporate entity directory, AI-powered analysis via Snowflake Cortex, and personal watchlist tracking.

**This is a localhost-ready package.** All Snowflake-in-Snowflake dependencies have been replaced with standard `snowflake-snowpark-python` connections that read credentials from a local secrets file.

---

## Quick Start (3 steps)

### 1. Run the setup script

**macOS / Linux:**
```bash
unzip us-macro-observatory-local.zip
cd us-macro-observatory-local
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell):**
```powershell
Expand-Archive us-macro-observatory-local.zip -DestinationPath .
cd us-macro-observatory-local
.\setup.bat
```

This creates a Python virtual environment, installs all dependencies, and generates a secrets file template.

### 2. Edit your Snowflake credentials

Open `.streamlit/secrets.toml` in any text editor and fill in your Snowflake account details:

```toml
[connections.snowflake]
account = "xy12345.us-east-1"     # Your account identifier
user = "my_user"                   # Your username
password = "my_password"           # Your password
role = "ACCOUNTADMIN"              # Role with access to public data
warehouse = "COMPUTE_WH"          # Any active warehouse
database = "SNOWFLAKE_PUBLIC_DATA_FREE"
schema = "PUBLIC_DATA_FREE"
```

**Finding your account identifier:**
- In Snowsight, click your name (bottom-left) > **Account** > copy the account URL
- The identifier is the part before `.snowflakecomputing.com`
- Examples: `xy12345.us-east-1`, `myorg-myaccount`, `abc12345.us-west-2.aws`

### 3. Run the app

**macOS / Linux:**
```bash
source venv/bin/activate
streamlit run streamlit_app.py
```

**Windows:**
```cmd
venv\Scripts\activate
streamlit run streamlit_app.py
```

The app opens at **http://localhost:8501**.

---

## Prerequisites

### Local Machine Requirements

| Requirement | Details | Install Link |
|---|---|---|
| **Python 3.9+** | Required. Python 3.11 recommended. | [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | Comes with Python. Used to install dependencies. | Included with Python |
| **Git** (optional) | Only if you want version control. | [git-scm.com](https://git-scm.com/) |

> **Windows users:** During Python installation, check **"Add Python to PATH"**. This is critical.

> **macOS users:** If you get `command not found: python3`, install via Homebrew: `brew install python3`

### Snowflake Account Requirements

| Requirement | Details |
|---|---|
| **Snowflake account** | Any edition (Standard, Enterprise, Business Critical). Trial accounts work. |
| **Role** | `ACCOUNTADMIN` for initial setup (Steps A-D below). After setup, a custom role with limited grants works fine. |
| **Warehouse** | Any active warehouse. The app defaults to `COMPUTE_WH`. |
| **Cortex LLM access** | Required **only** for the AI Advisor page and the Home page AI narrative. All other 7 pages work without it. See [Cortex Region Availability](#cortex-region-availability) below. |
| **Free public data** | `SNOWFLAKE_PUBLIC_DATA_FREE` database — free, installed from Marketplace (Step A below). |

---

## Snowflake Setup (do this BEFORE running the app)

Run these steps in a **Snowsight SQL worksheet** (or SnowSQL). You only need to do this once per account.

### Step A: Install the Free Public Data from Marketplace

The app reads from `SNOWFLAKE_PUBLIC_DATA_FREE`, a free shared database provided by Snowflake.

1. Log in to [Snowsight](https://app.snowflake.com)
2. Go to **Data Products > Marketplace**
3. Search for **"Snowflake Public Data Free"** (publisher: Snowflake)
4. Click **Get** and accept the terms

This creates the `SNOWFLAKE_PUBLIC_DATA_FREE` database in your account at no cost.

Then grant access to it:

```sql
USE ROLE ACCOUNTADMIN;

-- Make the shared public data accessible
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE ACCOUNTADMIN;
```

> **Trial accounts:** This listing is available on trial accounts. If you cannot find it, ensure your account region supports the Snowflake Marketplace.

### Step B: Create a Warehouse (skip if you already have one)

```sql
USE ROLE ACCOUNTADMIN;

-- Create a warehouse if COMPUTE_WH doesn't exist
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;
```

> If you want to use a different warehouse name, update it in `.streamlit/secrets.toml` later.

### Step C: Create the App Database and Tables

Copy and paste this into a Snowsight SQL worksheet and run it:

```sql
USE ROLE ACCOUNTADMIN;

-- Application database
CREATE DATABASE IF NOT EXISTS HACKDAYS_APP_DB;
CREATE SCHEMA IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA;

-- Watchlist: user-created tracked entities (full CRUD)
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.WATCHLIST (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    ENTITY_TYPE    VARCHAR(30)   NOT NULL,
    ENTITY_NAME    VARCHAR(500)  NOT NULL,
    TARGET_VALUE   FLOAT,
    NOTES          VARCHAR(2000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Chat history
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.CHAT_HISTORY (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    SESSION_ID     VARCHAR(100)  NOT NULL,
    ROLE           VARCHAR(20)   NOT NULL,
    CONTENT        VARCHAR(16000),
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insights log
CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.INSIGHTS_LOG (
    ID             NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
    INSIGHT_TYPE   VARCHAR(50)   NOT NULL,
    INSIGHT_TEXT   VARCHAR(8000) NOT NULL,
    DATA_SNAPSHOT  VARIANT,
    CREATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

> **Note:** The app also auto-creates these objects on first launch, but running this manually ensures a clean state and avoids first-run permission issues.

### Step D: Verify Everything Works

Run this to confirm all public datasets are accessible:

```sql
USE ROLE ACCOUNTADMIN;

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

**Expected:** All five sources return non-zero row counts. If any fail, go back to Step A.

### Step E (Optional): Seed Sample Watchlist Data

Pre-populate the watchlist so the app isn't empty on first launch:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

INSERT INTO WATCHLIST (ENTITY_TYPE, ENTITY_NAME, TARGET_VALUE, NOTES)
SELECT column1, column2, column3, column4
FROM VALUES
    ('State (Unemployment)', 'California',     4.50, 'Largest state economy — watch for tech layoff impact'),
    ('State (Unemployment)', 'Texas',           3.80, 'Energy sector recovery indicator'),
    ('State (Unemployment)', 'New York',         4.00, 'Financial sector bellwether'),
    ('Company',              'APPLE INC',        NULL, 'Market cap leader — consumer spending proxy'),
    ('Company',              'MICROSOFT CORP',   NULL, 'Enterprise tech demand signal'),
    ('Economic Indicator',   'CPI: All items',   3.00, 'Target: Fed 2% goal — currently above'),
    ('Economic Indicator',   'HPI Index',      500.00, 'Tracking housing affordability threshold')
WHERE NOT EXISTS (SELECT 1 FROM WATCHLIST LIMIT 1);
```

### Step F (Optional): Create Analytical Views

These pre-aggregated views are used by the correlations page. The app works without them, but they improve performance:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

CREATE OR REPLACE VIEW V_MONTHLY_UNEMPLOYMENT AS
SELECT
    t.DATE,
    ROUND(AVG(t.VALUE * 100), 2) AS AVG_UNEMPLOYMENT_RATE,
    COUNT(DISTINCT g.GEO_NAME) AS STATES_REPORTING,
    ROUND(MAX(t.VALUE * 100), 2) AS MAX_STATE_RATE,
    ROUND(MIN(t.VALUE * 100), 2) AS MIN_STATE_RATE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX g ON t.GEO_ID = g.GEO_ID
WHERE g.LEVEL = 'State'
  AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
  AND t.VALUE IS NOT NULL
GROUP BY t.DATE;

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

CREATE OR REPLACE VIEW V_MONTHLY_HPI AS
SELECT DATE, VALUE AS HPI_INDEX
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
WHERE GEO_ID = 'country/USA'
  AND VARIABLE = 'FHFA_HPI_traditional_purchase-only_monthly_SA'
  AND VALUE IS NOT NULL;

CREATE OR REPLACE VIEW V_MACRO_MONTHLY_SUMMARY AS
SELECT
    u.DATE,
    u.AVG_UNEMPLOYMENT_RATE,
    u.MAX_STATE_RATE   AS WORST_STATE_UNEMPLOYMENT,
    u.MIN_STATE_RATE   AS BEST_STATE_UNEMPLOYMENT,
    c.CPI_ALL_ITEMS, c.CPI_FOOD, c.CPI_ENERGY, c.CPI_SHELTER,
    h.HPI_INDEX,
    ROUND(((c.CPI_ALL_ITEMS - LAG(c.CPI_ALL_ITEMS, 12) OVER (ORDER BY u.DATE))
        / NULLIF(LAG(c.CPI_ALL_ITEMS, 12) OVER (ORDER BY u.DATE), 0)) * 100, 2) AS CPI_YOY_PCT,
    ROUND(((h.HPI_INDEX - LAG(h.HPI_INDEX, 12) OVER (ORDER BY u.DATE))
        / NULLIF(LAG(h.HPI_INDEX, 12) OVER (ORDER BY u.DATE), 0)) * 100, 2) AS HPI_YOY_PCT
FROM V_MONTHLY_UNEMPLOYMENT u
LEFT JOIN V_MONTHLY_CPI c ON u.DATE = c.DATE
LEFT JOIN V_MONTHLY_HPI h ON u.DATE = h.DATE
ORDER BY u.DATE;
```

---

## Using a Custom Role (Instead of ACCOUNTADMIN)

If you don't want to connect as `ACCOUNTADMIN`, create a dedicated role with the minimum grants needed:

```sql
USE ROLE ACCOUNTADMIN;

-- Create the app role
CREATE ROLE IF NOT EXISTS MACRO_OBSERVATORY_ROLE;

-- Warehouse access
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE MACRO_OBSERVATORY_ROLE;

-- Public data (read-only)
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE MACRO_OBSERVATORY_ROLE;

-- App database (read-write for watchlist CRUD)
GRANT USAGE ON DATABASE HACKDAYS_APP_DB TO ROLE MACRO_OBSERVATORY_ROLE;
GRANT USAGE ON SCHEMA HACKDAYS_APP_DB.APP_DATA TO ROLE MACRO_OBSERVATORY_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA HACKDAYS_APP_DB.APP_DATA TO ROLE MACRO_OBSERVATORY_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA HACKDAYS_APP_DB.APP_DATA TO ROLE MACRO_OBSERVATORY_ROLE;

-- Allow creating tables (for auto-setup on first launch)
GRANT CREATE TABLE ON SCHEMA HACKDAYS_APP_DB.APP_DATA TO ROLE MACRO_OBSERVATORY_ROLE;

-- Cortex AI functions (for AI Advisor and Home narrative)
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE MACRO_OBSERVATORY_ROLE;

-- Assign to a user
GRANT ROLE MACRO_OBSERVATORY_ROLE TO USER my_username;
```

Then in `.streamlit/secrets.toml`, set `role = "MACRO_OBSERVATORY_ROLE"`.

---

## Authentication Options

The app supports multiple Snowflake authentication methods via `.streamlit/secrets.toml`.

### Password (default, simplest)
```toml
[connections.snowflake]
account = "xy12345.us-east-1"
user = "my_user"
password = "my_password"
role = "ACCOUNTADMIN"
warehouse = "COMPUTE_WH"
database = "SNOWFLAKE_PUBLIC_DATA_FREE"
schema = "PUBLIC_DATA_FREE"
```

### Key-pair authentication (recommended for non-interactive / shared setups)
```toml
[connections.snowflake]
account = "xy12345.us-east-1"
user = "my_user"
private_key_file = "/path/to/rsa_key.p8"
private_key_file_pwd = "passphrase_if_encrypted"
role = "ACCOUNTADMIN"
warehouse = "COMPUTE_WH"
database = "SNOWFLAKE_PUBLIC_DATA_FREE"
schema = "PUBLIC_DATA_FREE"
```

To generate a key pair:
```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```
Then register the public key in Snowflake:
```sql
ALTER USER my_user SET RSA_PUBLIC_KEY='<paste contents of rsa_key.pub without header/footer>';
```

### SSO / externalbrowser (opens browser for login)
```toml
[connections.snowflake]
account = "xy12345.us-east-1"
user = "my_user"
authenticator = "externalbrowser"
role = "ACCOUNTADMIN"
warehouse = "COMPUTE_WH"
database = "SNOWFLAKE_PUBLIC_DATA_FREE"
schema = "PUBLIC_DATA_FREE"
```

---

## Cortex Region Availability

The **AI Economic Advisor** and **Home page AI narrative** use `SNOWFLAKE.CORTEX.COMPLETE()` with the `llama3.1-70b` model. This requires:

1. Your Snowflake account must be in a **Cortex-supported region** (most AWS US, AWS EU, and Azure regions are supported)
2. The `llama3.1-70b` model must be available in your region

**If Cortex is not available in your region:**
- The AI Advisor page will show an error message
- The Home page narrative section will show "Narrative unavailable"
- **All other 7 pages work perfectly without Cortex**

To check if Cortex is available, run in Snowsight:
```sql
SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', 'Say hello') AS TEST;
```
If this returns a response, you're good. If it errors, Cortex is not available in your region.

**To change the model** (if `llama3.1-70b` is unavailable but others are), edit `utils/db.py` line 22:
```python
def cortex_complete(prompt: str, model: str = "llama3.1-70b") -> str:
#                                              ^^^^^^^^^^^^^^
# Change to: "mistral-large2", "llama3.1-8b", "claude-3-5-sonnet", etc.
```

---

## Features

| Page | Description |
|---|---|
| **Home / Overview** | KPI cards (unemployment, CPI, HPI, company count) with MoM/YoY deltas, z-scores, percentile ranks, trend slopes, and an AI-generated narrative summary |
| **Labor & Employment** | State-level unemployment rankings and multi-state comparative line charts |
| **Inflation & CPI** | CPI breakdown across 7 categories with YoY inflation rate charts |
| **Housing Market** | FHFA House Price Index trajectory and key metrics |
| **Company Directory** | Searchable/filterable browser over 2M+ SEC EDGAR / LEI / OpenFIGI entities with CSV export |
| **Cross-Domain Correlations** | Dual-axis comparison, Pearson correlation matrix, lead-lag analysis, and YoY change overlays |
| **AI Economic Advisor** | Chat interface powered by Snowflake Cortex LLM with live data context injection |
| **SQL Studio** | Ad-hoc SELECT-only SQL explorer with prebuilt query templates |
| **My Watchlist** | Full CRUD to track states, companies, and indicators with notes and target values |

---

## Project Structure

```
us-macro-observatory-local/
|-- streamlit_app.py              # Entry point: page config, sidebar, navigation
|-- requirements.txt              # Python dependencies
|-- setup.sh                      # macOS/Linux setup script
|-- setup.bat                     # Windows setup script
|-- .gitignore                    # Excludes secrets.toml, venv, __pycache__
|-- .streamlit/
|   |-- config.toml               # Streamlit configuration
|   +-- secrets.toml.example      # Credentials template (copy to secrets.toml)
|-- app_pages/
|   |-- home.py                   # Overview dashboard with KPIs and AI narrative
|   |-- labor.py                  # State-level unemployment analysis
|   |-- inflation.py              # CPI category breakdowns
|   |-- housing.py                # FHFA House Price Index
|   |-- companies.py              # Corporate entity browser
|   |-- correlations.py           # Cross-domain statistical analysis
|   |-- ai_advisor.py             # Cortex LLM chat interface
|   |-- sql_studio.py             # Ad-hoc SQL explorer
|   +-- watchlist.py              # Personal watchlist CRUD
|-- utils/
|   +-- db.py                     # Data access layer: SQL queries, caching, Cortex
|-- sql/
|   |-- 01_setup_database.sql     # Database, schema, and table DDL
|   |-- 02_seed_watchlist.sql     # Sample watchlist data
|   |-- 03_verify_public_data.sql # Data access health check
|   +-- 04_analytical_views.sql   # Pre-aggregated analytical views
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| **`python3: command not found`** | Install Python 3.9+ from [python.org/downloads](https://www.python.org/downloads/). On macOS: `brew install python3`. On Windows: ensure "Add to PATH" was checked during install. |
| **`pip: command not found`** | Use `python3 -m pip install -r requirements.txt` instead. |
| **`ModuleNotFoundError: snowflake.snowpark`** | Activate your venv first: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows), then `pip install -r requirements.txt` |
| **`SNOWFLAKE_PUBLIC_DATA_FREE` not found** | Install the free listing from Snowflake Marketplace (see Step A above). Then run `GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_PUBLIC_DATA_FREE TO ROLE <your_role>;` |
| **`Connection refused` / `account not found`** | Double-check `account` in `.streamlit/secrets.toml`. Format: `orgname-accountname` or `accountlocator.region.cloud` (e.g. `xy12345.us-east-1` or `myorg-myaccount`) |
| **`Incorrect username or password`** | Verify user/password in secrets.toml. If using MFA, try `authenticator = "externalbrowser"` instead. |
| **`Insufficient privileges`** | Ensure your role has the required grants (see "Using a Custom Role" section). Easiest: use `ACCOUNTADMIN`. |
| **`HACKDAYS_APP_DB does not exist`** | Run Step C above, or use `ACCOUNTADMIN` role (the app auto-creates it on first launch if the role has `CREATE DATABASE` privilege). |
| **Cortex `COMPLETE()` fails** | Your account region may not support Cortex AI. Run the test query in the Cortex section above. The AI Advisor and Home narrative will fail, but all other pages work fine. |
| **`secrets.toml` not found** | Copy the example: `cp .streamlit/secrets.toml.example .streamlit/secrets.toml` and fill in your credentials. |
| **SSL errors on macOS** | Run: `pip install certifi` then `export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")` |
| **Stale data on charts** | Cached data refreshes every 60 minutes. Hard-refresh your browser (`Ctrl+Shift+R`) or restart the app with `Ctrl+C` then `streamlit run streamlit_app.py`. |
| **`Warehouse 'COMPUTE_WH' does not exist`** | Either create it (Step B) or change the warehouse name in `.streamlit/secrets.toml`. |

---

## Security Notes

- **Never commit `.streamlit/secrets.toml`** to version control. It is listed in `.gitignore`.
- The `secrets.toml.example` file contains placeholder values only.
- For shared or production setups, prefer key-pair or SSO authentication over password auth.
- The SQL Studio page only permits `SELECT` statements — DDL and DML are blocked.
- Use the custom role setup (above) to follow least-privilege principles.

---

## Differences from the Snowsight (SPCS) Version

| Aspect | Snowsight Version | Local Version |
|---|---|---|
| Connection | `st.connection("snowflake")` via SPCS runtime | `st.connection("snowflake")` via `.streamlit/secrets.toml` |
| Authentication | Automatic (session token) | Password, key-pair, or SSO (configured in secrets.toml) |
| Compute | Snowpark Container Services (SPCS) | Your local machine |
| Dependencies | `streamlit[snowflake]` (pre-installed) | `requirements.txt` (pip install) |
| Config files | `snowflake.yml` + `pyproject.toml` | `.streamlit/secrets.toml` |
| First-run setup | Automatic (SPCS handles infra) | Manual Snowflake setup (Steps A-D above) |
