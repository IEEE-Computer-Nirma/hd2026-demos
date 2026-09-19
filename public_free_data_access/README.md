# Snowflake Public Free Data Access — Tutorials & Hands-on Labs

A comprehensive hands-on learning hub designed to master Snowflake using free public datasets (`SNOWFLAKE_PUBLIC_DATA_FREE`) and sample benchmark datasets (`SNOWFLAKE_SAMPLE_DATA`).

This directory includes **SQL worksheets**, **Python scripts**, **Jupyter Notebooks**, and **pre-extracted CSV datasets** progressing from beginner exploration to advanced cross-domain analytics and AI assistants.

---

## 📋 Table of Contents

1. [Overview & Available Datasets](#overview--available-datasets)
2. [Prerequisites & Snowflake Setup](#prerequisites--snowflake-setup)
3. [Repository Structure](#repository-structure)
4. [Part 1: SQL Learning Path](#part-1-sql-learning-path)
5. [Part 2: Python Data Science Scripts](#part-2-python-data-science-scripts)
6. [Part 3: Interactive Jupyter Notebooks](#part-3-interactive-jupyter-notebooks)
7. [Part 4: Pre-packaged CSV Datasets](#part-4-pre-packaged-csv-datasets)
8. [Troubleshooting & FAQs](#troubleshooting--faqs)

---

## Overview & Available Datasets

Snowflake provides free, production-grade datasets that do not count against storage costs:

| Dataset Database | Description | Key Tables |
|------------------|-------------|------------|
| `SNOWFLAKE_PUBLIC_DATA_FREE` | Curated public datasets (Economics, Demographics, Weather, Finance, FEMA, Aviation) | `BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES`, `BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES`, `FHFA_HOUSE_PRICE_TIMESERIES`, `COMPANY_INDEX`, `GEOGRAPHY_INDEX`, `FEMA_DISASTER_DECLARATION_AREAS_INDEX` |
| `SNOWFLAKE_SAMPLE_DATA` | Standard industry benchmark datasets (TPC-H and TPC-DS) | `TPCH_SF1.CUSTOMER`, `TPCH_SF1.ORDERS`, `TPCH_SF1.LINEITEM`, `TPCH_SF1.PART`, `TPCH_SF1.SUPPLIER` |

---

## Prerequisites & Snowflake Setup

### 1. Snowflake Account
Ensure you have access to a Snowflake account. If you don't have one, sign up for a 30-day Free Trial at [signup.snowflake.com](https://signup.snowflake.com).

### 2. Add `SNOWFLAKE_PUBLIC_DATA_FREE` to your Account
1. Log in to [Snowsight](https://app.snowflake.com).
2. In the left navigation menu, navigate to **Data Products** > **Marketplace**.
3. In the search bar, type `Snowflake Public Data Free` (published by Snowflake).
4. Click on the listing and click **Get**.
5. Keep the default database name as `SNOWFLAKE_PUBLIC_DATA_FREE` and click **Get**.

### 3. Verify Dataset Access in SQL
Open a SQL Worksheet in Snowsight and run:

```sql
USE ROLE ACCOUNTADMIN;

-- 1. Check if the database is available
SHOW DATABASES LIKE 'SNOWFLAKE_PUBLIC_DATA_FREE';

-- 2. Verify row counts across key tables
SELECT 'BLS_EMPLOYMENT' AS DATASET, COUNT(*) AS TOTAL_ROWS
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES
UNION ALL
SELECT 'BLS_CPI', COUNT(*)
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
UNION ALL
SELECT 'FHFA_HOUSING', COUNT(*)
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
UNION ALL
SELECT 'COMPANY_INDEX', COUNT(*)
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.COMPANY_INDEX
UNION ALL
SELECT 'TPCH_ORDERS', COUNT(*)
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS;
```

---

## Repository Structure

```
public_free_data_access/
├── data/                                      # Pre-extracted CSV files for offline/local use
│   ├── us_macro_monthly.csv                   # Monthly US Unemployment, CPI, and HPI metrics
│   └── tpch_orders_enriched.csv               # TPC-H orders joined with customer and nation data
├── notebooks/                                 # Interactive Jupyter Notebooks
│   ├── 01_us_macro_dashboard.ipynb            # Visual macroeconomic EDA & charts
│   ├── 02_tpch_retail_analytics.ipynb         # Supply chain & retail analytics
│   └── 03_ai_data_assistant.ipynb             # Snowflake Cortex AI natural language SQL assistant
├── python/                                    # Standalone Python scripts (Pandas & data analysis)
│   ├── 01_beginner_python.py                  # Basic data exploration, filtering, summary stats
│   ├── 02_intermediate_python.py              # Aggregations, grouping, multi-dataset merges
│   └── 03_advanced_python.py                  # Statistical correlation, rolling windows, trend modeling
└── sql/                                       # Progressive SQL tutorials
    ├── 01_beginner_exploring_datasets.sql     # SELECT, SHOW, WHERE, LIMIT, ILIKE, COUNT
    ├── 02_intermediate_single_dataset.sql    # GROUP BY, HAVING, CASE WHEN, Window Functions
    ├── 03_advanced_cross_dataset.sql          # Multi-table JOINs, CTEs, lag/lead, cross-domain
    ├── 04_tpch_retail_training.sql           # TPC-H retail business intelligence queries
    └── public_data_free_guide.sql             # Reference catalog & time series join patterns
```

---

## Part 1: SQL Learning Path

Run these SQL scripts directly in Snowsight Worksheets or inside Snowflake Workspaces.

### Progression Overview

| Script | Level | Skills Covered | Datasets Used |
|--------|-------|----------------|---------------|
| `sql/01_beginner_exploring_datasets.sql` | Beginner | `SHOW`, `SELECT`, `LIMIT`, `WHERE`, `ILIKE`, `ORDER BY`, `COUNT` | Public Data Index, Calendar, Geography, Company, TPC-H |
| `sql/02_intermediate_single_dataset.sql` | Intermediate | `GROUP BY`, `HAVING`, `CASE WHEN`, `DATEADD`, `EXTRACT`, `ROUND` | BLS Employment, BLS CPI, FEMA Disasters, TPC-H Orders |
| `sql/03_advanced_cross_dataset.sql` | Advanced | Complex `JOIN`, `WITH` (CTEs), `LAG()` / `LEAD()`, Window Aggregations | BLS + FHFA + Geography + FEMA cross-domain joins |
| `sql/04_tpch_retail_training.sql` | Advanced BI | Revenue analysis, Customer RFM segmentation, Supply chain analytics | `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1` |
| `sql/public_data_free_guide.sql` | Reference | Time series pattern (`_TIMESERIES` + `_ATTRIBUTES` + `_PIT`) | Complete Public Data Catalogue |

### How to Run in Snowsight
1. Open Snowsight at [app.snowflake.com](https://app.snowflake.com).
2. Go to **Projects** > **Worksheets** > click **+** (New SQL Worksheet).
3. Set your execution context:
   - **Role**: `ACCOUNTADMIN` (or any role with access to public data)
   - **Warehouse**: `COMPUTE_WH`
4. Copy and paste the contents of any script from the `sql/` folder and execute statements individually or as a batch (using `Ctrl + Enter` / `Cmd + Enter`).

---

## Part 2: Python Data Science Scripts

The `python/` directory contains standalone Python scripts that analyze the pre-extracted CSV datasets using `pandas`, `numpy`, and `matplotlib`.

### Setup & Local Execution

#### Step 1: Create & Activate Virtual Environment

**On macOS / Linux:**
```bash
cd /path/to/hd2026-demos
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
cd \path\to\hd2026-demos
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Step 2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install pandas numpy matplotlib seaborn snowflake-snowpark-python
```

#### Step 3: Run the Scripts

##### Script 1: Beginner Python (`01_beginner_python.py`)
Explores data shape, column data types, summary statistics, missing values, and simple frequency counts.
```bash
python public_free_data_access/python/01_beginner_python.py
```

##### Script 2: Intermediate Python (`02_intermediate_python.py`)
Performs time series date filtering, monthly aggregations, customer segment revenue calculations, and multi-metric grouping.
```bash
python public_free_data_access/python/02_intermediate_python.py
```

##### Script 3: Advanced Python (`03_advanced_python.py`)
Computes Pearson cross-correlations between Inflation (CPI) and House Prices (HPI), calculates rolling standard deviations, and evaluates lead-lag relationships (+/- 6 months).
```bash
python public_free_data_access/python/03_advanced_python.py
```

---

## Part 3: Interactive Jupyter Notebooks

Three interactive notebooks are provided in `notebooks/`:

| Notebook | Topic | Description |
|----------|-------|-------------|
| `01_us_macro_dashboard.ipynb` | Macroeconomic EDA | Interactive visualization of US labor trends, inflation indices, and housing dynamics. |
| `02_tpch_retail_analytics.ipynb` | Retail Analytics | Supply chain optimization, customer cohort analysis, and sales performance. |
| `03_ai_data_assistant.ipynb` | AI Data Assistant | Cortex LLM integration (`SNOWFLAKE.CORTEX.COMPLETE`) translating plain-language prompts into SQL. |

### Running in Snowflake Workspaces (Recommended)
1. In Snowsight, navigate to **Projects** > **Workspaces**.
2. Open the workspace containing this repository.
3. In the workspace file explorer, navigate to `public_free_data_access/notebooks/`.
4. Click on any `.ipynb` file to open it directly in the native Snowflake Notebook UI.
5. Select warehouse **`COMPUTE_WH`** in the top bar.
6. Run the notebook cells sequentially.

### Running Locally via JupyterLab
If running outside Snowflake:
```bash
pip install jupyterlab ipywidgets
jupyter lab public_free_data_access/notebooks/
```

---

## Part 4: Pre-packaged CSV Datasets

For quick offline prototyping without querying Snowflake live:

### 1. `data/us_macro_monthly.csv`
- **Grain**: Monthly records (from 2010 to present).
- **Columns**:
  - `DATE`: First day of each month (`YYYY-MM-DD`).
  - `UNEMPLOYMENT_RATE`: US National Unemployment Rate (Seasonally Adjusted %).
  - `CPI_ALL_ITEMS`: Consumer Price Index for All Urban Consumers.
  - `CPI_FOOD`: CPI Food Sub-index.
  - `CPI_ENERGY`: CPI Energy Sub-index.
  - `CPI_SHELTER`: CPI Shelter Sub-index.
  - `HPI_INDEX`: FHFA House Price Index (Purchase-only).

### 2. `data/tpch_orders_enriched.csv`
- **Grain**: Individual customer orders from TPC-H Benchmark.
- **Columns**:
  - `O_ORDERKEY`: Unique order identifier.
  - `O_CUSTKEY`: Unique customer identifier.
  - `O_ORDERSTATUS`: Order status (`O` = Open, `F` = Fulfilled, `P` = Pending).
  - `O_TOTALPRICE`: Total transaction amount in USD.
  - `O_ORDERDATE`: Order timestamp.
  - `O_ORDERPRIORITY`: Priority class (`1-URGENT`, `2-HIGH`, `3-MEDIUM`, `4-NOT SPECIFIED`, `5-LOW`).
  - `C_NAME`: Customer display name.
  - `C_MKTSEGMENT`: Market segment (`BUILDING`, `AUTOMOBILE`, `MACHINERY`, `HOUSEHOLD`, `FURNITURE`).
  - `N_NAME`: Customer nationality / country.
  - `R_NAME`: Geographic region (`AMERICA`, `EUROPE`, `ASIA`, `AFRICA`, `MIDDLE EAST`).

---

## Troubleshooting & FAQs

### Q1: `Database 'SNOWFLAKE_PUBLIC_DATA_FREE' does not exist`
- **Fix**: The dataset has not yet been acquired in your account. Go to **Marketplace** > search `Snowflake Public Data Free` > click **Get**.

### Q2: `Database 'SNOWFLAKE_SAMPLE_DATA' does not exist`
- **Fix**: In trial or standard accounts, if `SNOWFLAKE_SAMPLE_DATA` was dropped, restore it using:
  ```sql
  CREATE DATABASE IF NOT EXISTS SNOWFLAKE_SAMPLE_DATA FROM SHARE SFC_SAMPLES.SAMPLE_DATA;
  ```

### Q3: `FileNotFoundError: public_free_data_access/data/us_macro_monthly.csv` when running Python scripts
- **Fix**: Ensure your working directory is the repository root (`hd2026-demos`), or pass absolute file paths to `pd.read_csv()`.

---

## License

MIT License
