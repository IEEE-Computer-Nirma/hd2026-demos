"""
app_pages/ai_advisor.py

AI Advisor page — Snowflake Cortex-powered business analysis.
Uses SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', ...) to answer
natural language questions grounded in live Snowflake data.
"""

import streamlit as st
from utils.queries import get_filter_options, build_cortex_context, run_cortex_query

# ── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Context filters")
    st.caption("Filter the data context that the AI receives.")

    try:
        opts = get_filter_options()
        countries = ["All"] + opts["countries"]
        categories = ["All"] + opts["categories"]
    except Exception as e:
        st.error(f"Could not load filter options: {e}")
        countries, categories = ["All"], ["All"]

    country = st.selectbox(
        ":material/public: Country",
        countries,
        key="ai_country",
    )
    category = st.selectbox(
        ":material/inventory_2: Category",
        categories,
        key="ai_category",
    )

    if country != "All" or category != "All":
        st.info(
            f"AI context: **{country}** · **{category}**",
            icon=":material/filter_alt:",
        )
    else:
        st.info("AI context: all markets and categories.", icon=":material/public:")

# ── Page header ──────────────────────────────────────────────────────────────
st.caption(
    "Ask questions about sales, customers, products, and inventory. "
    "The AI uses live Snowflake data as its knowledge base."
)

st.divider()

# ── Example questions ─────────────────────────────────────────────────────────
st.markdown("**Example questions**")

example_questions = [
    "Which product performs best?",
    "Who is our best customer?",
    "Which category should we focus on?",
    "Which products have low inventory?",
    "Which category generates the most revenue?",
]

selected_example = st.pills(
    "Quick start",
    example_questions,
    label_visibility="collapsed",
    key="ai_example_pills",
)

st.divider()

# ── Question input ────────────────────────────────────────────────────────────
default_text = selected_example if selected_example else ""

with st.form("ai_question_form"):
    question = st.text_input(
        "Your question",
        value=default_text,
        placeholder="Which product performs best in this market?",
        label_visibility="visible",
    )
    submitted = st.form_submit_button(
        ":material/send: Ask AI",
        type="primary",
    )

# ── Cortex response ───────────────────────────────────────────────────────────
if submitted and question.strip():

    with st.spinner("Querying Snowflake Cortex..."):
        try:
            context = build_cortex_context(country, category)
        except Exception as e:
            st.error(f"Could not retrieve business data from Snowflake: {e}")
            st.stop()

        prompt = f"""You are an AI retail business analyst.

You are helping a retail manager make data-driven decisions using Snowflake data.

Use ONLY the business data provided below. Do not invent products, customers,
sales figures, or inventory information. If the data is insufficient to answer
the question, say so clearly.

BUSINESS DATA
-------------
{context}

USER QUESTION
-------------
{question}

INSTRUCTIONS
------------
1. Answer the question directly and concisely.
2. Reference actual numbers from the data when relevant.
3. Do not fabricate any information not present in the data.
4. If the data does not contain enough information to answer, say so.
5. Offer practical business recommendations where appropriate.
6. Write in plain, clear business prose — no Markdown, no bullet points,
   no headers, no special formatting characters.
7. Write currency amounts with a dollar sign followed by the number,
   for example: dollar sign 299.98 (write it out in full as plain text,
   not as a special character). Use words like "USD 299.98" or
   "299.98 dollars" to avoid formatting issues.
8. Keep paragraphs short and separated by blank lines.
"""

        try:
            row = run_cortex_query(
                "SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', %s) AS RESPONSE",
                (prompt,),
            )
            response = row[0]
        except Exception as e:
            st.error(f"Snowflake Cortex returned an error: {e}")
            st.stop()

    st.subheader(":material/smart_toy: AI analysis")
    with st.container(border=True):
        # Escape $ so Streamlit's markdown/LaTeX renderer does not
        # interpret currency amounts as math delimiters.
        safe_response = response.replace("$", r"\$")
        st.markdown(safe_response)

    with st.expander(":material/database: Data context sent to AI", expanded=False):
        st.code(context, language="text")

elif submitted and not question.strip():
    st.warning("Please enter a question before submitting.", icon=":material/warning:")
