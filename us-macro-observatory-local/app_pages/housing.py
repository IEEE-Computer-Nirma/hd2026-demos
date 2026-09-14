"""Housing Market analysis (FHFA House Price Index)."""

import streamlit as st

from utils.db import load_housing_hpi

st.title("🏡 Federal Housing Finance Agency (FHFA) House Price Index")
st.caption("Data source: FHFA Single-Family Repeat-Sales Mortgage Transactions (Fannie Mae & Freddie Mac)")

start_date = st.session_state.get("start_date", "2021-01-01")

with st.spinner("Loading housing index..."):
    df_hpi = load_housing_hpi(start_date)

if df_hpi.empty:
    st.warning("No data returned for the selected timeframe.")
else:
    df_hpi["DATE"] = df_hpi["DATE"].astype("datetime64[ns]")
    pivot_hpi = df_hpi.pivot(index="DATE", columns="MEASURE", values="HPI_INDEX")

    st.markdown("#### 🏘️ US Single-Family Home Price Trajectory")
    st.line_chart(pivot_hpi, width="stretch")

    st.markdown("#### 📊 Key Housing Metrics")
    latest_hpi_val = pivot_hpi.iloc[-1].dropna()
    earliest_hpi_val = pivot_hpi.iloc[0].dropna()

    hpi_col1, hpi_col2, hpi_col3 = st.columns(3)
    with hpi_col1:
        st.metric("Latest Index Level", f"{latest_hpi_val.values[0]:.2f}", f"{pivot_hpi.index[-1].strftime('%B %Y')}")
    with hpi_col2:
        growth_pct = ((latest_hpi_val.values[0] - earliest_hpi_val.values[0]) / earliest_hpi_val.values[0]) * 100
        st.metric(f"Cumulative Growth ({st.session_state.get('timeframe', '')})", f"{growth_pct:+.2f}%")
    with hpi_col3:
        st.metric("Base Period", "Jan 1991 = 100")

    with st.expander("📄 View Housing Index History Table"):
        st.dataframe(df_hpi.sort_values("DATE", ascending=False), width="stretch")
