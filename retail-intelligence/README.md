# Retail Intelligence — Snowflake BI & Cortex AI Analytics Platform

A complete, production-grade retail analytics platform featuring interactive business intelligence dashboards, real-time KPI monitoring, inventory health alerting, and an AI-powered Business Advisor using Snowflake Cortex LLMs.

Supports dual deployment:
- **Snowflake Workspaces**: 1-click zero-config deployment using native session identity (`st.connection("snowflake")`).
- **Local Development**: Standard local Python runtime via `streamlit run` and `.env` credentials.

---

## 📋 Table of Contents

1. [Application Architecture](#application-architecture)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Step 1: Snowflake Database & View Setup (SQL)](#step-1-snowflake-database--view-setup-sql)
5. [Step 2: Deployment Guides](#step-2-deployment-guides)
   - [Option A: Deploy in Snowflake Workspaces (Recommended)](#option-a-deploy-in-snowflake-workspaces-recommended)
   - [Option B: Run Locally with Python & Streamlit](#option-b-run-locally-with-python--streamlit)
6. [Feature & Page Reference](#feature--page-reference)
7. [Snowflake Cortex AI Advisor](#snowflake-cortex-ai-advisor)
8. [Snowflake Objects Reference](#snowflake-objects-reference)
9. [Troubleshooting & Common Fixes](#troubleshooting--common-fixes)

---

## Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Application                    │
│                           (app.py)                          │
├──────────────────────────────┬──────────────────────────────┤
│ App Pages (app_pages/):      │ Shared Utilities:            │
│  ├── overview.py             │  ├── utils/queries.py        │
│  ├── sales_analytics.py      │  │   (@st.cache_data)        │
│  ├── customer_insights.py    │  └── snowflake_connection.py │
│  ├── inventory.py            │                              │
│  └── ai_advisor.py           │                              │
└───────────────┬──────────────┴───────────────┬──────────────┘
                │                              │
     (Workspace Runtime)               (Local Development)
     st.connection("snowflake")        snowflake.connector + .env
                │                              │
                └──────────────┬───────────────┘
                               │
            ┌──────────────────▼──────────────────┐
            │       Snowflake Cloud Data          │
            │ RETAIL_INTELLIGENCE_DB.RETAIL       │
            ├─────────────────────────────────────┤
            │  ├── CUSTOMERS                      │
            │  ├── PRODUCTS                       │
            │  ├── ORDERS                         │
            │  └── RETAIL_SALES (Joined View)     │
            └──────────────────┬──────────────────┘
                               │
            ┌──────────────────▼──────────────────┐
            │        Snowflake Cortex AI          │
            │     SNOWFLAKE.CORTEX.COMPLETE()     │
            │           (llama3.1-70b)            │
            └─────────────────────────────────────┘
```

---

## Project Structure

```
retail-intelligence/
├── app.py                        # Application entry point & page navigation router
├── snowflake_connection.py       # Dual-runtime Snowflake connection factory
├── test_connection.py            # Local connection verification script
├── snowflake.yml                 # Snowflake Workspace deployment manifest
├── pyproject.toml                # Workspace container package dependencies
├── requirements.txt              # Local pip dependencies
├── .env.example                  # Environment variable configuration template
├── .gitignore
├── .streamlit/
│   └── config.toml               # Streamlit theme styling (dark theme, custom fonts)
├── app_pages/                    # Modular page views
│   ├── overview.py               # Executive summary, KPI cards, trend charts
│   ├── sales_analytics.py        # Revenue breakdowns by category, country & time
│   ├── customer_insights.py      # Customer lifetime value & segment analysis
│   ├── inventory.py              # Product inventory levels & low-stock alerts
│   └── ai_advisor.py             # Snowflake Cortex AI chat grounded in live data
├── utils/
│   ├── __init__.py
│   └── queries.py                # Cached SQL query execution helpers
└── sql/
    └── setup.sql                 # Complete database, tables, sample data & view DDL
```

---

## Prerequisites

- **Snowflake Account**: Any standard edition or Free Trial account with `ACCOUNTADMIN` or `SYSADMIN` role.
- **Compute Warehouse**: `COMPUTE_WH` (or any available virtual warehouse).
- **Python 3.10+** (if developing locally).

---

## Step 1: Snowflake Database & View Setup (SQL)

Run the following SQL script in a Snowsight SQL Worksheet to create the database, tables, seed data, and analytical views:

```sql
-- ============================================================
-- Retail Intelligence — Complete Database Setup
-- ============================================================

USE ROLE ACCOUNTADMIN;

-- 1. Create Database & Schema
CREATE DATABASE IF NOT EXISTS RETAIL_INTELLIGENCE_DB;
USE DATABASE RETAIL_INTELLIGENCE_DB;

CREATE SCHEMA IF NOT EXISTS RETAIL;
USE SCHEMA RETAIL;

-- 2. Create Base Tables
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

-- 3. Insert Seed Data
INSERT INTO CUSTOMERS (CUSTOMER_ID, CUSTOMER_NAME, EMAIL, COUNTRY, CREATED_AT) VALUES
(1,  'Aanya Sharma',    'aanya@example.com',    'India',          '2023-01-10'),
(2,  'James Carter',    'james@example.com',    'United States',  '2023-02-14'),
(3,  'Li Wei',          'liwei@example.com',    'China',          '2023-03-05'),
(4,  'Fatima Al-Said',  'fatima@example.com',   'UAE',            '2023-03-22'),
(5,  'Carlos Rivera',   'carlos@example.com',   'Brazil',         '2023-04-01'),
(6,  'Sophie Martin',   'sophie@example.com',   'France',         '2023-04-18'),
(7,  'Kenji Tanaka',    'kenji@example.com',    'Japan',          '2023-05-09'),
(8,  'Priya Nair',      'priya@example.com',    'India',          '2023-05-20'),
(9,  'Ahmed Hassan',    'ahmed@example.com',    'Egypt',          '2023-06-03'),
(10, 'Emma Wilson',     'emma@example.com',     'United Kingdom', '2023-06-15');

INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY, PRICE, STOCK) VALUES
(1,  'UltraBook Pro 15',                     'Electronics',    1299.99,  45),
(2,  'Wireless Noise Cancelling Headphones', 'Electronics',     249.99, 180),
(3,  'Running Shoes X9',                     'Sports',           89.99, 320),
(4,  'Yoga Mat Premium',                     'Sports',           34.99,  80),
(5,  'Python Programming Guide',             'Books',            29.99, 500),
(6,  'Data Science Handbook',                'Books',            39.99, 310),
(7,  'Smart Watch Series 5',                 'Electronics',     399.99,  60),
(8,  'Resistance Bands Set',                 'Sports',           19.99,  95),
(9,  'Business Strategy 101',                'Books',            24.99, 420),
(10, '4K Gaming Monitor 27"',                'Electronics',     699.99,  30),
(11, 'Cotton T-Shirt Pack',                  'Apparel',          24.99, 600),
(12, 'Denim Jacket Classic',                 'Apparel',          79.99, 140),
(13, 'Ceramic Coffee Mug Set',               'Home & Kitchen',   19.99, 250),
(14, 'Non-Stick Cookware Set',               'Home & Kitchen',   89.99,  70),
(15, 'Standing Desk Adjustable',             'Home & Kitchen',  349.99,  25);

INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, PRODUCT_ID, ORDER_DATE, QUANTITY, TOTAL_AMOUNT) VALUES
(1001, 1,  1,  '2024-01-05', 1, 1299.99),
(1002, 2,  2,  '2024-01-08', 2,  499.98),
(1003, 3,  5,  '2024-01-12', 3,   89.97),
(1004, 4,  7,  '2024-01-15', 1,  399.99),
(1005, 5,  3,  '2024-01-20', 2,  179.98),
(1006, 6,  6,  '2024-01-22', 1,   39.99),
(1007, 7, 10,  '2024-01-28', 1,  699.99),
(1008, 8,  4,  '2024-02-01', 2,   69.98),
(1009, 9,  9,  '2024-02-05', 1,   24.99),
(1010, 10, 11, '2024-02-10', 3,   74.97),
(1011, 1,  2,  '2024-02-14', 1,  249.99),
(1012, 2,  8,  '2024-02-18', 4,   79.96),
(1013, 3, 12,  '2024-02-22', 1,   79.99),
(1014, 4, 13,  '2024-02-25', 2,   39.98),
(1015, 5,  1,  '2024-03-01', 1, 1299.99),
(1016, 6, 14,  '2024-03-04', 1,   89.99),
(1017, 7,  5,  '2024-03-08', 5,  149.95),
(1018, 8,  7,  '2024-03-12', 1,  399.99),
(1019, 9, 15,  '2024-03-15', 1,  349.99),
(1020, 10, 3,  '2024-03-20', 2,  179.98),
(1021, 1,  6,  '2024-03-25', 2,   79.98),
(1022, 2, 10,  '2024-03-28', 1,  699.99),
(1023, 3,  4,  '2024-04-02', 3,  104.97),
(1024, 4, 11,  '2024-04-05', 4,   99.96),
(1025, 5,  9,  '2024-04-10', 2,   49.98),
(1026, 6,  2,  '2024-04-14', 1,  249.99),
(1027, 7, 13,  '2024-04-18', 3,   59.97),
(1028, 8,  1,  '2024-04-22', 1, 1299.99),
(1029, 9, 12,  '2024-04-26', 2,  159.98),
(1030, 10, 7,  '2024-04-30', 1,  399.99);

-- 4. Create Analytical Joined View
CREATE OR REPLACE VIEW RETAIL_SALES AS
SELECT
    o.ORDER_ID,
    o.ORDER_DATE,
    o.QUANTITY,
    o.TOTAL_AMOUNT,
    c.CUSTOMER_ID,
    c.CUSTOMER_NAME,
    c.COUNTRY,
    p.PRODUCT_ID,
    p.PRODUCT_NAME,
    p.CATEGORY,
    p.PRICE
FROM ORDERS o
JOIN CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
JOIN PRODUCTS p  ON o.PRODUCT_ID = p.PRODUCT_ID;

-- 5. Verification
SELECT 'CUSTOMERS' AS TBL, COUNT(*) AS ROWS FROM CUSTOMERS
UNION ALL
SELECT 'PRODUCTS', COUNT(*) FROM PRODUCTS
UNION ALL
SELECT 'ORDERS', COUNT(*) FROM ORDERS
UNION ALL
SELECT 'RETAIL_SALES (VIEW)', COUNT(*) FROM RETAIL_SALES;
```

---

## Step 2: Deployment Guides

### Option A: Deploy in Snowflake Workspaces (Recommended)

Snowflake Workspaces provides an embedded, zero-configuration runtime.

1. In **Snowsight**, open **Projects** > **Workspaces**.
2. Navigate to `retail-intelligence/` folder.
3. Open `app.py`.
4. Ensure your role is `ACCOUNTADMIN` and warehouse is `COMPUTE_WH`.
5. Click **Run** in the top right.
6. The app renders instantly with all pages and Cortex AI features ready.

---

### Option B: Run Locally with Python & Streamlit

#### 1. Clone & Navigate to Project Directory
```bash
git clone https://github.com/IEEE-Computer-Nirma/hd2026-demos.git
cd hd2026-demos/retail-intelligence
```

#### 2. Create & Activate Virtual Environment

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Local Credentials (`.env`)
Create a `.env` file inside `retail-intelligence/`:

```env
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=ACCOUNTADMIN
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=RETAIL_INTELLIGENCE_DB
SNOWFLAKE_SCHEMA=RETAIL
```

#### 5. Verify Database Connection
Run the connection diagnostics test script:
```bash
python test_connection.py
```
*Expected output: `Connection successful! Fetched X rows from RETAIL_SALES.`*

#### 6. Launch the Streamlit App
```bash
streamlit run app.py
```
Open your web browser at `http://localhost:8501`.

---

## Feature & Page Reference

| Page | File Path | Capabilities |
|------|-----------|--------------|
| **Executive Overview** | `app_pages/overview.py` | Top-level revenue KPIs, daily sales trend charts, category contribution breakdown, and quick business metrics. |
| **Sales Analytics** | `app_pages/sales_analytics.py` | Multi-select country & category filtering, revenue vs. quantity trends, and drill-down order logs. |
| **Customer Insights** | `app_pages/customer_insights.py` | Top 10 customer rankings by total spend, average order value (AOV), and customer geographic distribution. |
| **Inventory Health** | `app_pages/inventory.py` | Real-time stock level monitoring, low-stock threshold alerts, and catalogue valuation. |
| **Cortex AI Advisor** | `app_pages/ai_advisor.py` | Natural language chat assistant with live retail database context injection for deep reasoning. |

---

## Snowflake Cortex AI Advisor

The **AI Advisor** (`app_pages/ai_advisor.py`) combines the power of **Snowflake Cortex** (`SNOWFLAKE.CORTEX.COMPLETE`) using the `llama3.1-70b` model.

When a question is submitted, the application:
1. Dynamically generates an aggregated data payload of top products, low inventory items, category totals, and top customers.
2. Injects this business context into a system prompt.
3. Streams the response back with actionable retail recommendations.

**Sample queries to try:**
- *"Which product category generates the highest revenue?"*
- *"Identify items at risk of stockout and recommend restock priorities."*
- *"Who are our top 3 most valuable customers and what did they buy?"*
- *"Analyze our sales in India compared to the United States."*

---

## Snowflake Objects Reference

| Object Name | Type | Purpose |
|-------------|------|---------|
| `RETAIL_INTELLIGENCE_DB` | Database | Root database container |
| `RETAIL` | Schema | Application schema |
| `CUSTOMERS` | Table | Customer demographic & registration data |
| `PRODUCTS` | Table | Product catalog, pricing, and live inventory count |
| `ORDERS` | Table | Transactional sales orders |
| `RETAIL_SALES` | View | Denormalized join across orders, customers, and products |

---

## Troubleshooting & Common Fixes

### 1. `Database RETAIL_INTELLIGENCE_DB does not exist`
* **Fix**: Run `sql/setup.sql` in Snowsight with `ACCOUNTADMIN` role before starting the app.

### 2. `Fail: Network policy is required (Error 390432)`
* **Fix**: If using local connections or Personal Access Tokens (PAT), apply an open development network policy:
  ```sql
  CREATE OR REPLACE NETWORK POLICY ALLOW_ALL_NP ALLOWED_IP_LIST = ('0.0.0.0/0');
  ALTER ACCOUNT SET NETWORK_POLICY = ALLOW_ALL_NP;
  ```

### 3. `ModuleNotFoundError: No module named 'snowflake.connector'`
* **Fix**: Activate your virtual environment and run `pip install -r requirements.txt`.

---

## License

MIT License
