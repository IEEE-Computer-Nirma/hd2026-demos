"""SQL studio: ad-hoc SELECT-only explorer against the public data catalog."""

import streamlit as st

from utils.db import get_conn

st.title("Interactive SQL explorer")
st.caption("Run ad-hoc read-only queries against `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`")

sample_queries = {
    "Top 10 states with highest unemployment (latest month)": """SELECT
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
    "US CPI inflation categories (last 12 months)": """SELECT
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
    "Federally declared disasters by type (last 5 years)": """SELECT
    DISASTER_TYPE,
    COUNT(*) AS TOTAL_DISASTERS,
    SUM(APPROVED_INDIVIDUAL_AND_HOUSEHOLDS_PROGRAM_AMOUNT) AS TOTAL_AID_DOLLARS
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_INDEX
WHERE DISASTER_DECLARATION_DATE >= DATEADD('year', -5, CURRENT_DATE())
GROUP BY DISASTER_TYPE
ORDER BY TOTAL_DISASTERS DESC
LIMIT 10;""",
}

selected_template = st.selectbox("Prebuilt query template", options=list(sample_queries.keys()))
user_sql = st.text_area("SQL statement", value=sample_queries[selected_template], height=180)

st.caption("Only `SELECT` statements are allowed.")

if st.button("Execute query", type="primary", icon=":material/play_arrow:"):
    stripped = user_sql.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT") and not stripped.upper().startswith("WITH"):
        st.error("Only `SELECT` (or `WITH ... SELECT`) statements are allowed.", icon=":material/error:")
    else:
        with st.spinner("Executing SQL query..."):
            try:
                sql_result = get_conn().query(stripped)
                st.success(f"Query returned {len(sql_result)} rows.", icon=":material/check_circle:")
                st.dataframe(sql_result, use_container_width=True)
            except Exception as e:
                st.error(f"SQL execution error: {e}", icon=":material/error:")
