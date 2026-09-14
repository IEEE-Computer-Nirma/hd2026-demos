# ================================================================
# 03 ADVANCED: Cross-Dataset Analysis & Composite Indicators
# ================================================================
# Skills: Multi-source Snowpark queries, pandas merge, correlation
#         matrix, composite scoring, regime detection, multi-panel
#         matplotlib dashboard
# ================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from snowflake.snowpark.context import get_active_session

session = get_active_session()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION A: Pull multiple macro datasets from Snowflake
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# A1. CPI (inflation proxy)
cpi = session.sql("""
    SELECT DATE, VALUE AS CPI_INDEX
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
    WHERE VARIABLE_NAME = 'CPI: All items, Not seasonally adjusted, Monthly'
      AND GEO_ID = 'country/USA'
      AND DATE >= '2010-01-01'
    ORDER BY DATE
""").to_pandas()
cpi["DATE"] = pd.to_datetime(cpi["DATE"])

# A2. House Price Index
hpi = session.sql("""
    SELECT DATE, VALUE AS HPI
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
    WHERE VARIABLE_NAME = 'FHFA_HPI traditional purchase-only monthly Seasonally Adjusted'
      AND GEO_ID = 'country/USA'
      AND DATE >= '2010-01-01'
    ORDER BY DATE
""").to_pandas()
hpi["DATE"] = pd.to_datetime(hpi["DATE"])

# A3. State-level unemployment (aggregate to national average)
unemployment = session.sql("""
    SELECT DATE, AVG(VALUE) AS AVG_UNEMPLOYMENT_RATE
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES
    WHERE VARIABLE_NAME = 'Local Area Unemployment: Unemployment Rate, Seasonally adjusted, Monthly'
      AND DATE >= '2010-01-01'
    GROUP BY DATE
    ORDER BY DATE
""").to_pandas()
unemployment["DATE"] = pd.to_datetime(unemployment["DATE"])

print(f"CPI: {len(cpi)} rows | HPI: {len(hpi)} rows | Unemployment: {len(unemployment)} rows")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION B: Merge into a single macro panel
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

macro = (cpi.merge(hpi, on="DATE", how="outer")
            .merge(unemployment, on="DATE", how="outer")
            .sort_values("DATE")
            .reset_index(drop=True))

# Derived features
macro["CPI_YOY"] = macro["CPI_INDEX"].pct_change(12).mul(100).round(2)
macro["HPI_YOY"] = macro["HPI"].pct_change(12).mul(100).round(2)
macro["UE_CHANGE_12M"] = macro["AVG_UNEMPLOYMENT_RATE"] - macro["AVG_UNEMPLOYMENT_RATE"].shift(12)

