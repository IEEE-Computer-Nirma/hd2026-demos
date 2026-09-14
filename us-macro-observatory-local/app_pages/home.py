"""Overview: cross-domain KPIs, trend sparklines, and statistically grounded analysis."""

import numpy as np
import pandas as pd
import streamlit as st

from utils.db import (
    cortex_complete,
    load_cpi_breakdown,
    load_housing_hpi,
    load_macro_history,
    load_macro_kpis,
    load_unemployment_by_state,
)


def _compute_series_stats(series: pd.Series, z_window: int = 60, trend_window: int = 6):
    """Z-score and percentile vs a trailing window, plus a short-term trend slope.

    z_window: months of trailing history used for the mean/std baseline (default 5yr).
    trend_window: months used to fit a linear trend (slope per month).
    """
    s = series.dropna()
    if len(s) < 6:
        return None

    hist = s.iloc[-z_window:] if len(s) > z_window else s
    latest = float(s.iloc[-1])
    mean = float(hist.mean())
    std = float(hist.std(ddof=0))
    z_score = (latest - mean) / std if std > 0 else 0.0
    percentile = float((hist < latest).mean() * 100)

    trend_slice = s.iloc[-trend_window:]
    if len(trend_slice) >= 2:
        x = np.arange(len(trend_slice))
        slope = float(np.polyfit(x, trend_slice.values, 1)[0])
    else:
        slope = 0.0

    return {
        "latest": latest,
        "mean": mean,
        "std": std,
        "z_score": z_score,
        "percentile": percentile,
        "trend_slope_per_month": slope,
        "window_months": len(hist),
    }


@st.cache_data(ttl=3600)
def _generate_narrative(stats_summary: str) -> str:
    prompt = (
        "You are a macroeconomic analyst writing for a data dashboard. Base your analysis "
        "ONLY on the statistically computed indicators below — each shows the latest value, "
        "the trailing-window mean, a z-score (standard deviations from that mean), a percentile "
        "rank within the trailing window, and a 6-month linear trend slope per month.\n\n"
        f"{stats_summary}\n\n"
        "Write a 3-4 sentence analytical summary of the current US economic state. Be specific "
        "about direction and magnitude using the actual numbers, call out any statistically "
        "notable readings (|z-score| > 1.5, or percentile above 85 / below 15), and note any "
        "tension between indicators (e.g., inflation trending up while labor market cools). "
        "Do not restate the raw numbers verbatim — interpret them."
    )
    try:
        return cortex_complete(prompt)
    except Exception as e:
        return f"Narrative unavailable: {e}"


st.title("📈 US Macroeconomic & Corporate Intelligence Observatory")
st.write(
    "Explore authoritative US public datasets directly from Snowflake's curated "
    "public data catalog — with statistically grounded analysis."
)

start_date = st.session_state.get("start_date", "2021-01-01")

with st.spinner("Fetching macro indicators..."):
    kpis = load_macro_kpis()

# --- KPI row ---
if not kpis.empty:
    cur_unemp = kpis["CURRENT_UNEMPLOYMENT"].iloc[0]
    prev_unemp = kpis["PREV_UNEMPLOYMENT"].iloc[0]
    unemp_delta = (cur_unemp - prev_unemp) if (cur_unemp is not None and prev_unemp is not None) else 0

    cur_cpi = kpis["CURRENT_CPI"].iloc[0]
    prev_cpi = kpis["PREV_YEAR_CPI"].iloc[0]
    cpi_yoy = ((cur_cpi - prev_cpi) / prev_cpi * 100) if (cur_cpi is not None and prev_cpi is not None) else 0

    cur_hpi = kpis["CURRENT_HPI"].iloc[0]
    prev_hpi = kpis["PREV_YEAR_HPI"].iloc[0]
    hpi_yoy = ((cur_hpi - prev_hpi) / prev_hpi * 100) if (cur_hpi is not None and prev_hpi is not None) else 0

    total_comps = kpis["TOTAL_COMPANIES"].iloc[0]

    with st.container(horizontal=True):
        st.metric(
            "Avg State Unemployment Rate",
            f"{cur_unemp:.2f}%" if cur_unemp is not None else "N/A",
            delta=f"{unemp_delta:+.2f}% MoM",
            delta_color="inverse",
            border=True,
        )
        st.metric(
            "CPI YoY Inflation",
            f"{cpi_yoy:.2f}%" if cur_cpi is not None else "N/A",
            delta=f"{cur_cpi:.1f} Index Level" if cur_cpi is not None else None,
            border=True,
        )
        st.metric(
            "Home Price Index YoY",
            f"{hpi_yoy:+.2f}%" if cur_hpi is not None else "N/A",
            delta=f"{cur_hpi:.1f} HPI" if cur_hpi is not None else None,
            border=True,
        )
        st.metric(
            "Tracked Entities",
            f"{int(total_comps):,}" if total_comps is not None else "N/A",
            delta="SEC & Public Entities",
            border=True,
        )

