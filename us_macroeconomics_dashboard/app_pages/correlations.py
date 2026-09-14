"""Cross-domain correlation — explore relationships between macro indicators."""

import pandas as pd
import streamlit as st

from utils.db import get_conn

PUBLIC_DATA = "SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE"

st.title("Cross-domain correlation analysis")
st.caption("Explore how unemployment, inflation, and housing prices move together over time")

start_date = st.session_state.get("start_date", "2021-01-01")


@st.cache_data(ttl=3600)
def load_macro_monthly(start_date: str):
    sql = f"""
    WITH unemp AS (
        SELECT t.DATE,
               ROUND(AVG(t.VALUE * 100), 2) AS UNEMPLOYMENT_RATE
        FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES t
        JOIN {PUBLIC_DATA}.GEOGRAPHY_INDEX g ON t.GEO_ID = g.GEO_ID
        WHERE g.LEVEL = 'State'
          AND t.VARIABLE = 'Local_Area_Unemployment:_Unemployment_Rate,_Seasonally_adjusted,_Monthly'
          AND t.VALUE IS NOT NULL
          AND t.DATE >= ?
        GROUP BY t.DATE
    ),
    cpi AS (
        SELECT DATE, VALUE AS CPI_INDEX
        FROM {PUBLIC_DATA}.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'CPI:_All_items,_Seasonally_adjusted,_Monthly'
          AND VALUE IS NOT NULL
          AND DATE >= ?
    ),
    hpi AS (
        SELECT DATE, VALUE AS HPI_INDEX
        FROM {PUBLIC_DATA}.FHFA_HOUSE_PRICE_TIMESERIES
        WHERE GEO_ID = 'country/USA'
          AND VARIABLE = 'FHFA_HPI_traditional_purchase-only_monthly_SA'
          AND VALUE IS NOT NULL
          AND DATE >= ?
    )
    SELECT u.DATE,
           u.UNEMPLOYMENT_RATE,
           c.CPI_INDEX,
           h.HPI_INDEX
    FROM unemp u
    LEFT JOIN cpi c ON u.DATE = c.DATE
    LEFT JOIN hpi h ON u.DATE = h.DATE
    ORDER BY u.DATE
    """
    return get_conn().query(sql, params=[start_date, start_date, start_date])


def _lead_lag_correlation(series_a: pd.Series, series_b: pd.Series, max_lag: int = 12) -> pd.DataFrame:
    rows = []
    for lag in range(-max_lag, max_lag + 1):
        aligned = pd.concat([series_a, series_b.shift(lag)], axis=1).dropna()
        if len(aligned) < 12:
            continue
        r = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        rows.append({"lag": lag, "correlation": r})
    return pd.DataFrame(rows)


with st.spinner("Loading cross-domain data..."):
    df = load_macro_monthly(start_date)

if df.empty:
    st.warning("No data available for the selected timeframe.", icon=":material/warning:")
