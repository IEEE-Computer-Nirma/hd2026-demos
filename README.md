# Snowflake HackDays 2026 — Demos & Learning Hub

A monorepo containing production-grade Snowflake applications, interactive Streamlit dashboards, machine learning pipelines, and hands-on SQL/Python tutorials powered by **Snowflake Cortex AI**, **Snowpark Python**, and free public datasets.

---

## 🧭 Monorepo Projects Overview

```
hd2026-demos/
├── llm-chat-lab/                 # Cortex LLM Chat Assistant + FEMA Flood Insurance ML Model
├── retail-intelligence/          # Retail BI Dashboard, Inventory Monitor & AI Business Advisor
├── us_macroeconomics_dashboard/  # US Macroeconomic & Corporate Intelligence Observatory
└── public_free_data_access/      # Progressive SQL, Python & Jupyter tutorials on public datasets
```

| Project | Key Technologies | Description | Setup Time |
|---------|------------------|-------------|------------|
| [**LLM Chat Lab**](./llm-chat-lab/) | Snowflake Cortex (`llama3.1-70b`), Streamlit, Scikit-learn, Snowpark | Real-time multi-turn LLM chat interface + Random Forest classifier predicting flood damage causes on 2.7M+ FEMA claims. | ~2 mins |
| [**Retail Intelligence**](./retail-intelligence/) | Streamlit, Snowflake SQL Views, Cortex AI Advisor, Pandas | Full-stack retail business intelligence platform with revenue analytics, customer lifetime value, inventory health, and AI recommendations. | ~3 mins |
| [**US Macro Observatory**](./us_macroeconomics_dashboard/) | Streamlit (SPCS), Cortex AI, Scikit-learn, Plotly, Public Data | 11-page macroeconomic observatory with 50-state unemployment, 7-category CPI, FHFA housing indices, 2M+ SEC company directory, and ML forecasting. | ~5 mins |
| [**Public Free Data Access**](./public_free_data_access/) | SQL (Beginner to Advanced), Python (Pandas/Seaborn), Jupyter Notebooks | Structured hands-on labs and tutorials utilizing `SNOWFLAKE_PUBLIC_DATA_FREE` and `SNOWFLAKE_SAMPLE_DATA`. | Instant |

---

## 📋 Table of Contents

