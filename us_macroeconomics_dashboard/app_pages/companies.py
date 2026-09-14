"""Company directory: browse the public Company Index."""

import streamlit as st

from utils.db import load_exchanges, search_companies

st.title("Corporate intelligence & entity search")
st.caption("Data source: Snowflake Public Data Company Index (SEC EDGAR, LEI, PermID, OpenFIGI)")

exchanges = load_exchanges()

search_c1, search_c2, search_c3 = st.columns([2, 1, 1])
with search_c1:
    search_query = st.text_input("Search company name, ticker, or CIK", placeholder="e.g. Apple, MSFT, NVDA...")
with search_c2:
    selected_exchange = st.selectbox("Exchange venue", options=exchanges)
with search_c3:
    max_rows = st.number_input("Max results", min_value=10, max_value=200, value=50, step=10)

with st.spinner("Searching company entities..."):
    df_companies = search_companies(search_query, selected_exchange, limit=int(max_rows))

st.markdown(f"**{len(df_companies)} entities** matching criteria")
st.dataframe(df_companies, use_container_width=True, hide_index=True)

if not df_companies.empty:
    csv = df_companies.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download results as CSV",
        data=csv,
        file_name="snowflake_company_index_export.csv",
        mime="text/csv",
        icon=":material/download:",
    )