else:
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df.set_index("DATE")

    df["CPI_YOY_PCT"] = df["CPI_INDEX"].pct_change(periods=12) * 100
    df["HPI_YOY_PCT"] = df["HPI_INDEX"].pct_change(periods=12) * 100
    df["UNEMP_CHANGE_YOY"] = df["UNEMPLOYMENT_RATE"] - df["UNEMPLOYMENT_RATE"].shift(12)

    df_clean = df.dropna()

    # ----- Dual-axis comparison -----
    st.subheader("Indicator comparison", anchor=False)
    INDICATORS = {
        "Unemployment rate (%)": "UNEMPLOYMENT_RATE",
        "CPI index level": "CPI_INDEX",
        "CPI YoY inflation (%)": "CPI_YOY_PCT",
        "Home price index": "HPI_INDEX",
        "HPI YoY change (%)": "HPI_YOY_PCT",
    }

    c1, c2 = st.columns(2)
    with c1:
        left_label = st.selectbox("Left axis", list(INDICATORS.keys()), index=0)
    with c2:
        right_label = st.selectbox(
            "Right axis",
            [k for k in INDICATORS.keys() if k != left_label],
            index=1,
        )

    left_col = INDICATORS[left_label]
    right_col = INDICATORS[right_label]

    chart_df = df_clean[[left_col, right_col]].rename(
        columns={left_col: left_label, right_col: right_label}
    )
    st.line_chart(chart_df, use_container_width=True)

    # ----- Correlation matrix -----
    st.subheader("Pearson correlation matrix", anchor=False)
    st.caption("Based on monthly aligned data")

    corr_cols = ["UNEMPLOYMENT_RATE", "CPI_INDEX", "HPI_INDEX"]
    available = [c for c in corr_cols if c in df_clean.columns]
    if len(available) >= 2:
        corr_matrix = df_clean[available].corr()
        corr_display = corr_matrix.rename(
            columns={"UNEMPLOYMENT_RATE": "Unemployment", "CPI_INDEX": "CPI", "HPI_INDEX": "HPI"},
            index={"UNEMPLOYMENT_RATE": "Unemployment", "CPI_INDEX": "CPI", "HPI_INDEX": "HPI"},
        )
        st.dataframe(
            corr_display.style.format("{:.3f}"),
            use_container_width=True,
        )

        interpretations = []
        if "UNEMPLOYMENT_RATE" in available and "CPI_INDEX" in available:
            r = corr_matrix.loc["UNEMPLOYMENT_RATE", "CPI_INDEX"]
            if r < -0.3:
                interpretations.append(
                    f"Unemployment & CPI are **negatively correlated** (r={r:.2f}) — "
                    "consistent with the Phillips Curve."
                )
            elif r > 0.3:
                interpretations.append(
                    f"Unemployment & CPI are **positively correlated** (r={r:.2f}) — "
                    "unusual pattern suggesting possible stagflationary dynamics."
                )

        if "CPI_INDEX" in available and "HPI_INDEX" in available:
            r = corr_matrix.loc["CPI_INDEX", "HPI_INDEX"]
            if r > 0.7:
                interpretations.append(
                    f"CPI & Housing are **strongly correlated** (r={r:.2f}) — "
                    "housing costs are a major driver of overall inflation."
                )

        if interpretations:
            with st.container(border=True):
                st.markdown("**Correlation insights**")
                for interp in interpretations:
                    st.markdown(f"- {interp}")

    # ----- Lead-lag analysis -----
    st.subheader("Lead-lag analysis", anchor=False)
    st.caption(
        "Does a change in one indicator predict a later change in another? "
        "Correlation computed across a ±12 month shift window."
    )

    LAG_INDICATORS = {
        "Unemployment rate (%)": "UNEMPLOYMENT_RATE",
        "CPI YoY inflation (%)": "CPI_YOY_PCT",
        "HPI YoY change (%)": "HPI_YOY_PCT",
    }
    lag_available = {k: v for k, v in LAG_INDICATORS.items() if v in df_clean.columns}

    if len(lag_available) >= 2:
        lc1, lc2 = st.columns(2)
        with lc1:
            lead_label = st.selectbox("Leading indicator", list(lag_available.keys()), index=0, key="lead_sel")
        with lc2:
            lag_label = st.selectbox(
                "Lagging indicator",
                [k for k in lag_available.keys() if k != lead_label],
                index=0,
                key="lag_sel",
            )

        lead_col = lag_available[lead_label]
        lag_col = lag_available[lag_label]

        lag_df = _lead_lag_correlation(df_clean[lead_col], df_clean[lag_col], max_lag=12)

        if not lag_df.empty:
            chart_lag = lag_df.set_index("lag")
            st.bar_chart(chart_lag, use_container_width=True)

            best_row = lag_df.loc[lag_df["correlation"].abs().idxmax()]
            best_lag = int(best_row["lag"])
            best_r = best_row["correlation"]

            with st.container(border=True):
                st.markdown("**Lead-lag insight**")
                if best_lag == 0:
                    st.markdown(
                        f"Strongest relationship (r={best_r:.2f}) is **contemporaneous** — "
                        f"**{lead_label}** and **{lag_label}** move together in the same month."
                    )
                elif best_lag > 0:
                    st.markdown(
                        f"**{lead_label}** leads **{lag_label}** by **{best_lag} month(s)** "
                        f"(r={best_r:.2f})."
                    )
                else:
                    st.markdown(
                        f"**{lag_label}** leads **{lead_label}** by **{abs(best_lag)} month(s)** "
                        f"(r={best_r:.2f})."
                    )
                st.caption("Correlation, not causation — reflects historical co-movement only.")
        else:
            st.caption("Not enough overlapping history for the selected timeframe.")
    else:
        st.caption("Select a longer timeframe to enable lead-lag analysis.")

    # ----- YoY overlay -----
    st.subheader("Year-over-year changes (normalized view)", anchor=False)
    yoy_cols = ["CPI_YOY_PCT", "HPI_YOY_PCT", "UNEMP_CHANGE_YOY"]
    available_yoy = [c for c in yoy_cols if c in df_clean.columns]
    if available_yoy:
        yoy_chart = df_clean[available_yoy].rename(columns={
            "CPI_YOY_PCT": "CPI inflation %",
            "HPI_YOY_PCT": "Housing price change %",
            "UNEMP_CHANGE_YOY": "Unemployment change (pp)",
        })
        st.line_chart(yoy_chart, use_container_width=True)
        st.caption("All series show year-over-year changes for fair cross-scale comparison.")

    with st.expander("View aligned monthly data", icon=":material/table_chart:"):
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
