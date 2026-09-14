"""
app_pages/sales_analytics.py

Sales Analytics page — filterable revenue metrics, country/category
breakdowns, top products, and recent orders — all powered by Snowflake.
"""

import streamlit as st
import altair as alt
from utils.queries import (
    get_filter_options,
    get_kpis,
    get_revenue_trend,
    get_category_revenue,
    get_country_revenue,
    get_top_products,
    get_recent_orders,
)

# ── Sidebar filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filters")
    try:
        opts = get_filter_options()
        countries = ["All"] + opts["countries"]
        categories = ["All"] + opts["categories"]
    except Exception as e:
        st.error(f"Could not load filter options: {e}")
        countries, categories = ["All"], ["All"]

    country = st.selectbox(
        ":material/public: Country",
        countries,
        key="sales_country",
    )
    category = st.selectbox(
        ":material/inventory_2: Category",
        categories,
        key="sales_category",
    )

    if country != "All" or category != "All":
        st.info(
            f"Filtering: **{country}** · **{category}**",
            icon=":material/filter_alt:",
        )

st.caption("Detailed sales performance filtered by country and product category.")

st.divider()

# ── KPI row ─────────────────────────────────────────────────────────────────
try:
    kpis = get_kpis(country, category)
except Exception as e:
    st.error(f"Could not load KPIs: {e}")
    st.stop()

with st.container(horizontal=True):
    st.metric(
        label=":material/payments: Revenue",
        value=f"${kpis['total_revenue']:,.0f}",
        border=True,
    )
    st.metric(
        label=":material/shopping_cart: Orders",
        value=f"{kpis['total_orders']:,}",
        border=True,
    )
    st.metric(
        label=":material/group: Customers",
        value=f"{kpis['unique_customers']:,}",
        border=True,
    )
    st.metric(
        label=":material/trending_up: Avg Order Value",
        value=f"${kpis['aov']:,.2f}",
        border=True,
    )

st.divider()

# ── Revenue over time ────────────────────────────────────────────────────────
st.subheader(":material/show_chart: Revenue over time")

with st.container(border=True):
    try:
        trend_df = get_revenue_trend(country, category)
        if trend_df.empty:
            st.info("No data for the selected filters.")
        else:
            chart = (
                alt.Chart(trend_df)
                .mark_line(point=True, strokeWidth=2)
                .encode(
                    x=alt.X(
                        "ORDER_DATE:T",
                        title=None,
                        axis=alt.Axis(
                            format="%b %d",
                            labelAngle=-35,
                            tickCount="week",
                        ),
                    ),
                    y=alt.Y(
                        "REVENUE:Q",
                        title="Revenue (USD)",
                        axis=alt.Axis(format="$,.0f"),
                    ),
                    tooltip=[
                        alt.Tooltip("ORDER_DATE:T", title="Date", format="%b %d, %Y"),
                        alt.Tooltip("REVENUE:Q", title="Revenue", format="$,.2f"),
                    ],
                )
                .properties(height=260)
            )
            st.altair_chart(chart)
    except Exception as e:
        st.error(f"Revenue trend error: {e}")

st.divider()

# ── Country + Category breakdown ────────────────────────────────────────────
st.subheader(":material/bar_chart: Revenue breakdown")

breakdown_col1, breakdown_col2 = st.columns(2)

with breakdown_col1:
    with st.container(border=True):
        st.markdown("**By country**")
        try:
            country_df = get_country_revenue(country, category)
            if country_df.empty:
                st.info("No country data available.")
            else:
                st.bar_chart(country_df.set_index("COUNTRY"), height=240)
        except Exception as e:
            st.error(f"Country revenue error: {e}")

with breakdown_col2:
    with st.container(border=True):
        st.markdown("**By category**")
        try:
            cat_df = get_category_revenue(country, category)
            if cat_df.empty:
                st.info("No category data available.")
            else:
                st.bar_chart(cat_df.set_index("CATEGORY"), height=240)
        except Exception as e:
            st.error(f"Category revenue error: {e}")

st.divider()

# ── Top products ─────────────────────────────────────────────────────────────
st.subheader(":material/star: Top products")

with st.container(border=True):
    try:
        prod_df = get_top_products(country, category, limit=10)
        if prod_df.empty:
            st.info("No product data for the selected filters.")
        else:
            display_df = prod_df.copy()
            display_df.columns = ["Product", "Category", "Units Sold", "Revenue"]
            display_df["Revenue"] = display_df["Revenue"].map("${:,.2f}".format)
            st.dataframe(display_df, hide_index=True)
    except Exception as e:
        st.error(f"Top products error: {e}")

st.divider()

# ── Recent orders ────────────────────────────────────────────────────────────
st.subheader(":material/receipt_long: Recent orders")

with st.container(border=True):
    try:
        orders_df = get_recent_orders(country, category, limit=20)
        if orders_df.empty:
            st.info("No orders for the selected filters.")
        else:
            display_orders = orders_df.copy()
            display_orders.columns = [
                "Order ID", "Date", "Customer", "Product",
                "Category", "Quantity", "Amount"
            ]
            display_orders["Amount"] = display_orders["Amount"].map("${:,.2f}".format)
            st.dataframe(display_orders, hide_index=True)
    except Exception as e:
        st.error(f"Recent orders error: {e}")