1. [Global Prerequisites](#global-prerequisites)
2. [Step-by-Step Global Snowflake Setup](#step-by-step-global-snowflake-setup)
   - [Step 1: Mount Free Public Data from Marketplace](#step-1-mount-free-public-data-from-marketplace)
   - [Step 2: Configure Snowflake Network Policy](#step-2-configure-snowflake-network-policy)
   - [Step 3: Setup Databases and Analytical Views](#step-3-setup-databases-and-analytical-views)
3. [Quick Start & Setup by Project](#quick-start--setup-by-project)
   - [1. LLM Chat Lab Setup](#1-llm-chat-lab-setup)
   - [2. Retail Intelligence Setup](#2-retail-intelligence-setup)
   - [3. US Macroeconomics Dashboard Setup](#3-us-macroeconomics-dashboard-setup)
   - [4. Public Free Data Tutorials Setup](#4-public-free-data-tutorials-setup)
4. [Deployment Environments](#deployment-environments)
   - [Snowflake Workspaces (Zero-Config)](#snowflake-workspaces-zero-config)
   - [Local Development Setup](#local-development-setup)
5. [Architecture & Tech Stack](#architecture--tech-stack)
6. [Global Troubleshooting Matrix](#global-troubleshooting-matrix)

---

## Global Prerequisites

Before starting, ensure you have:
- A **Snowflake Account** with `ACCOUNTADMIN` role access (Free Trial accounts at [signup.snowflake.com](https://signup.snowflake.com)).
- **Python 3.10, 3.11, or 3.12+** installed on your local machine (if developing locally).
- **Git** installed to clone the repository.
- A virtual warehouse named **`COMPUTE_WH`** in Snowflake.

---

## Step-by-Step Global Snowflake Setup

### Step 1: Mount Free Public Data from Marketplace

All projects in this repository utilize free public data provided by Snowflake.

1. Sign in to [Snowsight](https://app.snowflake.com).
2. Go to **Data Products** > **Marketplace**.
3. Search for **"Snowflake Public Data Free"** (published by Snowflake).
4. Click **Get** and ensure the database name is set to:
   ```
   SNOWFLAKE_PUBLIC_DATA_FREE
   ```
5. Click **Get** to mount the database into your account.

---

### Step 2: Configure Snowflake Network Policy

When connecting from local machines, IDEs, or using Personal Access Tokens (PAT), Snowflake requires an active Network Policy:

1. Open a new **SQL Worksheet** in Snowsight.
2. Set your role to **`ACCOUNTADMIN`**.
3. Run:

```sql
-- Create an open network policy for development
CREATE OR REPLACE NETWORK POLICY ALLOW_ALL_NP
  ALLOWED_IP_LIST = ('0.0.0.0/0');

-- Apply policy to the account
ALTER ACCOUNT SET NETWORK_POLICY = ALLOW_ALL_NP;
```

---

### Step 3: Setup Databases and Analytical Views

Execute the combined master initialization script in a Snowsight SQL Worksheet:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE_WH;

-- ============================================================
-- 1. Setup LLM Chat Lab Database & Schema
-- ============================================================
CREATE DATABASE IF NOT EXISTS LLM_CHAT_LAB_DB;
CREATE SCHEMA IF NOT EXISTS LLM_CHAT_LAB_DB.ML;

-- ============================================================
-- 2. Setup Retail Intelligence Database & Tables
-- ============================================================
CREATE DATABASE IF NOT EXISTS RETAIL_INTELLIGENCE_DB;
CREATE SCHEMA IF NOT EXISTS RETAIL_INTELLIGENCE_DB.RETAIL;

USE DATABASE RETAIL_INTELLIGENCE_DB;
USE SCHEMA RETAIL;

CREATE TABLE IF NOT EXISTS CUSTOMERS (
    CUSTOMER_ID     INT PRIMARY KEY,
    CUSTOMER_NAME   VARCHAR(100) NOT NULL,
    EMAIL           VARCHAR(150),
    COUNTRY         VARCHAR(50)  NOT NULL,
    CREATED_AT      DATE
);

CREATE TABLE IF NOT EXISTS PRODUCTS (
    PRODUCT_ID      INT PRIMARY KEY,
    PRODUCT_NAME    VARCHAR(150) NOT NULL,
    CATEGORY        VARCHAR(50)  NOT NULL,
    PRICE           DECIMAL(10, 2) NOT NULL,
    STOCK           INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ORDERS (
    ORDER_ID        INT PRIMARY KEY,
    CUSTOMER_ID     INT REFERENCES CUSTOMERS(CUSTOMER_ID),
    PRODUCT_ID      INT REFERENCES PRODUCTS(PRODUCT_ID),
    ORDER_DATE      DATE NOT NULL,
    QUANTITY        INT NOT NULL,
    TOTAL_AMOUNT    DECIMAL(10, 2) NOT NULL
);

-- Seed Retail Data
INSERT INTO CUSTOMERS (CUSTOMER_ID, CUSTOMER_NAME, EMAIL, COUNTRY, CREATED_AT) VALUES
(1,  'Aanya Sharma',    'aanya@example.com',    'India',          '2023-01-10'),
(2,  'James Carter',    'james@example.com',    'United States',  '2023-02-14'),
(3,  'Li Wei',          'liwei@example.com',    'China',          '2023-03-05'),
(4,  'Fatima Al-Said',  'fatima@example.com',   'UAE',            '2023-03-22'),
(5,  'Carlos Rivera',   'carlos@example.com',   'Brazil',         '2023-04-01');

INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY, PRICE, STOCK) VALUES
(1,  'UltraBook Pro 15',                     'Electronics',    1299.99,  45),
(2,  'Wireless Noise Cancelling Headphones', 'Electronics',     249.99, 180),
(3,  'Running Shoes X9',                     'Sports',           89.99, 320),
(4,  'Yoga Mat Premium',                     'Sports',           34.99,  80),
(5,  'Python Programming Guide',             'Books',            29.99, 500);

INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE, QUANTITY, TOTAL_AMOUNT) VALUES
(1001, 1, 1, '2024-01-05', 1, 1299.99),
(1002, 2, 2, '2024-01-08', 2,  499.98),
(1003, 3, 5, '2024-01-12', 3,   89.97),
(1004, 4, 1, '2024-01-15', 1, 1299.99),
(1005, 5, 3, '2024-01-20', 2,  179.98);

CREATE OR REPLACE VIEW RETAIL_SALES AS
SELECT o.ORDER_ID, o.ORDER_DATE, o.QUANTITY, o.TOTAL_AMOUNT,
       c.CUSTOMER_ID, c.CUSTOMER_NAME, c.COUNTRY,
       p.PRODUCT_ID, p.PRODUCT_NAME, p.CATEGORY, p.PRICE
FROM ORDERS o
JOIN CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
JOIN PRODUCTS p  ON o.PRODUCT_ID = p.PRODUCT_ID;

-- ============================================================
-- 3. Setup US Macroeconomics Dashboard Database & Views
-- ============================================================
CREATE DATABASE IF NOT EXISTS HACKDAYS_APP_DB;
CREATE SCHEMA IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA;

USE DATABASE HACKDAYS_APP_DB;
USE SCHEMA APP_DATA;

CREATE TABLE IF NOT EXISTS WATCHLIST (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    ENTITY_TYPE VARCHAR(30) NOT NULL,
    ENTITY_NAME VARCHAR(500) NOT NULL,
    TARGET_VALUE FLOAT,
    NOTES VARCHAR(2000),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS CHAT_HISTORY (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    SESSION_ID VARCHAR(100) NOT NULL,
    ROLE VARCHAR(20) NOT NULL,
    CONTENT VARCHAR(16000),
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS INSIGHTS_LOG (
    ID NUMBER AUTOINCREMENT PRIMARY KEY,
    INSIGHT_TYPE VARCHAR(50) NOT NULL,
    INSIGHT_TEXT VARCHAR(8000) NOT NULL,
    DATA_SNAPSHOT VARIANT,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

---

## Quick Start & Setup by Project

### 1. LLM Chat Lab Setup

* **Location**: `llm-chat-lab/`
* **Docs**: [llm-chat-lab/README.md](./llm-chat-lab/README.md)

#### Workspace Execution (1-Click)
1. In Snowsight, navigate to **Projects** > **Workspaces**.
2. Open `llm-chat-lab/streamlit_app.py` and click **Run**.
3. To train the ML model, open `llm-chat-lab/ml/train_flood_claim_model.py` and run it as a Python script.

#### Local Terminal Execution
```bash
cd llm-chat-lab
python3 -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt || pip install streamlit snowflake-connector-python snowflake-snowpark-python scikit-learn pandas

# Run Chat App
streamlit run streamlit_app.py

# Run ML Training Script
python ml/train_flood_claim_model.py
```

---

### 2. Retail Intelligence Setup

* **Location**: `retail-intelligence/`
* **Docs**: [retail-intelligence/README.md](./retail-intelligence/README.md)

#### Workspace Execution (1-Click)
1. In Snowsight, navigate to **Projects** > **Workspaces**.
2. Open `retail-intelligence/app.py` and click **Run**.

#### Local Terminal Execution
```bash
cd retail-intelligence
python3 -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create .env credentials file
cat <<EOF > .env
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=RETAIL_INTELLIGENCE_DB
SNOWFLAKE_SCHEMA=RETAIL
EOF

# Test connection & run
python test_connection.py
streamlit run app.py
```

---

### 3. US Macroeconomics Dashboard Setup

* **Location**: `us_macroeconomics_dashboard/`
* **Docs**: [us_macroeconomics_dashboard/README.md](./us_macroeconomics_dashboard/README.md)

#### Workspace Execution (1-Click)
1. In Snowsight, navigate to **Projects** > **Workspaces**.
2. Open `us_macroeconomics_dashboard/streamlit_app.py` and click **Run**.

#### Local Terminal Execution
```bash
cd us_macroeconomics_dashboard
python3 -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install streamlit snowflake-connector-python scikit-learn pandas numpy plotly altair

# Run app
streamlit run streamlit_app.py
```

---

### 4. Public Free Data Tutorials Setup

* **Location**: `public_free_data_access/`
* **Docs**: [public_free_data_access/README.md](./public_free_data_access/README.md)

#### Running SQL Tutorials
Open any script in `public_free_data_access/sql/` inside a Snowsight SQL Worksheet:
- `01_beginner_exploring_datasets.sql`
- `02_intermediate_single_dataset.sql`
- `03_advanced_cross_dataset.sql`
- `04_tpch_retail_training.sql`

#### Running Python Scripts & Notebooks
```bash
cd public_free_data_access
pip install pandas numpy matplotlib seaborn jupyterlab

# Run standalone analysis
python python/01_beginner_python.py
python python/02_intermediate_python.py
python python/03_advanced_python.py

# Launch interactive notebooks
jupyter lab notebooks/
```

---

## Deployment Environments

### Snowflake Workspaces (Zero-Config)
Snowflake Workspaces provides an embedded containerized runtime:
- **No credential management**: Authenticates via the active user session.
- **Pre-installed connectors**: `st.connection("snowflake")` and Snowpark `get_active_session()` connect automatically.
- **Compute options**: Backed by `COMPUTE_WH` and `SYSTEM_COMPUTE_POOL_CPU`.

### Local Development Setup
When developing locally:
1. Always isolate dependencies inside `.venv`.
2. Provide connection parameters via `.env` or `.streamlit/secrets.toml`.
3. Account Identifiers format: `<org>-<account>` or `<account_locator>` (e.g., `xy12345`).

---

## Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                     │
│  Streamlit • Plotly • Altair • Native Snowflake Notebooks   │
├─────────────────────────────────────────────────────────────┤
│                     AI & ANALYTICS LAYER                    │
│  Snowflake Cortex (Llama 3.1 70B, Claude 3.5 Sonnet)       │
│  Snowpark Python • Scikit-learn (RandomForest, Regression)  │
├─────────────────────────────────────────────────────────────┤
│                       DATA & STORAGE                        │
│  Snowflake Cloud DW • SNOWFLAKE_PUBLIC_DATA_FREE            │
│  Analytical Views • Dynamic SQL Caching (@st.cache_data)    │
└─────────────────────────────────────────────────────────────┘
```

---

## Global Troubleshooting Matrix

| Issue | Cause | Solution |
|-------|-------|----------|
| `Database 'SNOWFLAKE_PUBLIC_DATA_FREE' does not exist` | Public marketplace listing not mounted | Go to **Marketplace** > search `Snowflake Public Data Free` > click **Get**. |
| `Fail: Network policy is required (Error 390432)` | PAT or local IP blocked by account policy | Run `CREATE OR REPLACE NETWORK POLICY ALLOW_ALL_NP ALLOWED_IP_LIST = ('0.0.0.0/0'); ALTER ACCOUNT SET NETWORK_POLICY = ALLOW_ALL_NP;` using `ACCOUNTADMIN`. |
| `Database 'RETAIL_INTELLIGENCE_DB' does not exist` | Setup SQL not executed | Run `retail-intelligence/sql/setup.sql` in Snowsight. |
| `Database 'HACKDAYS_APP_DB' does not exist` | Setup SQL not executed | Run `us_macroeconomics_dashboard/sql/01_setup_database.sql` and `sql/04_analytical_views.sql`. |
| `Cortex LLM function execution failed` | Region does not support target model | Change `MODEL` parameter to `mistral-large2` or `llama3.1-8b` in app settings. |

---

## License

MIT License
