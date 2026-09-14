"""Inflation & CPI analysis (BLS Consumer Price Index)."""

import streamlit as st

from utils.db import load_cpi_breakdown

st.title("🏷️ Consumer Price Index (CPI) Breakdown")
st.caption("Data source: Bureau of Labor Statistics (BLS) Consumer Price Index (CPI)")

start_date = st.session_state.get("start_date", "2021-01-01")

with st.spinner("Loading CPI series..."):
    df_cpi = load_cpi_breakdown(start_date)

if df_cpi.empty:
    st.warning("No data returned for the selected timeframe.")
else:
    df_cpi["DATE"] = df_cpi["DATE"].astype("datetime64[ns]")
    pivot_cpi = df_cpi.pivot(index="DATE", columns="CATEGORY", values="CPI_INDEX")

    st.markdown("#### 📊 CPI Category Trajectories")
    categories_available = list(pivot_cpi.columns)
    selected_cats = st.multiselect(
        "Select CPI Categories:",
        options=categories_available,
        default=[c for c in ["All_items", "Food", "Energy", "Shelter"] if c in categories_available],
    )

    if selected_cats:
        st.line_chart(pivot_cpi[selected_cats], width="stretch")

    st.markdown("#### 📉 YoY Inflation Rate by Category (%)")
    yoy_cpi = pivot_cpi.pct_change(periods=12) * 100
    yoy_cpi_clean = yoy_cpi.dropna(how="all")

    if selected_cats:
        st.line_chart(yoy_cpi_clean[selected_cats], width="stretch")

    with st.expander("📄 Underlying CPI Raw Index Values"):
        st.dataframe(pivot_cpi.sort_index(ascending=False), width="stretch")