# --- Statistical analysis (z-scores, percentiles, trend) + Cortex narrative ---
with st.spinner("Computing statistics..."):
    history = load_macro_history()

stats = {}
if not history.empty:
    history["DATE"] = pd.to_datetime(history["DATE"])
    history = history.set_index("DATE").sort_index()
    history["CPI_YOY_PCT"] = history["CPI_INDEX"].pct_change(periods=12) * 100
    history["HPI_YOY_PCT"] = history["HPI_INDEX"].pct_change(periods=12) * 100

    for label, col in [
        ("Unemployment Rate (%)", "UNEMPLOYMENT_RATE"),
        ("CPI YoY Inflation (%)", "CPI_YOY_PCT"),
        ("Home Price Index YoY (%)", "HPI_YOY_PCT"),
    ]:
        if col in history.columns:
            s = _compute_series_stats(history[col])
            if s:
                stats[label] = s

if stats:
    stats_lines = [
        f"- {label}: latest={s['latest']:.2f}, {s['window_months']}mo-mean={s['mean']:.2f}, "
        f"z-score={s['z_score']:+.2f}, percentile={s['percentile']:.0f}th, "
        f"6mo trend slope={s['trend_slope_per_month']:+.3f}/month"
        for label, s in stats.items()
    ]
    stats_summary = "\n".join(stats_lines)

    with st.container(border=True):
        st.subheader("🧠 Statistical Analysis")
        with st.spinner("Generating analysis..."):
            narrative = _generate_narrative(stats_summary)
        st.markdown(narrative)
        with st.expander("📐 Underlying statistics"):
            st.code(stats_summary, language="text")
        st.caption("Analysis is grounded in trailing z-scores, percentile rank, and 6-month trend slope — not fixed thresholds.")

st.divider()

# --- Trend charts ---
col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.subheader("👥 State Unemployment Trend")
        df_unemp = load_unemployment_by_state(start_date)
        if not df_unemp.empty:
            df_unemp["DATE"] = pd.to_datetime(df_unemp["DATE"])
            national_avg = df_unemp.groupby("DATE")["UNEMPLOYMENT_RATE"].mean()
            st.line_chart(national_avg, width="stretch")
        st.caption("National average of state-level unemployment rates. See **Labor & Employment** for detail.")

with col2:
    with st.container(border=True):
        st.subheader("🏡 Housing Price Index Trend")
        df_hpi = load_housing_hpi(start_date)
        if not df_hpi.empty:
            df_hpi["DATE"] = pd.to_datetime(df_hpi["DATE"])
            pivot_hpi = df_hpi.pivot(index="DATE", columns="MEASURE", values="HPI_INDEX")
            st.line_chart(pivot_hpi, width="stretch")
        st.caption("US single-family home price index. See **Housing Market** for detail.")

with st.container(border=True):
    st.subheader("🏷️ CPI Category Snapshot")
    df_cpi = load_cpi_breakdown(start_date)
    if not df_cpi.empty:
        df_cpi["DATE"] = pd.to_datetime(df_cpi["DATE"])
        pivot_cpi = df_cpi.pivot(index="DATE", columns="CATEGORY", values="CPI_INDEX")
        st.line_chart(pivot_cpi, width="stretch")
    st.caption("Consumer Price Index across major categories. See **Inflation & CPI** for detail.")

# --- State disparity quick view ---
if not df_unemp.empty:
    with st.container(border=True):
        st.subheader("🗺️ State Unemployment Disparity")
        latest_date = df_unemp["DATE"].max()
        df_latest = df_unemp[df_unemp["DATE"] == latest_date].sort_values("UNEMPLOYMENT_RATE", ascending=False)
        gap = df_latest["UNEMPLOYMENT_RATE"].max() - df_latest["UNEMPLOYMENT_RATE"].min()

        c1, c2, c3 = st.columns(3)
        with c1:
            top = df_latest.iloc[0]
            st.metric("Highest", f"{top['STATE_NAME']}", f"{top['UNEMPLOYMENT_RATE']:.1f}%")
        with c2:
            bottom = df_latest.iloc[-1]
            st.metric("Lowest", f"{bottom['STATE_NAME']}", f"{bottom['UNEMPLOYMENT_RATE']:.1f}%")
        with c3:
            st.metric("State Gap", f"{gap:.1f} pp", "Max - Min spread")
        st.caption(f"As of {latest_date.strftime('%B %Y')}. Visit **Labor & Employment** for state comparisons.")

st.info(
    "💡 Use **AI Advisor** to ask questions about these indicators, or check **My Watchlist** "
    "to track specific states, companies, or indicators with alerts and notes."
)
