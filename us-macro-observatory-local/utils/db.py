"""Shared Snowflake connection, cached data loaders, and CRUD helpers.

LOCAL VERSION: Uses snowflake-snowpark-python with credentials from
.streamlit/secrets.toml via st.connection("snowflake").

All queries against the public reference data
(`SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`) are read-only.
The watchlist table (`HACKDAYS_APP_DB.APP_DATA.WATCHLIST`) is app-owned
and supports full Create / Read / Update / Delete.
"""

import streamlit as st

WATCHLIST_TABLE = "HACKDAYS_APP_DB.APP_DATA.WATCHLIST"
PUBLIC_DATA = "SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE"


def get_conn():
    return st.connection("snowflake")


def cortex_complete(prompt: str, model: str = "llama3.1-70b") -> str:
    """Call Snowflake Cortex COMPLETE via SQL."""
    session = get_conn().session()
    rows = session.sql(
        "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS RESPONSE",
        params=[model, prompt],
    ).collect()
    return rows[0]["RESPONSE"] if rows else ""


def ensure_watchlist_table():
    """Idempotently create the app-owned database/schema/tables."""
    session = get_conn().session()
    session.sql("CREATE DATABASE IF NOT EXISTS HACKDAYS_APP_DB").collect()
    session.sql("CREATE SCHEMA IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA").collect()
    session.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {WATCHLIST_TABLE} (
            ID NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
            ENTITY_TYPE VARCHAR(30) NOT NULL,
            ENTITY_NAME VARCHAR(500) NOT NULL,
            TARGET_VALUE FLOAT,
            NOTES VARCHAR(2000),
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            UPDATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
    ).collect()
    session.sql(
        """
        CREATE TABLE IF NOT EXISTS HACKDAYS_APP_DB.APP_DATA.INSIGHTS_LOG (
            ID NUMBER AUTOINCREMENT START 1 INCREMENT 1 PRIMARY KEY,
            INSIGHT_TYPE VARCHAR(50) NOT NULL,
            INSIGHT_TEXT VARCHAR(8000) NOT NULL,
            DATA_SNAPSHOT VARIANT,
            CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
    ).collect()


# -------------------------------------------------------------
# Read-only public data loaders (cached)
# -------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_macro_kpis():
    sql = f"""
    WITH unemp_by_date AS (
        SELECT
            t.DATE,
            AVG(t.VALUE * 100) AS AVG_VAL
        FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
        JOIN {PUBLIC_DATA}.GEOGRAPHY_INDEX g
          ON t.GEO_ID = g.GEO_ID
        WHERE g.LEVEL = 'State'
          AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
          AND t.VALUE IS NOT NULL
        GROUP BY t.DATE
    ),
    unemp_ranked AS (
        SELECT AVG_VAL AS VAL, ROW_NUMBER() OVER (ORDER BY DATE DESC) AS RN
        FROM unemp_by_date
    ),
    cpi_ranked AS (
        SELECT VALUE AS VAL, ROW_NUMBER() OVER (ORDER BY DATE DESC) AS RN
        FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'CPI:_All_items,_Seasonally_adjusted,_Monthly'
          AND VALUE IS NOT NULL
    ),
    hpi_ranked AS (
        SELECT VALUE AS VAL, ROW_NUMBER() OVER (ORDER BY DATE DESC) AS RN
        FROM {PUBLIC_DATA}.FHFA_HOUSE_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'FHFA_HPI_traditional_purchase-only_monthly_SA'
          AND VALUE IS NOT NULL
    ),
    comp_cnt AS (
        SELECT COUNT(*) AS CNT FROM {PUBLIC_DATA}.COMPANY_INDEX
    )
    SELECT
        MAX(CASE WHEN u.RN = 1 THEN u.VAL END) AS CURRENT_UNEMPLOYMENT,
        MAX(CASE WHEN u.RN = 2 THEN u.VAL END) AS PREV_UNEMPLOYMENT,
        MAX(CASE WHEN c.RN = 1 THEN c.VAL END) AS CURRENT_CPI,
        MAX(CASE WHEN c.RN = 13 THEN c.VAL END) AS PREV_YEAR_CPI,
        MAX(CASE WHEN h.RN = 1 THEN h.VAL END) AS CURRENT_HPI,
        MAX(CASE WHEN h.RN = 13 THEN h.VAL END) AS PREV_YEAR_HPI,
        MAX(comp_cnt.CNT) AS TOTAL_COMPANIES
    FROM comp_cnt
    LEFT JOIN unemp_ranked u ON u.RN IN (1, 2)
    LEFT JOIN cpi_ranked c ON c.RN IN (1, 13)
    LEFT JOIN hpi_ranked h ON h.RN IN (1, 13)
    """
    return get_conn().query(sql)


@st.cache_data(ttl=3600)
def load_unemployment_by_state(start_date: str):
    sql = f"""
    SELECT
        g.GEO_NAME AS STATE_NAME,
        t.DATE,
        ROUND(t.VALUE * 100, 2) AS UNEMPLOYMENT_RATE
    FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
    JOIN {PUBLIC_DATA}.GEOGRAPHY_INDEX g
        ON t.GEO_ID = g.GEO_ID
    WHERE g.LEVEL = 'State'
      AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
      AND t.VALUE IS NOT NULL
      AND t.DATE >= ?
    ORDER BY t.DATE ASC, g.GEO_NAME ASC
    """
    return get_conn().query(sql, params=[start_date])


@st.cache_data(ttl=3600)
def load_cpi_breakdown(start_date: str):
    sql = f"""
    SELECT
        DATE,
        REPLACE(REPLACE(VARIABLE, 'CPI:_', ''), ',_Seasonally_adjusted,_Monthly', '') AS CATEGORY,
        VALUE AS CPI_INDEX
    FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
    WHERE GEO_ID = 'country/USA'
      AND VARIABLE IN (
        'CPI:_All_items,_Seasonally_adjusted,_Monthly',
        'CPI:_Food,_Seasonally_adjusted,_Monthly',
        'CPI:_Energy,_Seasonally_adjusted,_Monthly',
        'CPI:_Shelter,_Seasonally_adjusted,_Monthly',
        'CPI:_Medical_care,_Seasonally_adjusted,_Monthly',
        'CPI:_Transportation,_Seasonally_adjusted,_Monthly',
        'CPI:_Apparel,_Seasonally_adjusted,_Monthly'
      )
      AND VALUE IS NOT NULL
      AND DATE >= ?
    ORDER BY DATE ASC, CATEGORY ASC
    """
    return get_conn().query(sql, params=[start_date])


@st.cache_data(ttl=3600)
def load_housing_hpi(start_date: str):
    sql = f"""
    SELECT
        DATE,
        VARIABLE_NAME AS MEASURE,
        VALUE AS HPI_INDEX
    FROM {PUBLIC_DATA}.FHFA_HOUSE_PRICE_TIMESERIES
    WHERE GEO_ID = 'country/USA'
      AND VARIABLE IN (
        'FHFA_HPI_traditional_purchase-only_monthly_SA',
        'FHFA_HPI_traditional_expanded-data_quarterly_SA'
      )
      AND VALUE IS NOT NULL
      AND DATE >= ?
    ORDER BY DATE ASC
    """
    return get_conn().query(sql, params=[start_date])


@st.cache_data(ttl=3600)
def load_macro_history():
    sql = f"""
    WITH unemp AS (
        SELECT t.DATE, ROUND(AVG(t.VALUE * 100), 3) AS UNEMPLOYMENT_RATE
        FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
        JOIN {PUBLIC_DATA}.GEOGRAPHY_INDEX g ON t.GEO_ID = g.GEO_ID
        WHERE g.LEVEL = 'State'
          AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
          AND t.VALUE IS NOT NULL
        GROUP BY t.DATE
    ),
    cpi AS (
        SELECT DATE, VALUE AS CPI_INDEX
        FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'CPI:_All_items,_Seasonally_adjusted,_Monthly'
          AND VALUE IS NOT NULL
    ),
    hpi AS (
        SELECT DATE, VALUE AS HPI_INDEX
        FROM {PUBLIC_DATA}.FHFA_HOUSE_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'FHFA_HPI_traditional_purchase-only_monthly_SA'
          AND VALUE IS NOT NULL
    )
    SELECT u.DATE, u.UNEMPLOYMENT_RATE, c.CPI_INDEX, h.HPI_INDEX
    FROM unemp u
    LEFT JOIN cpi c ON u.DATE = c.DATE
    LEFT JOIN hpi h ON u.DATE = h.DATE
    WHERE u.DATE >= '2010-01-01'
    ORDER BY u.DATE
    """
    return get_conn().query(sql)


@st.cache_data(ttl=3600)
def search_companies(query: str, exchange_filter: str, limit: int = 50):
    conditions = ["1=1"]
    params = []

    if query.strip():
        conditions.append("(COMPANY_NAME ILIKE ? OR PRIMARY_TICKER ILIKE ? OR CIK ILIKE ?)")
        like = f"%{query.strip()}%"
        params.extend([like, like, like])

    if exchange_filter and exchange_filter != "All Exchanges":
        conditions.append("PRIMARY_EXCHANGE_NAME = ?")
        params.append(exchange_filter)

    params.append(limit)

    sql = f"""
    SELECT
        COMPANY_NAME,
        PRIMARY_TICKER,
        PRIMARY_EXCHANGE_NAME AS EXCHANGE,
        CIK,
        EIN,
        ENTITY_LEVEL
    FROM {PUBLIC_DATA}.COMPANY_INDEX
    WHERE {' AND '.join(conditions)}
    ORDER BY CASE WHEN PRIMARY_TICKER IS NOT NULL THEN 0 ELSE 1 END, COMPANY_NAME ASC
    LIMIT ?
    """
    return get_conn().query(sql, params=params)


@st.cache_data(ttl=3600)
def load_exchanges():
    sql = f"""
    SELECT DISTINCT PRIMARY_EXCHANGE_NAME
    FROM {PUBLIC_DATA}.COMPANY_INDEX
    WHERE PRIMARY_EXCHANGE_NAME IS NOT NULL
    ORDER BY PRIMARY_EXCHANGE_NAME ASC
    """
    df = get_conn().query(sql)
    return ["All Exchanges"] + list(df["PRIMARY_EXCHANGE_NAME"].dropna())


@st.cache_data(ttl=3600)
def load_state_names():
    sql = f"""
    SELECT DISTINCT GEO_NAME
    FROM {PUBLIC_DATA}.GEOGRAPHY_INDEX
    WHERE LEVEL = 'State'
    ORDER BY GEO_NAME ASC
    """
    df = get_conn().query(sql)
    return list(df["GEO_NAME"].dropna())


@st.cache_data(ttl=3600)
def load_company_names(limit: int = 500):
    sql = f"""
    SELECT COMPANY_NAME
    FROM {PUBLIC_DATA}.COMPANY_INDEX
    WHERE COMPANY_NAME IS NOT NULL
    ORDER BY COMPANY_NAME ASC
    LIMIT ?
    """
    df = get_conn().query(sql, params=[limit])
    return list(df["COMPANY_NAME"].dropna())


@st.cache_data(ttl=3600)
def latest_unemployment_by_state_map():
    sql = f"""
    SELECT
        g.GEO_NAME AS STATE_NAME,
        ROUND(t.VALUE * 100, 2) AS UNEMPLOYMENT_RATE
    FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
    JOIN {PUBLIC_DATA}.GEOGRAPHY_INDEX g ON t.GEO_ID = g.GEO_ID
    WHERE g.LEVEL = 'State'
      AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
      AND t.VALUE IS NOT NULL
      AND t.DATE = (
          SELECT MAX(DATE) FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES
      )
    """
    df = get_conn().query(sql)
    return dict(zip(df["STATE_NAME"], df["UNEMPLOYMENT_RATE"]))


# -------------------------------------------------------------
# Watchlist CRUD (app-owned table)
# -------------------------------------------------------------
@st.cache_data(ttl=30)
def watchlist_list():
    sql = f"""
    SELECT ID, ENTITY_TYPE, ENTITY_NAME, TARGET_VALUE, NOTES, CREATED_AT, UPDATED_AT
    FROM {WATCHLIST_TABLE}
    ORDER BY UPDATED_AT DESC
    """
    return get_conn().query(sql)


def watchlist_create(entity_type: str, entity_name: str, target_value, notes: str):
    session = get_conn().session()
    session.sql(
        f"""
        INSERT INTO {WATCHLIST_TABLE} (ENTITY_TYPE, ENTITY_NAME, TARGET_VALUE, NOTES)
        VALUES (?, ?, ?, ?)
        """,
        params=[entity_type, entity_name, target_value, notes],
    ).collect()
    watchlist_list.clear()


def watchlist_update(row_id: int, target_value, notes: str):
    session = get_conn().session()
    session.sql(
        f"""
        UPDATE {WATCHLIST_TABLE}
        SET TARGET_VALUE = ?,
            NOTES = ?,
            UPDATED_AT = CURRENT_TIMESTAMP()
        WHERE ID = ?
        """,
        params=[target_value, notes, row_id],
    ).collect()
    watchlist_list.clear()


def watchlist_delete(row_ids: list):
    if not row_ids:
        return
    session = get_conn().session()
    placeholders = ", ".join("?" for _ in range(len(row_ids)))
    session.sql(
        f"DELETE FROM {WATCHLIST_TABLE} WHERE ID IN ({placeholders})",
        params=list(row_ids),
    ).collect()
    watchlist_list.clear()
