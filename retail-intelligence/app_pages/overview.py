"""
app_pages/overview.py

Overview / Home page — headline KPIs, revenue charts, top products,
and a Quick Insights section drawn from live Snowflake data.
"""

import streamlit as st
from utils.queries import (
    get_kpis,
    get_revenue_trend,
    get_category_revenue,
    get_top_products,
    get_quick_insights,
)

# ── Description ────────────────────────────────────────────────────────────
st.caption("A high-level view of your retail business performance.")

st.divider()

# ── KPI cards ──────────────────────────────────────────────────────────────
try:
    kpis = get_kpis()
except Exception as e:
    st.error(f"Could not load KPI data: {e}")
    st.stop()

with st.container(horizontal=True):
    st.metric(
        label=":material/payments: Total Revenue",
        value=f"${kpis['total_revenue']:,.0f}",
        border=True,
    )
    st.metric(
        label=":material/shopping_cart: Total Orders",
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

# ── Revenue charts ──────────────────────────────────────────────────────────
st.subheader(":material/bar_chart: Revenue analytics")

trend_col, cat_col = st.columns(2)

with trend_col:
    with st.container(border=True):
        st.markdown("**Revenue over time**")
        try:
            trend_df = get_revenue_trend()
            if trend_df.empty:
                st.info("No revenue data available.")
            else:
                st.line_chart(trend_df.set_index("ORDER_DATE"), height=240)
        except Exception as e:
            st.error(f"Revenue trend error: {e}")

with cat_col:
    with st.container(border=True):
        st.markdown("**Revenue by category**")
        try:
            cat_df = get_category_revenue()
            if cat_df.empty:
                st.info("No category data available.")
            else:
                st.bar_chart(cat_df.set_index("CATEGORY"), height=240)
        except Exception as e:
            st.error(f"Category revenue error: {e}")

st.divider()

# ── Top products ────────────────────────────────────────────────────────────
st.subheader(":material/star: Top products")

with st.container(border=True):
    try:
        products_df = get_top_products(limit=5)
        if products_df.empty:
            st.info("No product data available.")
        else:
            display_df = products_df.copy()
            display_df.columns = ["Product", "Category", "Units Sold", "Revenue"]
            display_df["Revenue"] = display_df["Revenue"].map("${:,.2f}".format)
            st.dataframe(display_df, hide_index=True)
    except Exception as e:
        st.error(f"Top products error: {e}")

st.divider()

# ── Quick insights ──────────────────────────────────────────────────────────
st.subheader(":material/lightbulb: Quick insights")

try:
    insights = get_quick_insights()

    i1, i2, i3, i4 = st.columns(4)

    with i1:
        with st.container(border=True):
            st.markdown("**Highest revenue category**")
            name, rev = insights["best_category"]
            st.markdown(f"### {name}")
            st.caption(f"${rev:,.0f} in revenue")

    with i2:
        with st.container(border=True):
            st.markdown("**Best-selling product**")
            name, rev = insights["best_product"]
            st.markdown(f"### {name}")
            st.caption(f"${rev:,.0f} in revenue")

    with i3:
        with st.container(border=True):
            st.markdown("**Top customer**")
            name, rev = insights["top_customer"]
            st.markdown(f"### {name}")
            st.caption(f"${rev:,.0f} total spend")

    with i4:
        with st.container(border=True):
            st.markdown("**Lowest stock product**")
            name, stock = insights["lowest_stock"]
            st.markdown(f"### {name}")
            if int(stock) < 100:
                st.caption(f":red[⚠ {int(stock)} units remaining]")
            else:
                st.caption(f"{int(stock)} units remaining")

except Exception as e:
    st.error(f"Could not load quick insights: {e}")
