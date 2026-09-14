"""US Macro Economic & Corporate Intelligence Observatory.

Multi-page Streamlit app over Snowflake's public data catalog
(SNOWFLAKE_PUBLIC_DATA_FREE), plus a fully CRUD-enabled personal watchlist.
"""

import streamlit as st

from utils.db import ensure_watchlist_table

st.set_page_config(
    page_title="US Macro Observatory",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.session_state.setdefault("watchlist_table_ready", False)
if not st.session_state.watchlist_table_ready:
    ensure_watchlist_table()
    st.session_state.watchlist_table_ready = True

TIMEFRAME_MAP = {
    "1 Year": "2025-01-01",
    "3 Years": "2023-01-01",
    "5 Years": "2021-01-01",
    "10 Years": "2016-01-01",
    "Max history": "2000-01-01",
}

with st.sidebar:
    st.title("US Macro Observatory")
    st.caption("Powered by Snowflake Public Data")

    st.session_state.setdefault("timeframe", "5 Years")
    st.selectbox(
        "Timeframe",
        options=list(TIMEFRAME_MAP.keys()),
        key="timeframe",
    )
    st.session_state["start_date"] = TIMEFRAME_MAP[st.session_state.timeframe]

page = st.navigation(
    {
        "Overview": [
            st.Page("app_pages/home.py", title="Home", icon=":material/home:"),
            st.Page("app_pages/dashboard.py", title="Interactive dashboard", icon=":material/dashboard:"),
        ],
        "Analysis": [
            st.Page("app_pages/labor.py", title="Labor & employment", icon=":material/group:"),
            st.Page("app_pages/inflation.py", title="Inflation & CPI", icon=":material/price_change:"),
            st.Page("app_pages/housing.py", title="Housing market", icon=":material/cottage:"),
            st.Page("app_pages/companies.py", title="Company directory", icon=":material/business:"),
            st.Page("app_pages/correlations.py", title="Cross-domain correlations", icon=":material/hub:"),
        ],
        "Intelligence": [
            st.Page("app_pages/ai_advisor.py", title="AI advisor", icon=":material/smart_toy:"),
            st.Page("app_pages/sql_studio.py", title="SQL studio", icon=":material/code:"),
            st.Page("app_pages/ml_training.py", title="ML training lab", icon=":material/psychology:"),
        ],
        "Manage": [
            st.Page("app_pages/watchlist.py", title="My watchlist", icon=":material/bookmark:"),
        ],
    },
    position="sidebar",
)

page.run()
