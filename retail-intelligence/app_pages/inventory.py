"""
app_pages/inventory.py

Inventory page — product stock monitoring, low-stock alerts,
and full inventory table. No country filter (inventory is global).
"""

import streamlit as st
from utils.queries import get_inventory

LOW_STOCK_THRESHOLD = 100

st.caption("Monitor product stock levels and identify items that need restocking.")

st.divider()

# ── Load inventory ────────────────────────────────────────────────────────────
try:
    inv_df = get_inventory()
except Exception as e:
    st.error(f"Could not load inventory data: {e}")
    st.stop()

if inv_df.empty:
    st.warning("No inventory data available.")
    st.stop()

low_stock_df = inv_df[inv_df["STOCK"] < LOW_STOCK_THRESHOLD]

# ── Inventory KPIs ────────────────────────────────────────────────────────────
total_products = len(inv_df)
total_units = int(inv_df["STOCK"].sum())
low_stock_count = len(low_stock_df)

with st.container(horizontal=True):
    st.metric(
        label=":material/inventory_2: Total products",
        value=f"{total_products:,}",
        border=True,
    )
    st.metric(
        label=":material/warehouse: Units in stock",
        value=f"{total_units:,}",
        border=True,
    )
    st.metric(
        label=":material/warning: Low-stock products",
        value=f"{low_stock_count}",
        border=True,
    )

st.divider()

# ── Low-stock alert ───────────────────────────────────────────────────────────
if low_stock_count > 0:
    st.warning(
        f"**{low_stock_count} product{'s' if low_stock_count > 1 else ''} "
        f"{'are' if low_stock_count > 1 else 'is'} below {LOW_STOCK_THRESHOLD} units.** "
        f"Review and consider restocking.",
        icon=":material/warning:",
    )

    st.subheader(":material/priority_high: Low-stock products")

    with st.container(border=True):
        display_low = low_stock_df[["PRODUCT", "CATEGORY", "PRICE", "STOCK"]].copy()
        display_low.columns = ["Product", "Category", "Price", "Stock"]
        display_low["Price"] = display_low["Price"].map("${:,.2f}".format)
        st.dataframe(display_low, hide_index=True)

    st.divider()
else:
    st.success(
        "All products are adequately stocked.",
        icon=":material/check_circle:",
    )
    st.divider()

# ── Full inventory table ───────────────────────────────────────────────────────
st.subheader(":material/table_rows: Full inventory")

st.caption(
    f"Sorted by stock level (lowest first). "
    f"Items below {LOW_STOCK_THRESHOLD} units are highlighted."
)

with st.container(border=True):
    display_inv = inv_df[["PRODUCT", "CATEGORY", "PRICE", "STOCK"]].copy()
    display_inv.columns = ["Product", "Category", "Price", "Stock"]
    display_inv["Price"] = display_inv["Price"].map("${:,.2f}".format)

    st.dataframe(
        display_inv,
        hide_index=True,
        column_config={
            "Stock": st.column_config.NumberColumn(
                "Stock",
                help=f"Units available. Items below {LOW_STOCK_THRESHOLD} need attention.",
                format="%d",
            ),
        },
    )
