"""SQL Studio: ad-hoc SELECT-only explorer against the public data catalog."""

import streamlit as st

from utils.db import get_conn

st.title("🔍 Interactive SQL Explorer")
st.caption("Run ad-hoc read-only queries against `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`")
st.info("For safety, only `SELECT` statements are allowed here.")

sample_queries = {
    "Top 10 States with Highest Unemployment (Latest Month)": """SELECT
    g.GEO_NAME AS STATE_NAME,
    t.DATE,
    ROUND(t.VALUE * 100, 2) AS UNEMPLOYMENT_RATE_PCT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX g
    ON t.GEO_ID = g.GEO_ID
WHERE g.LEVEL = 'State'
  AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
  AND t.DATE = (SELECT MAX(DATE) FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES)
ORDER BY UNEMPLOYMENT_RATE_PCT DESC
LIMIT 10;""",
    "US CPI Inflation Categories (Last 12 Months)": """SELECT
    DATE,
    VARIABLE_NAME,
    VALUE AS CPI_INDEX
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
WHERE GEO_ID = 'country/USA'
  AND VARIABLE IN (
    'CPI:_All_items,_Seasonally_adjusted,_Monthly',
    'CPI:_Food,_Seasonally_adjusted,_Monthly',
    'CPI:_Energy,_Seasonally_adjusted,_Monthly'
  )
  AND DATE >= DATEADD('month', -12, CURRENT_DATE())
ORDER BY DATE DESC, VARIABLE_NAME ASC;""",
    "Federally Declared Disasters by Incident Type (Last 5 Years)": """SELECT
    DISASTER_TYPE,
    COUNT(*) AS TOTAL_DISASTERS,
    SUM(APPROVED_INDIVIDUAL_AND_HOUSEHOLDS_PROGRAM_AMOUNT) AS TOTAL_AID_DOLLARS
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_INDEX
WHERE DISASTER_DECLARATION_DATE >= DATEADD('year', -5, CURRENT_DATE())
GROUP BY DISASTER_TYPE
ORDER BY TOTAL_DISASTERS DESC
LIMIT 10;""",
}

selected_template = st.selectbox("Choose a prebuilt SQL query template:", options=list(sample_queries.keys()))
user_sql = st.text_area("SQL Statement:", value=sample_queries[selected_template], height=180)

if st.button("▶️ Execute Query", type="primary"):
    stripped = user_sql.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT") and not stripped.upper().startswith("WITH"):
        st.error("Only `SELECT` (or `WITH ... SELECT`) statements are allowed in this explorer.")
    else:
        with st.spinner("Executing SQL query on Snowflake..."):
            try:
                sql_result = get_conn().query(stripped)
                st.success(f"Query returned {len(sql_result)} rows.")
                st.dataframe(sql_result, width="stretch")
            except Exception as e:
                st.error(f"SQL Execution Error: {e}")
