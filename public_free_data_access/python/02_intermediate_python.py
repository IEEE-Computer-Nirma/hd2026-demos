# ================================================================
# 02 INTERMEDIATE: Single-Dataset Analysis & Snowpark
# ================================================================
# Skills: Snowpark session, DataFrame ops, pandas time-series,
#         rolling averages, YoY calculations, window functions,
#         multi-panel plots
# ================================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from snowflake.snowpark.context import get_active_session

session = get_active_session()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION A: Snowpark — Querying BLS Price Data
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# A1. Read CPI data directly from Snowflake via Snowpark
cpi_df = session.sql("""
    SELECT DATE, VALUE AS CPI_INDEX, VARIABLE_NAME
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
    WHERE VARIABLE_NAME = 'CPI: All items, Not seasonally adjusted, Monthly'
      AND GEO_ID = 'country/USA'
      AND DATE >= '2015-01-01'
    ORDER BY DATE
""").to_pandas()

cpi_df["DATE"] = pd.to_datetime(cpi_df["DATE"])
print(f"CPI data: {len(cpi_df)} rows, {cpi_df['DATE'].min()} to {cpi_df['DATE'].max()}")
print(cpi_df.head(5).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION B: Snowpark — House Price Index
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

hpi_df = session.sql("""
    SELECT DATE, VALUE AS HPI
    FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FHFA_HOUSE_PRICE_TIMESERIES
    WHERE VARIABLE_NAME = 'FHFA_HPI traditional purchase-only monthly Seasonally Adjusted'
      AND GEO_ID = 'country/USA'
      AND DATE >= '2015-01-01'
    ORDER BY DATE
""").to_pandas()

hpi_df["DATE"] = pd.to_datetime(hpi_df["DATE"])
print(f"\nHouse Price data: {len(hpi_df)} rows")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION C: Pandas — YoY Inflation Calculation
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cpi_df = cpi_df.sort_values("DATE").reset_index(drop=True)
cpi_df["CPI_12M_AGO"] = cpi_df["CPI_INDEX"].shift(12)
cpi_df["YOY_INFLATION"] = ((cpi_df["CPI_INDEX"] - cpi_df["CPI_12M_AGO"])
                            / cpi_df["CPI_12M_AGO"] * 100).round(2)

print("\n=== YoY Inflation (last 12 months) ===")
print(cpi_df[["DATE", "CPI_INDEX", "YOY_INFLATION"]].tail(12).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION D: Pandas — Rolling Averages on House Prices
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

hpi_df = hpi_df.sort_values("DATE").reset_index(drop=True)
hpi_df["HPI_3M_AVG"] = hpi_df["HPI"].rolling(3).mean().round(2)
hpi_df["HPI_12M_AVG"] = hpi_df["HPI"].rolling(12).mean().round(2)
hpi_df["MOM_CHANGE"] = hpi_df["HPI"].pct_change().mul(100).round(2)

print("\n=== House Prices with Rolling Averages (last 12 months) ===")
print(hpi_df[["DATE", "HPI", "HPI_3M_AVG", "HPI_12M_AVG", "MOM_CHANGE"]].tail(12).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION E: Snowpark — TPC-H Revenue by Region & Month
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

revenue_df = session.sql("""
    SELECT
        DATE_TRUNC('month', o.O_ORDERDATE) AS ORDER_MONTH,
        r.R_NAME AS REGION,
        COUNT(*) AS ORDER_COUNT,
        SUM(o.O_TOTALPRICE) AS REVENUE
    FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS o
    JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
    JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
    JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.REGION r ON n.N_REGIONKEY = r.R_REGIONKEY
    GROUP BY ORDER_MONTH, r.R_NAME
    ORDER BY ORDER_MONTH, r.R_NAME
""").to_pandas()

revenue_df["ORDER_MONTH"] = pd.to_datetime(revenue_df["ORDER_MONTH"])
print(f"\n=== Revenue by Region: {len(revenue_df)} rows ===")
print(revenue_df.head(10).to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION F: Pandas — Pivot table & window-style operations
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Pivot: regions as columns, months as rows
pivot = revenue_df.pivot_table(
    index="ORDER_MONTH", columns="REGION", values="REVENUE", aggfunc="sum"
)

# Month-over-month growth per region
growth = pivot.pct_change().mul(100).round(2)
print("\n=== MoM Revenue Growth by Region (last 6 months) ===")
print(growth.tail(6).to_string())


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION G: Visualization — Multi-panel macro dashboard
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=False)

# G1. CPI Index with rolling average
axes[0].plot(cpi_df["DATE"], cpi_df["CPI_INDEX"], color="steelblue", linewidth=1.2, label="CPI Index")
axes[0].set_title("US CPI Index (Monthly)")
axes[0].set_ylabel("Index Value")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# G2. YoY Inflation rate
valid_inflation = cpi_df.dropna(subset=["YOY_INFLATION"])
colors = ["crimson" if v > 3 else "steelblue" for v in valid_inflation["YOY_INFLATION"]]
axes[1].bar(valid_inflation["DATE"], valid_inflation["YOY_INFLATION"], color=colors, width=25)
axes[1].axhline(y=2, color="green", linestyle="--", alpha=0.7, label="2% Target")
axes[1].set_title("Year-over-Year Inflation Rate")
axes[1].set_ylabel("Inflation %")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# G3. House Price Index with moving averages
axes[2].plot(hpi_df["DATE"], hpi_df["HPI"], color="coral", linewidth=1.2, label="HPI")
axes[2].plot(hpi_df["DATE"], hpi_df["HPI_12M_AVG"], color="navy", linewidth=1.5,
             linestyle="--", label="12M Avg")
axes[2].set_title("FHFA House Price Index (Purchase-Only, SA)")
axes[2].set_ylabel("Index Value")
axes[2].legend()
axes[2].grid(True, alpha=0.3)

for ax in axes:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator())

plt.tight_layout()
plt.savefig("public_free_data_access/data/02_intermediate_dashboard.png", dpi=120)
plt.show()
print("\nDashboard saved to public_free_data_access/data/02_intermediate_dashboard.png")
