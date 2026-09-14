"""
utils/queries.py

Shared, cached Snowflake query functions for Retail Intelligence.
All functions accept filter arguments so that SQL-level filtering
is used instead of loading full datasets into pandas.
"""

import streamlit as st
import pandas as pd
from snowflake_connection import get_connection


# ---------------------------------------------------------------------------
# Shared connection — one pool per Streamlit session, not per query
# ---------------------------------------------------------------------------

@st.cache_resource
def get_conn():
    """Return a cached Snowflake connection shared across all pages."""
    return get_connection()


# ---------------------------------------------------------------------------
# Helper — execute a parameterized query, return a DataFrame
# ---------------------------------------------------------------------------

def _query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        cursor.close()


def _scalar(sql: str, params: tuple = ()):
    """Execute a query that returns a single row/value."""
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Filter options
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_filter_options() -> dict:
    """Return sorted lists of distinct countries and categories."""
    countries_df = _query(
        "SELECT DISTINCT COUNTRY FROM RETAIL_SALES ORDER BY COUNTRY"
    )
    categories_df = _query(
        "SELECT DISTINCT CATEGORY FROM RETAIL_SALES ORDER BY CATEGORY"
    )
    return {
        "countries": countries_df.iloc[:, 0].tolist(),
        "categories": categories_df.iloc[:, 0].tolist(),
    }


# ---------------------------------------------------------------------------
# KPI Metrics
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_kpis(country: str = "All", category: str = "All") -> dict:
    """
    Return headline KPIs filtered by country and/or category.
    Keys: total_revenue, total_orders, unique_customers, aov
    """
    where, params = _build_where(country, category)
    sql = f"""
        SELECT
            COALESCE(SUM(TOTAL_AMOUNT), 0)      AS TOTAL_REVENUE,
            COUNT(*)                             AS TOTAL_ORDERS,
            COUNT(DISTINCT CUSTOMER_ID)          AS UNIQUE_CUSTOMERS,
            COALESCE(AVG(TOTAL_AMOUNT), 0)       AS AOV
        FROM RETAIL_SALES
        {where}
    """
    row = _scalar(sql, tuple(params))
    if row is None:
        return {"total_revenue": 0.0, "total_orders": 0, "unique_customers": 0, "aov": 0.0}
    return {
        "total_revenue": float(row[0]),
        "total_orders": int(row[1]),
        "unique_customers": int(row[2]),
        "aov": float(row[3]),
    }


