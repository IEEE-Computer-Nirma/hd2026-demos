"""
app_pages/customer_insights.py

Customer Insights page — who are our most valuable customers?
Analysis based strictly on available Snowflake data.
"""

import streamlit as st
from utils.queries import (
    get_filter_options,
    get_top_customers,
    get_customer_metrics,
    get_customer_country_distribution,
)

# ── Sidebar filter ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    try:
        opts = get_filter_options()
        countries = ["All"] + opts["countries"]
    except Exception as e:
        st.error(f"Could not load filter options: {e}")
        countries = ["All"]

    country = st.selectbox(
        ":material/public: Country",
        countries,
        key="customers_country",
    )

    if country != "All":
        st.info(f"Filtering: **{country}**", icon=":material/filter_alt:")

st.caption("Revenue, order activity, and value of individual customers.")

st.divider()

# ── Customer KPI row ─────────────────────────────────────────────────────────
try:
    all_customers_df = get_customer_metrics(country)
except Exception as e:
    st.error(f"Could not load customer data: {e}")
    st.stop()

if all_customers_df.empty:
    st.warning("No customer data for the selected filter.")
    st.stop()

total_customers = len(all_customers_df)
avg_revenue = float(all_customers_df["REVENUE"].mean())
top_cust_name = all_customers_df.iloc[0]["CUSTOMER"]
top_cust_rev = float(all_customers_df.iloc[0]["REVENUE"])

with st.container(horizontal=True):
    st.metric(
        label=":material/group: Total customers",
        value=f"{total_customers:,}",
        border=True,
    )
    st.metric(
        label=":material/payments: Avg revenue / customer",
        value=f"${avg_revenue:,.2f}",
        border=True,
    )
    st.metric(
        label=":material/emoji_events: Top customer",
        value=top_cust_name,
        border=True,
    )
    st.metric(
        label=":material/trending_up: Top customer spend",
        value=f"${top_cust_rev:,.2f}",
        border=True,
    )

st.divider()

# ── Top customers table ──────────────────────────────────────────────────────
st.subheader(":material/leaderboard: Top customers")

with st.container(border=True):
    try:
        top_df = get_top_customers(country=country, limit=10)
        if top_df.empty:
            st.info("No data for the selected filter.")
        else:
            display_df = top_df.copy()
            display_df.columns = ["Customer", "Country", "Orders", "Revenue"]
            display_df["Revenue"] = display_df["Revenue"].map("${:,.2f}".format)
            st.dataframe(display_df, hide_index=True)
    except Exception as e:
        st.error(f"Top customers error: {e}")

st.divider()

# ── Revenue by customer chart ─────────────────────────────────────────────────
st.subheader(":material/bar_chart: Revenue and orders by customer")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    with st.container(border=True):
        st.markdown("**Revenue by customer (top 10)**")
        try:
            rev_df = all_customers_df.head(10)[["CUSTOMER", "REVENUE"]].copy()
            st.bar_chart(rev_df.set_index("CUSTOMER"), height=280)
        except Exception as e:
            st.error(f"Revenue chart error: {e}")

with chart_col2:
    with st.container(border=True):
        st.markdown("**Orders by customer (top 10)**")
        try:
            ord_df = all_customers_df.head(10)[["CUSTOMER", "ORDERS"]].copy()
            st.bar_chart(ord_df.set_index("CUSTOMER"), height=280)
        except Exception as e:
            st.error(f"Orders chart error: {e}")

st.divider()

# ── Country distribution ──────────────────────────────────────────────────────
st.subheader(":material/public: Customer distribution by country")

with st.container(border=True):
    try:
        dist_df = get_customer_country_distribution()
        if dist_df.empty:
            st.info("No distribution data available.")
        else:
            st.bar_chart(dist_df.set_index("COUNTRY"), height=260)
    except Exception as e:
        st.error(f"Country distribution error: {e}")
