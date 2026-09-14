"""Housing market analysis (FHFA House Price Index)."""

import streamlit as st

from utils.db import load_housing_hpi

st.title("FHFA House Price Index")
st.caption("Data source: Federal Housing Finance Agency single-family repeat-sales mortgage transactions")

start_date = st.session_state.get("start_date", "2021-01-01")

with st.spinner("Loading housing index..."):
    df_hpi = load_housing_hpi(start_date)

if df_hpi.empty:
    st.warning("No data returned for the selected timeframe.", icon=":material/warning:")
else:
    df_hpi["DATE"] = df_hpi["DATE"].astype("datetime64[ns]")
    pivot_hpi = df_hpi.pivot(index="DATE", columns="MEASURE", values="HPI_INDEX")

    st.subheader("US single-family home price trajectory", anchor=False)
    st.line_chart(pivot_hpi, use_container_width=True)

    st.subheader("Key housing metrics", anchor=False)
    latest_hpi_val = pivot_hpi.iloc[-1].dropna()
    earliest_hpi_val = pivot_hpi.iloc[0].dropna()

    with st.container(horizontal=True):
        st.metric("Latest index level", f"{latest_hpi_val.values[0]:.2f}", f"{pivot_hpi.index[-1].strftime('%B %Y')}", border=True)
        growth_pct = ((latest_hpi_val.values[0] - earliest_hpi_val.values[0]) / earliest_hpi_val.values[0]) * 100
        st.metric(f"Cumulative growth ({st.session_state.get('timeframe', '')})", f"{growth_pct:+.2f}%", border=True)
        st.metric("Base period", "Jan 1991 = 100", border=True)

    with st.expander("View housing index history", icon=":material/table_chart:"):
        st.dataframe(df_hpi.sort_values("DATE", ascending=False), use_container_width=True)