# ---------------------------------------------------------------------------
# Revenue trend
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_revenue_trend(country: str = "All", category: str = "All") -> pd.DataFrame:
    """Daily revenue over time, filtered."""
    where, params = _build_where(country, category)
    sql = f"""
        SELECT
            ORDER_DATE,
            SUM(TOTAL_AMOUNT) AS REVENUE
        FROM RETAIL_SALES
        {where}
        GROUP BY ORDER_DATE
        ORDER BY ORDER_DATE
    """
    df = _query(sql, tuple(params))
    df["REVENUE"] = df["REVENUE"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Category revenue
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_category_revenue(country: str = "All", category: str = "All") -> pd.DataFrame:
    where, params = _build_where(country, category)
    sql = f"""
        SELECT
            CATEGORY,
            SUM(TOTAL_AMOUNT) AS REVENUE
        FROM RETAIL_SALES
        {where}
        GROUP BY CATEGORY
        ORDER BY REVENUE DESC
    """
    df = _query(sql, tuple(params))
    df["REVENUE"] = df["REVENUE"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Country revenue
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_country_revenue(country: str = "All", category: str = "All") -> pd.DataFrame:
    where, params = _build_where(country, category)
    sql = f"""
        SELECT
            COUNTRY,
            SUM(TOTAL_AMOUNT) AS REVENUE
        FROM RETAIL_SALES
        {where}
        GROUP BY COUNTRY
        ORDER BY REVENUE DESC
    """
    df = _query(sql, tuple(params))
    df["REVENUE"] = df["REVENUE"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Top products
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_top_products(
    country: str = "All", category: str = "All", limit: int = 10
) -> pd.DataFrame:
    where, params = _build_where(country, category)
    sql = f"""
        SELECT
            PRODUCT_NAME      AS PRODUCT,
            CATEGORY,
            SUM(QUANTITY)     AS UNITS_SOLD,
            SUM(TOTAL_AMOUNT) AS REVENUE
        FROM RETAIL_SALES
        {where}
        GROUP BY PRODUCT_NAME, CATEGORY
        ORDER BY REVENUE DESC
        LIMIT {int(limit)}
    """
    df = _query(sql, tuple(params))
    df["REVENUE"] = df["REVENUE"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Top customers
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_top_customers(
    country: str = "All", category: str = "All", limit: int = 10
) -> pd.DataFrame:
    where, params = _build_where(country, category)
    sql = f"""
        SELECT
            CUSTOMER_NAME               AS CUSTOMER,
            COUNTRY,
            COUNT(DISTINCT ORDER_ID)    AS ORDERS,
            SUM(TOTAL_AMOUNT)           AS REVENUE
        FROM RETAIL_SALES
        {where}
        GROUP BY CUSTOMER_NAME, COUNTRY
        ORDER BY REVENUE DESC
        LIMIT {int(limit)}
    """
    df = _query(sql, tuple(params))
    df["REVENUE"] = df["REVENUE"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Customer metrics
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_customer_metrics(country: str = "All") -> pd.DataFrame:
    """Per-customer orders and revenue, optionally filtered by country."""
    where, params = _build_where(country=country)
    sql = f"""
        SELECT
            CUSTOMER_NAME               AS CUSTOMER,
            COUNTRY,
            COUNT(DISTINCT ORDER_ID)    AS ORDERS,
            SUM(TOTAL_AMOUNT)           AS REVENUE
        FROM RETAIL_SALES
        {where}
        GROUP BY CUSTOMER_NAME, COUNTRY
        ORDER BY REVENUE DESC
    """
    df = _query(sql, tuple(params))
    df["REVENUE"] = df["REVENUE"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Country distribution (for customer page)
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_customer_country_distribution() -> pd.DataFrame:
    sql = """
        SELECT
            COUNTRY,
            COUNT(DISTINCT CUSTOMER_ID) AS CUSTOMERS
        FROM RETAIL_SALES
        GROUP BY COUNTRY
        ORDER BY CUSTOMERS DESC
    """
    return _query(sql)


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_inventory() -> pd.DataFrame:
    """All products with price and stock, sorted by stock ascending."""
    sql = """
        SELECT
            PRODUCT_NAME    AS PRODUCT,
            CATEGORY,
            PRICE,
            STOCK
        FROM PRODUCTS
        ORDER BY STOCK ASC
    """
    df = _query(sql)
    df["PRICE"] = df["PRICE"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Recent orders
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_recent_orders(
    country: str = "All", category: str = "All", limit: int = 20
) -> pd.DataFrame:
    where, params = _build_where(country, category)
    sql = f"""
        SELECT
            ORDER_ID        AS ORDER_ID,
            ORDER_DATE,
            CUSTOMER_NAME   AS CUSTOMER,
            PRODUCT_NAME    AS PRODUCT,
            CATEGORY,
            QUANTITY,
            TOTAL_AMOUNT    AS AMOUNT
        FROM RETAIL_SALES
        {where}
        ORDER BY ORDER_DATE DESC
        LIMIT {int(limit)}
    """
    df = _query(sql, tuple(params))
    df["AMOUNT"] = df["AMOUNT"].astype(float)
    return df


# ---------------------------------------------------------------------------
# Quick insights (overview page)
# ---------------------------------------------------------------------------

@st.cache_data(ttl="10m")
def get_quick_insights() -> dict:
    """
    Return a single dict with snapshot insights from Snowflake.
    These are global (no filter) to give an overall picture.
    """
    # Best category
    cat = _scalar("""
        SELECT CATEGORY, SUM(TOTAL_AMOUNT) AS REV
        FROM RETAIL_SALES
        GROUP BY CATEGORY
        ORDER BY REV DESC
        LIMIT 1
    """)

    # Best product
    prod = _scalar("""
        SELECT PRODUCT_NAME, SUM(TOTAL_AMOUNT) AS REV
        FROM RETAIL_SALES
        GROUP BY PRODUCT_NAME
        ORDER BY REV DESC
        LIMIT 1
    """)

    # Top customer
    cust = _scalar("""
        SELECT CUSTOMER_NAME, SUM(TOTAL_AMOUNT) AS REV
        FROM RETAIL_SALES
        GROUP BY CUSTOMER_NAME
        ORDER BY REV DESC
        LIMIT 1
    """)

    # Lowest stock product
    low = _scalar("""
        SELECT PRODUCT_NAME, STOCK
        FROM PRODUCTS
        ORDER BY STOCK ASC
        LIMIT 1
    """)

    return {
        "best_category": (cat[0], float(cat[1])) if cat else ("—", 0.0),
        "best_product": (prod[0], float(prod[1])) if prod else ("—", 0.0),
        "top_customer": (cust[0], float(cust[1])) if cust else ("—", 0.0),
        "lowest_stock": (low[0], int(low[1])) if low else ("—", 0),
    }


# ---------------------------------------------------------------------------
# Cortex context builder (used by AI Advisor page)
# ---------------------------------------------------------------------------

def build_cortex_context(country: str = "All", category: str = "All") -> str:
    """
    Assemble a text context block from live Snowflake data.
    Used by the AI Advisor page to ground the Cortex prompt.
    """
    # Category performance
    cat_df = get_category_revenue(country, category)
    cat_ctx = "CATEGORY PERFORMANCE:\n"
    for _, row in cat_df.iterrows():
        cat_ctx += f"  - {row['CATEGORY']}: Revenue ${float(row['REVENUE']):,.2f}\n"

    # Product performance
    prod_df = get_top_products(country, category, limit=10)
    prod_ctx = "TOP PRODUCTS:\n"
    for _, row in prod_df.iterrows():
        prod_ctx += (
            f"  - {row['PRODUCT']} ({row['CATEGORY']}): "
            f"Revenue ${float(row['REVENUE']):,.2f}, Units Sold {row['UNITS_SOLD']}\n"
        )

    # Customer performance
    cust_df = get_top_customers(country, category, limit=10)
    cust_ctx = "TOP CUSTOMERS:\n"
    for _, row in cust_df.iterrows():
        cust_ctx += (
            f"  - {row['CUSTOMER']} ({row['COUNTRY']}): "
            f"Revenue ${float(row['REVENUE']):,.2f}, Orders {row['ORDERS']}\n"
        )

    # Inventory
    inv_df = get_inventory()
    inv_ctx = "INVENTORY:\n"
    for _, row in inv_df.iterrows():
        inv_ctx += (
            f"  - {row['PRODUCT']} ({row['CATEGORY']}): "
            f"{row['STOCK']} units in stock\n"
        )

    filter_ctx = (
        f"Active Country Filter: {country}\n"
        f"Active Category Filter: {category}\n"
    )

    return f"{filter_ctx}\n{cat_ctx}\n{prod_ctx}\n{cust_ctx}\n{inv_ctx}"


# ---------------------------------------------------------------------------
# Internal helper — WHERE clause builder
# ---------------------------------------------------------------------------

def _build_where(country: str = "All", category: str = "All"):
    """Return a (WHERE clause string, params list) tuple."""
    conditions = ["1 = 1"]
    params = []

    if country and country != "All":
        conditions.append("COUNTRY = %s")
        params.append(country)

    if category and category != "All":
        conditions.append("CATEGORY = %s")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions)
    return where, params
