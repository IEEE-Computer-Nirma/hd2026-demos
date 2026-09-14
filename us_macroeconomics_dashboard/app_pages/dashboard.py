"""Interactive dashboard — multi-indicator explorer with anomaly detection and regime classification."""

import numpy as np
import pandas as pd
import streamlit as st

from utils.db import load_macro_history, load_unemployment_by_state, cortex_complete

st.title("Interactive dashboard")
st.caption("Explore macro indicators side-by-side, detect anomalies, and classify economic regimes")

start_date = st.session_state.get("start_date", "2021-01-01")

# ----- Load & prepare data -----

@st.cache_data(ttl=3600)
def _prepare_dashboard_data():
    raw = load_macro_history()
    if raw.empty:
        return pd.DataFrame()
    raw["DATE"] = pd.to_datetime(raw["DATE"])
    raw = raw.sort_values("DATE").set_index("DATE")
    raw["CPI_YOY_PCT"] = raw["CPI_INDEX"].pct_change(periods=12) * 100
    raw["HPI_YOY_PCT"] = raw["HPI_INDEX"].pct_change(periods=12) * 100
    raw["UNEMP_CHANGE_YOY"] = raw["UNEMPLOYMENT_RATE"] - raw["UNEMPLOYMENT_RATE"].shift(12)
    return raw.dropna()


df = _prepare_dashboard_data()

if df.empty:
    st.warning("No data available. Check your Snowflake connection and timeframe.", icon=":material/warning:")
    st.stop()

# Filter to selected timeframe
df = df[df.index >= start_date]

if df.empty:
    st.warning("No data for the selected timeframe.", icon=":material/warning:")
    st.stop()

INDICATORS = {
    "Unemployment rate (%)": "UNEMPLOYMENT_RATE",
    "CPI index level": "CPI_INDEX",
    "CPI YoY inflation (%)": "CPI_YOY_PCT",
    "Home price index": "HPI_INDEX",
    "HPI YoY change (%)": "HPI_YOY_PCT",
    "Unemployment YoY change (pp)": "UNEMP_CHANGE_YOY",
}


# ===== SECTION 1: Multi-indicator explorer =====

st.subheader("Multi-indicator explorer", anchor=False)

selected_labels = st.multiselect(
    "Select indicators to overlay",
    list(INDICATORS.keys()),
    default=["Unemployment rate (%)", "CPI YoY inflation (%)", "HPI YoY change (%)"],
)

if selected_labels:
    cols = [INDICATORS[lbl] for lbl in selected_labels]
    chart_df = df[cols].rename(columns={INDICATORS[lbl]: lbl for lbl in selected_labels})
    st.line_chart(chart_df, use_container_width=True)


# ===== SECTION 2: Anomaly detection =====

st.subheader("Anomaly detection", anchor=False)
st.caption("Months where indicators deviate more than 2 standard deviations from their trailing 36-month average")

z_threshold = st.slider("Z-score threshold", 1.0, 3.0, 2.0, 0.25, key="anomaly_z")
trailing_window = 36

anomaly_records = []
for label, col in [
    ("Unemployment rate", "UNEMPLOYMENT_RATE"),
    ("CPI YoY inflation", "CPI_YOY_PCT"),
    ("HPI YoY change", "HPI_YOY_PCT"),
]:
    if col not in df.columns:
        continue
    series = df[col]
    rolling_mean = series.rolling(trailing_window, min_periods=12).mean()
    rolling_std = series.rolling(trailing_window, min_periods=12).std()
    z_scores = (series - rolling_mean) / rolling_std.replace(0, np.nan)

    anomalies = z_scores[z_scores.abs() > z_threshold].dropna()
    for date, z in anomalies.items():
        anomaly_records.append({
            "Date": date.strftime("%Y-%m"),
            "Indicator": label,
            "Value": f"{series.loc[date]:.2f}",
            "Z-score": f"{z:+.2f}",
            "Direction": "Above" if z > 0 else "Below",
        })

if anomaly_records:
    anomaly_df = pd.DataFrame(anomaly_records).sort_values("Date", ascending=False)

    with st.container(border=True):
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total anomalies", len(anomaly_df), border=True)
        above = len(anomaly_df[anomaly_df["Direction"] == "Above"])
        col_b.metric("Above normal", above, border=True)
        col_c.metric("Below normal", len(anomaly_df) - above, border=True)

    with st.expander("View all detected anomalies", icon=":material/search:"):
        st.dataframe(anomaly_df, hide_index=True, use_container_width=True)
else:
    st.caption("No anomalies detected at the current threshold.")


# ===== SECTION 3: Economic regime classifier =====

st.subheader("Economic regime classifier", anchor=False)
st.caption("Rule-based classification using unemployment trend and inflation level")

