# Retail Intelligence

A Snowflake-powered retail analytics application with interactive business intelligence and AI-powered insights using Snowflake Cortex.

---

## Features

- **Interactive sales analytics** — revenue trends, country/category breakdowns, top products
- **Customer insights** — most valuable customers, revenue per customer, order activity
- **Inventory monitoring** — stock levels, low-stock alerts, full product catalogue
- **Snowflake-powered KPIs** — all metrics queried live from Snowflake
- **Snowflake Views** — `RETAIL_SALES` view joins orders, customers, and products
- **Snowflake Cortex AI** — natural language business analysis via `SNOWFLAKE.CORTEX.COMPLETE`
- **Streamlit interface** — multi-page app with sidebar navigation
- **Country / category filtering** — SQL-level filtering (no full-dataset loads)

---

## Architecture

```
Streamlit (app.py)
    ↓
Python (app_pages/ + utils/queries.py)
    ↓
Snowflake Connector (snowflake_connection.py)
    ↓
Snowflake (RETAIL_INTELLIGENCE_DB.RETAIL)
    ├── CUSTOMERS
    ├── PRODUCTS
    ├── ORDERS
    └── RETAIL_SALES  (view — joins all three tables)
    ↓
Snowflake Cortex  (SNOWFLAKE.CORTEX.COMPLETE)
    ↓
AI Business Insights
```

---

## Project Structure

```
retail-intelligence/
├── app.py                        # Entry point — st.navigation router
├── snowflake_connection.py       # Snowflake connector (reads .env)
├── test_connection.py            # Quick connection test script
│
├── app_pages/                    # One file per page
│   ├── overview.py               # Home — KPIs, charts, quick insights
│   ├── sales_analytics.py        # Sales — filters, breakdown, orders
│   ├── customer_insights.py      # Customer value analysis
│   ├── inventory.py              # Stock monitoring + low-stock alerts
│   └── ai_advisor.py             # Cortex AI Business Advisor
│
├── utils/
│   └── queries.py                # Shared cached Snowflake query functions
│
├── sql/
│   └── setup.sql                 # DDL + sample data + view (reproducibility)
│
├── .streamlit/
│   └── config.toml               # App theme (dark, Inter font)
│
├── .env                          # Snowflake credentials (not committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Interface | Streamlit |
| Language | Python 3.10+ |
| Data warehouse | Snowflake |
| AI | Snowflake Cortex (`llama3.1-70b`) |
| Query layer | Snowflake Python Connector |
| Data manipulation | Pandas |
| Config | python-dotenv |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/retail-intelligence.git
cd retail-intelligence
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SNOWFLAKE_ACCOUNT=your-account-identifier
SNOWFLAKE_USER=your-username
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=RETAIL_INTELLIGENCE_DB
SNOWFLAKE_SCHEMA=RETAIL
```

> **Never commit `.env` to version control.**

### 5. Set up Snowflake (first time only)

Run `sql/setup.sql` in your Snowflake worksheet to create the database, tables, sample data, and the `RETAIL_SALES` view.

### 6. Test the connection

```bash
python test_connection.py
```

Expected output: `('RETAIL_INTELLIGENCE_DB', 'RETAIL', 'COMPUTE_WH')`

### 7. Run the application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Snowflake Objects

| Object | Type | Description |
|--------|------|-------------|
| `CUSTOMERS` | Table | Customer profiles with country |
| `PRODUCTS` | Table | Product catalogue with price and stock |
| `ORDERS` | Table | Order transactions |
| `RETAIL_SALES` | View | Denormalized join: orders + customers + products |

---

## Pages

| Page | Path | Description |
|------|------|-------------|
| Overview | `app_pages/overview.py` | KPIs, revenue charts, quick insights |
| Sales analytics | `app_pages/sales_analytics.py` | Filterable sales breakdown |
| Customer insights | `app_pages/customer_insights.py` | Customer value analysis |
| Inventory | `app_pages/inventory.py` | Stock levels and low-stock alerts |
| AI advisor | `app_pages/ai_advisor.py` | Snowflake Cortex Q&A |

---

## AI Advisor

The AI Advisor uses **Snowflake Cortex** (`SNOWFLAKE.CORTEX.COMPLETE`) with the `llama3.1-70b` model.

It receives a context block built from live Snowflake data (category performance, top products, top customers, inventory) and answers natural language business questions grounded entirely in that data.

Example questions:
- "Which product performs best?"
- "Who is our best customer?"
- "Which category should we focus on?"
- "Which products have low inventory?"
- "Which product performs best in India?" *(with India filter active)*

---

## License

MIT
