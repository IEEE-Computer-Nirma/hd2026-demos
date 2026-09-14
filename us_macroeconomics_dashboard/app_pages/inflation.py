"""Inflation & CPI analysis (BLS Consumer Price Index)."""

import streamlit as st

from utils.db import load_cpi_breakdown

st.title("Consumer Price Index (CPI) breakdown")
st.caption("Data source: Bureau of Labor Statistics (BLS) Consumer Price Index")

start_date = st.session_state.get("start_date", "2021-01-01")

with st.spinner("Loading CPI series..."):
    df_cpi = load_cpi_breakdown(start_date)

if df_cpi.empty:
    st.warning("No data returned for the selected timeframe.", icon=":material/warning:")
else:
    df_cpi["DATE"] = df_cpi["DATE"].astype("datetime64[ns]")
    pivot_cpi = df_cpi.pivot(index="DATE", columns="CATEGORY", values="CPI_INDEX")

    st.subheader("CPI category trajectories", anchor=False)
    categories_available = list(pivot_cpi.columns)
    selected_cats = st.multiselect(
        "Select CPI categories",
        options=categories_available,
        default=[c for c in ["All_items", "Food", "Energy", "Shelter"] if c in categories_available],
    )

    if selected_cats:
        st.line_chart(pivot_cpi[selected_cats], use_container_width=True)

    st.subheader("YoY inflation rate by category (%)", anchor=False)
    yoy_cpi = pivot_cpi.pct_change(periods=12) * 100
    yoy_cpi_clean = yoy_cpi.dropna(how="all")

    if selected_cats:
        st.line_chart(yoy_cpi_clean[selected_cats], use_container_width=True)

    with st.expander("Underlying CPI raw index values", icon=":material/table_chart:"):
        st.dataframe(pivot_cpi.sort_index(ascending=False), use_container_width=True)