def classify_regime(row):
    unemp = row.get("UNEMPLOYMENT_RATE")
    cpi_yoy = row.get("CPI_YOY_PCT")
    unemp_chg = row.get("UNEMP_CHANGE_YOY")

    if unemp is None or cpi_yoy is None or unemp_chg is None:
        return "Insufficient data"
    if pd.isna(unemp) or pd.isna(cpi_yoy) or pd.isna(unemp_chg):
        return "Insufficient data"

    high_inflation = cpi_yoy > 4.0
    rising_unemployment = unemp_chg > 0.5
    falling_unemployment = unemp_chg < -0.3
    low_unemployment = unemp < 5.0

    if high_inflation and rising_unemployment:
        return "Stagflation"
    elif high_inflation and not rising_unemployment:
        return "Overheating"
    elif not high_inflation and falling_unemployment and low_unemployment:
        return "Expansion"
    elif not high_inflation and rising_unemployment:
        return "Contraction"
    elif not high_inflation and not rising_unemployment:
        return "Stable growth"
    return "Mixed signals"


regime_df = df.copy()
regime_df["Regime"] = regime_df.apply(classify_regime, axis=1)

REGIME_COLORS = {
    "Expansion": "green",
    "Stable growth": "blue",
    "Overheating": "orange",
    "Contraction": "red",
    "Stagflation": "violet",
    "Mixed signals": "gray",
}

# Current regime
current_regime = regime_df["Regime"].iloc[-1]
current_date = regime_df.index[-1].strftime("%B %Y")

with st.container(border=True):
    rc1, rc2 = st.columns([1, 2])
    with rc1:
        color = REGIME_COLORS.get(current_regime, "gray")
        st.metric("Current regime", current_regime, current_date, border=True)
    with rc2:
        regime_counts = regime_df["Regime"].value_counts()
        total = len(regime_df)
        badges = []
        for regime, count in regime_counts.items():
            pct = count / total * 100
            badges.append(f"**{regime}**: {pct:.0f}% ({count} months)")
        st.markdown("**Regime distribution** (selected timeframe)")
        st.markdown(" | ".join(badges))

# Regime timeline
regime_map = {"Expansion": 3, "Stable growth": 2, "Overheating": 1, "Mixed signals": 0, "Contraction": -1, "Stagflation": -2, "Insufficient data": -3}
regime_df["Regime_Score"] = regime_df["Regime"].map(regime_map)
st.bar_chart(regime_df[["Regime_Score"]].rename(columns={"Regime_Score": "Regime score"}), use_container_width=True)
st.caption("Regime score: 3=Expansion, 2=Stable, 1=Overheating, 0=Mixed, -1=Contraction, -2=Stagflation")


# ===== SECTION 4: State-level heatmap =====

st.subheader("State unemployment ranking", anchor=False)

with st.spinner("Loading state data..."):
    df_states = load_unemployment_by_state(start_date)

if not df_states.empty:
    df_states["DATE"] = pd.to_datetime(df_states["DATE"])
    latest_date = df_states["DATE"].max()
    df_latest = df_states[df_states["DATE"] == latest_date].sort_values("UNEMPLOYMENT_RATE", ascending=False)

    n_show = st.slider("Number of states to display", 5, 50, 15, key="state_n")
    st.bar_chart(
        df_latest.head(n_show).set_index("STATE_NAME")["UNEMPLOYMENT_RATE"],
        use_container_width=True,
        horizontal=True,
    )
    st.caption(f"Data as of {latest_date.strftime('%B %Y')}")


# ===== SECTION 5: AI regime summary =====

st.subheader("AI regime analysis", anchor=False)

if st.button("Generate AI analysis", icon=":material/auto_awesome:", type="secondary"):
    last_row = regime_df.iloc[-1]
    prompt = (
        "You are a macroeconomic analyst. Based on the following data, provide a 3-4 sentence "
        "assessment of the current US economic regime and what to watch for:\n"
        f"- Current regime classification: {current_regime}\n"
        f"- Unemployment rate: {last_row['UNEMPLOYMENT_RATE']:.2f}%\n"
        f"- CPI YoY inflation: {last_row['CPI_YOY_PCT']:.2f}%\n"
        f"- HPI YoY change: {last_row['HPI_YOY_PCT']:.2f}%\n"
        f"- Unemployment YoY change: {last_row['UNEMP_CHANGE_YOY']:+.2f}pp\n"
        f"- Anomalies detected: {len(anomaly_records)}\n"
        "Be specific and use the numbers provided."
    )
    with st.spinner("Analyzing..."):
        try:
            analysis = cortex_complete(prompt)
            with st.container(border=True):
                st.markdown(analysis)
        except Exception as e:
            st.error(f"AI analysis unavailable: {e}", icon=":material/error:")
