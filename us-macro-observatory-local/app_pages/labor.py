"""Labor & Employment analysis (BLS Local Area Unemployment Statistics)."""

import pandas as pd
import streamlit as st

from utils.db import load_unemployment_by_state

st.title("👥 US Labor Market & State Unemployment Trends")
st.caption("Data source: Bureau of Labor Statistics (BLS) Local Area Unemployment Statistics (LAUS)")

start_date = st.session_state.get("start_date", "2021-01-01")

with st.spinner("Loading state employment data..."):
    df_unemp = load_unemployment_by_state(start_date)

if df_unemp.empty:
    st.warning("No data returned for the selected timeframe.")
else:
    df_unemp["DATE"] = pd.to_datetime(df_unemp["DATE"])
    latest_date = df_unemp["DATE"].max()
    df_latest = df_unemp[df_unemp["DATE"] == latest_date].sort_values("UNEMPLOYMENT_RATE", ascending=False)

    top_col1, top_col2 = st.columns(2)
    with top_col1:
        st.markdown(f"**Highest State Unemployment Rates** ({latest_date.strftime('%B %Y')})")
        st.dataframe(
            df_latest.head(10)[["STATE_NAME", "UNEMPLOYMENT_RATE"]].rename(
                columns={"STATE_NAME": "State / Territory", "UNEMPLOYMENT_RATE": "Rate (%)"}
            ),
            width="stretch",
            hide_index=True,
        )
    with top_col2:
        st.markdown(f"**Lowest State Unemployment Rates** ({latest_date.strftime('%B %Y')})")
        st.dataframe(
            df_latest.tail(10).iloc[::-1][["STATE_NAME", "UNEMPLOYMENT_RATE"]].rename(
                columns={"STATE_NAME": "State / Territory", "UNEMPLOYMENT_RATE": "Rate (%)"}
            ),
            width="stretch",
            hide_index=True,
        )

    st.markdown("#### 📈 Multi-State Comparative Trend")
    all_states = sorted(df_unemp["STATE_NAME"].unique())
    default_selection = [s for s in ["California", "Texas", "New York", "Florida", "Illinois"] if s in all_states]
    selected_states = st.multiselect("Select States to Compare:", options=all_states, default=default_selection)

    if selected_states:
        df_filtered = df_unemp[df_unemp["STATE_NAME"].isin(selected_states)]
        pivot_states = df_filtered.pivot(index="DATE", columns="STATE_NAME", values="UNEMPLOYMENT_RATE")
        st.line_chart(pivot_states, width="stretch")
    else:
        st.info("Select at least one state from the list above to view the time series.")

    with st.expander("📄 View Full State-by-State Data Table"):
        st.dataframe(df_unemp, width="stretch")
