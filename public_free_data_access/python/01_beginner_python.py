# ================================================================
# 01 BEGINNER: Exploring Datasets with Python & Pandas
# ================================================================
# Skills: read CSV, df.head(), df.info(), filtering, value_counts,
#         basic bar chart with matplotlib
# ================================================================

import pandas as pd

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION A: Load and inspect the US Macro Monthly CSV
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

macro = pd.read_csv("public_free_data_access/data/us_macro_monthly.csv", parse_dates=["DATE"])

# A1. First 10 rows
print("=== US MACRO MONTHLY (first 10 rows) ===")
print(macro.head(10).to_string(index=False))

# A2. Shape and column types
print(f"\nShape: {macro.shape[0]} rows x {macro.shape[1]} columns")
print(f"\nColumn types:\n{macro.dtypes}")

# A3. Summary statistics
print("\n=== Summary Statistics ===")
print(macro.describe().round(2).to_string())


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION B: Load and inspect the TPC-H Orders CSV
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

orders = pd.read_csv("public_free_data_access/data/tpch_orders_enriched.csv", parse_dates=["O_ORDERDATE"])

print("\n=== TPC-H ORDERS (first 10 rows) ===")
print(orders.head(10).to_string(index=False))

print(f"\nShape: {orders.shape[0]} rows x {orders.shape[1]} columns")
print(f"\nColumn types:\n{orders.dtypes}")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION C: Filtering rows
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# C1. Macro data from 2022 onward
recent_macro = macro[macro["DATE"] >= "2022-01-01"]
print(f"\n=== Macro rows from 2022+: {len(recent_macro)} rows ===")
print(recent_macro.head(5).to_string(index=False))

# C2. High-value orders (> $200,000)
big_orders = orders[orders["O_TOTALPRICE"] > 200000]
print(f"\n=== Orders > $200k: {len(big_orders)} of {len(orders)} ===")
print(big_orders.head(5).to_string(index=False))

# C3. Orders from a specific region
europe_orders = orders[orders["REGION"] == "EUROPE"]
print(f"\n=== European orders: {len(europe_orders)} ===")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION D: Counting and grouping
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# D1. Orders by region
print("\n=== Orders by Region ===")
print(orders["REGION"].value_counts().to_string())

# D2. Orders by market segment
print("\n=== Orders by Market Segment ===")
print(orders["MARKET_SEGMENT"].value_counts().to_string())

# D3. Orders by priority
print("\n=== Orders by Priority ===")
print(orders["O_ORDERPRIORITY"].value_counts().to_string())


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION E: Basic sorting
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# E1. Top 10 most expensive orders
print("\n=== Top 10 Most Expensive Orders ===")
top_orders = orders.nlargest(10, "O_TOTALPRICE")[["O_ORDERKEY", "O_TOTALPRICE", "CUSTOMER_NAME", "NATION"]]
print(top_orders.to_string(index=False))

# E2. Months with highest inflation
print("\n=== Top 10 Highest Inflation Months ===")
top_inflation = macro.nlargest(10, "YOY_INFLATION_PCT")[["DATE", "CPI_INDEX", "YOY_INFLATION_PCT"]]
print(top_inflation.to_string(index=False))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SECTION F: Simple visualization
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# F1. CPI over time
axes[0].plot(macro["DATE"], macro["CPI_INDEX"], color="steelblue", linewidth=1.5)
axes[0].set_title("US CPI Index (2015-Present)")
axes[0].set_ylabel("CPI Index")
axes[0].grid(True, alpha=0.3)

# F2. Orders by region (bar chart)
region_counts = orders["REGION"].value_counts()
axes[1].bar(region_counts.index, region_counts.values, color="coral")
axes[1].set_title("TPC-H Orders by Region")
axes[1].set_ylabel("Order Count")

plt.tight_layout()
plt.savefig("public_free_data_access/data/01_beginner_charts.png", dpi=100)
plt.show()
print("\nChart saved to public_free_data_access/data/01_beginner_charts.png")
