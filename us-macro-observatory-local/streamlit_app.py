"""US Macro Economic & Corporate Intelligence Observatory.

Multi-page Streamlit app over Snowflake's public data catalog
(SNOWFLAKE_PUBLIC_DATA_FREE), plus a fully CRUD-enabled personal watchlist.
"""

import streamlit as st

from utils.db import ensure_watchlist_table

st.set_page_config(
    page_title="US Macro Economic & Corporate Observatory",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure the app-owned CRUD table exists (idempotent, cheap after first run).
st.session_state.setdefault("watchlist_table_ready", False)
if not st.session_state.watchlist_table_ready:
    ensure_watchlist_table()
    st.session_state.watchlist_table_ready = True

# -------------------------------------------------------------
# Shared sidebar controls (available to every page via session_state)
# -------------------------------------------------------------
TIMEFRAME_MAP = {
    "1 Years": "2025-01-01",
    "3 Years": "2023-01-01",
    "5 Years": "2021-01-01",
    "10 Years": "2016-01-01",
    "Max History": "2000-01-01",
}

with st.sidebar:
    st.title("📊 US Data Observatory")
    st.caption("Powered by `SNOWFLAKE_PUBLIC_DATA_FREE`")

    st.session_state.setdefault("timeframe", "5 Years")
    st.selectbox(
        "📅 Timeframe Horizon",
        options=list(TIMEFRAME_MAP.keys()),
        key="timeframe",
    )
    st.session_state["start_date"] = TIMEFRAME_MAP[st.session_state.timeframe]

# -------------------------------------------------------------
# Navigation
# -------------------------------------------------------------
page = st.navigation(
    {
        "Overview": [
            st.Page("app_pages/home.py", title="Home", icon="🏠"),
        ],
        "Analysis": [
            st.Page("app_pages/labor.py", title="Labor & Employment", icon="👥"),
            st.Page("app_pages/inflation.py", title="Inflation & CPI", icon="🏷️"),
            st.Page("app_pages/housing.py", title="Housing Market", icon="🏡"),
            st.Page("app_pages/companies.py", title="Company Directory", icon="🏢"),
            st.Page("app_pages/correlations.py", title="Cross-Domain Correlations", icon="🔗"),
        ],
        "Intelligence": [
            st.Page("app_pages/ai_advisor.py", title="AI Advisor", icon="🤖"),
            st.Page("app_pages/sql_studio.py", title="SQL Studio", icon="🔍"),
        ],
        "Manage": [
            st.Page("app_pages/watchlist.py", title="My Watchlist", icon="⭐"),
        ],
    },
    posit