print(f"\n=== Merged Macro Panel: {len(macro)} rows ===")
print(macro.dropna().tail(12).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION C: Correlation Matrix
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

corr_cols = ["CPI_INDEX", "CPI_YOY", "HPI", "HPI_YOY", "AVG_UNEMPLOYMENT_RATE"]
corr = macro[corr_cols].dropna().corr().round(3)

print("\n=== Correlation Matrix ===")
print(corr.to_string())


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION D: Economic Regime Detection
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def classify_regime(row):
    if pd.isna(row["CPI_YOY"]) or pd.isna(row["AVG_UNEMPLOYMENT_RATE"]):
        return "UNKNOWN"
    if row["CPI_YOY"] > 4 and row["AVG_UNEMPLOYMENT_RATE"] > 6:
        return "STAGFLATION"
    if row["CPI_YOY"] > 4:
        return "OVERHEATING"
    if row["AVG_UNEMPLOYMENT_RATE"] > 6:
        return "RECESSION"
    if row["CPI_YOY"] < 2 and row["AVG_UNEMPLOYMENT_RATE"] < 5:
        return "GOLDILOCKS"
    return "NORMAL"

macro["REGIME"] = macro.apply(classify_regime, axis=1)

print("\n=== Economic Regime Distribution ===")
print(macro["REGIME"].value_counts().to_string())

# Show regime transitions
regime_changes = macro[macro["REGIME"] != macro["REGIME"].shift(1)].dropna(subset=["REGIME"])
print("\n=== Regime Transitions (last 10) ===")
print(regime_changes[["DATE", "REGIME", "CPI_YOY", "AVG_UNEMPLOYMENT_RATE"]].tail(10).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION E: Composite Economic Health Score (0-100)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def normalize(series, lower_is_better=False):
    s_min, s_max = series.min(), series.max()
    if s_max == s_min:
        return pd.Series(50, index=series.index)
    normed = (series - s_min) / (s_max - s_min)
    if lower_is_better:
        normed = 1 - normed
    return normed

scored = macro.dropna(subset=["CPI_YOY", "HPI_YOY", "AVG_UNEMPLOYMENT_RATE"]).copy()
scored["UE_SCORE"] = normalize(scored["AVG_UNEMPLOYMENT_RATE"], lower_is_better=True) * 40
scored["INF_SCORE"] = normalize(scored["CPI_YOY"].abs(), lower_is_better=True) * 30
scored["HPI_SCORE"] = normalize(scored["HPI_YOY"].clip(-5, 15)) * 30

scored["HEALTH_SCORE"] = (scored["UE_SCORE"] + scored["INF_SCORE"] + scored["HPI_SCORE"]).round(1)

print("\n=== Economic Health Score (last 12 months) ===")
print(scored[["DATE", "HEALTH_SCORE", "AVG_UNEMPLOYMENT_RATE", "CPI_YOY", "HPI_YOY"]].tail(12).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION F: Cross-dataset — TPC-H + Global Emissions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Revenue by nation from TPC-H
nation_revenue = session.sql("""
    SELECT
        n.N_NAME AS NATION,
        r.R_NAME AS REGION,
        SUM(o.O_TOTALPRICE) AS TOTAL_REVENUE,
        COUNT(*) AS ORDER_COUNT
    FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS o
    JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
    JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
    JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.REGION r ON n.N_REGIONKEY = r.R_REGIONKEY
    GROUP BY n.N_NAME, r.R_NAME
    ORDER BY TOTAL_REVENUE DESC
""").to_pandas()

# CO2 emissions by country
emissions = session.sql("""
    SELECT
        GEO_ID,
        SUM(VALUE) AS TOTAL_EMISSIONS
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.CLIMATE_WATCH_TIMESERIES
    WHERE VARIABLE_NAME ILIKE '%Total GHG%'
      AND DATE >= '2018-01-01'
    GROUP BY GEO_ID
    ORDER BY TOTAL_EMISSIONS DESC
    LIMIT 25
""").to_pandas()

print("\n=== TPC-H Revenue by Nation (Top 10) ===")
print(nation_revenue.head(10).to_string(index=False))

print("\n=== CO2 Emissions (Top 10) ===")
print(emissions.head(10).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION G: Grand Dashboard — 6-panel visualization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

fig, axes = plt.subplots(3, 2, figsize=(18, 16))

# G1. CPI + YoY Inflation
ax = axes[0, 0]
ax.plot(macro["DATE"], macro["CPI_INDEX"], color="steelblue", linewidth=1.2)
ax.set_title("CPI Index")
ax.set_ylabel("Index")
ax.grid(True, alpha=0.3)

ax = axes[0, 1]
valid = macro.dropna(subset=["CPI_YOY"])
colors = ["crimson" if v > 3 else "forestgreen" if v < 2 else "steelblue" for v in valid["CPI_YOY"]]
ax.bar(valid["DATE"], valid["CPI_YOY"], color=colors, width=25)
ax.axhline(y=2, color="black", linestyle="--", alpha=0.5, label="2% Target")
ax.set_title("YoY Inflation Rate")
ax.set_ylabel("%")
ax.legend()
ax.grid(True, alpha=0.3)

# G2. House Prices + YoY Growth
ax = axes[1, 0]
ax.plot(macro["DATE"], macro["HPI"], color="coral", linewidth=1.2)
ax.set_title("House Price Index (FHFA)")
ax.set_ylabel("Index")
ax.grid(True, alpha=0.3)

ax = axes[1, 1]
valid_hpi = macro.dropna(subset=["HPI_YOY"])
ax.fill_between(valid_hpi["DATE"], 0, valid_hpi["HPI_YOY"],
                where=valid_hpi["HPI_YOY"] > 0, color="coral", alpha=0.5, label="Growth")
ax.fill_between(valid_hpi["DATE"], 0, valid_hpi["HPI_YOY"],
                where=valid_hpi["HPI_YOY"] <= 0, color="steelblue", alpha=0.5, label="Decline")
ax.set_title("House Price YoY Growth")
ax.set_ylabel("%")
ax.legend()
ax.grid(True, alpha=0.3)

# G3. Unemployment + Health Score
ax = axes[2, 0]
ax.plot(macro["DATE"], macro["AVG_UNEMPLOYMENT_RATE"], color="darkred", linewidth=1.2)
ax.set_title("Avg State Unemployment Rate")
ax.set_ylabel("Rate %")
ax.grid(True, alpha=0.3)

ax = axes[2, 1]
ax.plot(scored["DATE"], scored["HEALTH_SCORE"], color="navy", linewidth=1.5)
ax.axhline(y=50, color="gray", linestyle="--", alpha=0.5)
ax.fill_between(scored["DATE"], 0, scored["HEALTH_SCORE"],
                where=scored["HEALTH_SCORE"] >= 50, color="forestgreen", alpha=0.2)
ax.fill_between(scored["DATE"], 0, scored["HEALTH_SCORE"],
                where=scored["HEALTH_SCORE"] < 50, color="crimson", alpha=0.2)
ax.set_title("Composite Economic Health Score (0-100)")
ax.set_ylabel("Score")
ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3)

for row in axes:
    for ax in row:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))

plt.suptitle("US Macro Observatory — Cross-Dataset Dashboard", fontsize=16, y=1.01)
plt.tight_layout()
plt.savefig("public_free_data_access/data/03_advanced_dashboard.png", dpi=120, bbox_inches="tight")
plt.show()
print("\nDashboard saved to public_free_data_access/data/03_advanced_dashboard.png")
