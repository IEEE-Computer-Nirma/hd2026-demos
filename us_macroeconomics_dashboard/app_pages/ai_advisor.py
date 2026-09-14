"""AI Economic Advisor — chat with Snowflake Cortex about macro data."""

import streamlit as st

from utils.db import cortex_complete, get_conn

SYSTEM_PROMPT = """You are an expert US macroeconomic analyst embedded in a Snowflake-powered
data observatory. You have access to these datasets from SNOWFLAKE_PUBLIC_DATA_FREE:

1. **BLS Employment** — Monthly state-level unemployment rates (LAUS, seasonally adjusted)
2. **BLS Consumer Price Index** — Monthly CPI across categories (All items, Food, Energy, Shelter, Medical care, Transportation, Apparel)
3. **FHFA House Price Index** — Monthly/quarterly US home price index (purchase-only, seasonally adjusted, base Jan 1991=100)
4. **Company Index** — ~2M+ global corporate entities with tickers, exchanges, CIK, EIN, LEI

When answering:
- Ground responses in the data context provided. Reference specific indicators by name.
- Explain economic relationships (e.g., unemployment vs inflation via Phillips Curve).
- Provide actionable interpretation, not just numbers.
- If the user asks about data you have context for, interpret it. If not, say so clearly.
- Keep responses concise but insightful. Use bullet points for clarity.
"""


def _build_data_context():
    sql = """
    WITH latest_unemp AS (
        SELECT ROUND(AVG(t.VALUE * 100), 2) AS AVG_RATE, MAX(t.DATE) AS AS_OF
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX g ON t.GEO_ID = g.GEO_ID
        WHERE g.LEVEL = 'State'
          AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
          AND t.VALUE IS NOT NULL
          AND t.DATE = (SELECT MAX(DATE) FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES)
    ),
    latest_cpi AS (
        SELECT VALUE AS CPI_VAL, DATE AS AS_OF
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'CPI:_All_items,_Seasonally_adjusted,_Monthly'
          AND VALUE IS NOT NULL
        ORDER BY DATE DESC LIMIT 1
    ),
    prev_cpi AS (
        SELECT VALUE AS CPI_VAL
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'CPI:_All_items,_Seasonally_adjusted,_Monthly'
          AND VALUE IS NOT NULL
        ORDER BY DATE DESC LIMIT 1 OFFSET 12
    ),
    latest_hpi AS (
        SELECT VALUE AS HPI_VAL, DATE AS AS_OF
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'FHFA_HPI_traditional_purchase-only_monthly_SA'
          AND VALUE IS NOT NULL
        ORDER BY DATE DESC LIMIT 1
    )
    SELECT
        u.AVG_RATE AS UNEMPLOYMENT_RATE,
        u.AS_OF AS UNEMP_DATE,
        c.CPI_VAL AS CURRENT_CPI,
        ROUND(((c.CPI_VAL - p.CPI_VAL) / p.CPI_VAL) * 100, 2) AS CPI_YOY_PCT,
        c.AS_OF AS CPI_DATE,
        h.HPI_VAL AS CURRENT_HPI,
        h.AS_OF AS HPI_DATE
    FROM latest_unemp u, latest_cpi c, prev_cpi p, latest_hpi h
    """
    try:
        df = get_conn().query(sql)
        if df.empty:
            return "No live data context available."
        r = df.iloc[0]
        return (
            f"LIVE DATA SNAPSHOT:\n"
            f"- Avg State Unemployment: {r['UNEMPLOYMENT_RATE']}% (as of {r['UNEMP_DATE']})\n"
            f"- CPI All Items: {r['CURRENT_CPI']} | YoY Inflation: {r['CPI_YOY_PCT']}% (as of {r['CPI_DATE']})\n"
            f"- FHFA Home Price Index: {r['CURRENT_HPI']} (as of {r['HPI_DATE']})\n"
        )
    except Exception:
        return "Live data context could not be loaded."


SUGGESTIONS = {
    ":blue[:material/trending_up:] Inflation outlook": "Based on the latest CPI data, what's the current inflation trend and outlook?",
    ":green[:material/cottage:] Housing affordability": "How has housing affordability changed? Analyze the HPI trend relative to inflation.",
    ":orange[:material/work:] Labor market health": "Assess the current health of the US labor market based on unemployment data across states.",
    ":violet[:material/compare_arrows:] Unemployment vs inflation": "Explain the relationship between unemployment and inflation. What does the current data suggest about the Phillips Curve?",
}

st.title("AI economic advisor")
st.caption("Ask questions about US macroeconomic data — powered by Snowflake Cortex")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "data_context" not in st.session_state:
    with st.spinner("Loading live data context..."):
        st.session_state.data_context = _build_data_context()

with st.expander("Current data context (grounding the AI)", expanded=False, icon=":material/database:"):
    st.code(st.session_state.data_context, language="text")

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state.chat_messages:
    selected = st.pills(
        "Try asking:", list(SUGGESTIONS.keys()), label_visibility="collapsed"
    )
    if selected:
        prompt = SUGGESTIONS[selected]
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        st.rerun()

if prompt := st.chat_input("Ask about unemployment, inflation, housing, companies..."):
    st.session_state.chat_messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n{st.session_state.data_context}\n\n"
            f"User question: {prompt}"
        )
        with st.spinner("Analyzing..."):
            try:
                response = cortex_complete(full_prompt)
            except Exception as e:
                response = f"Error calling Cortex: {e}"
        st.markdown(response)

    st.session_state.chat_messages.append({"role": "assistant", "content": response})

if st.session_state.chat_messages:
    if st.button("Clear conversation", type="tertiary", icon=":material/delete:"):
        st.session_state.chat_messages = []
        st.session_state.pop("data_context", None)
        st.rerun()
