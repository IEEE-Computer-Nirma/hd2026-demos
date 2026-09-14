"""
app.py

Retail Intelligence — entry point.
Defines the multi-page navigation and shared app-level configuration.
"""

import streamlit as st

st.set_page_config(
    page_title="Retail Intelligence",
    page_icon=":material/storefront:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Navigation ───────────────────────────────────────────────────────────────

page = st.navigation(
    {
        "": [
            st.Page(
                "app_pages/overview.py",
                title="Overview",
                icon=":material/home:",
                default=True,
            ),
        ],
        "Analytics": [
            st.Page(
                "app_pages/sales_analytics.py",
                title="Sales analytics",
                icon=":material/bar_chart:",
            ),
            st.Page(
                "app_pages/customer_insights.py",
                title="Customer insights",
                icon=":material/group:",
            ),
            st.Page(
                "app_pages/inventory.py",
                title="Inventory",
                icon=":material/inventory_2:",
            ),
        ],
        "AI": [
            st.Page(
                "app_pages/ai_advisor.py",
                title="AI advisor",
                icon=":material/smart_toy:",
            ),
        ],
    },
    position="sidebar",
)

# ── Sidebar branding ─────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0;">
            <span style="font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em;">
                🛍️ Retail Intelligence
            </span><br>
            <span style="font-size: 0.78rem; opacity: 0.6;">
                Snowflake · Cortex · Streamlit
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

# ── Page title (rendered above page content) ─────────────────────────────────

st.title(page.title, anchor=False)

# ── Run current page ──────────────────────────────────────────────────────────

page.run()