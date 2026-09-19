"""
LLM Chat Lab — Plug-and-play chat with Llama via Snowflake Cortex.
"""

import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="LLM Chat Lab", page_icon="*", layout="centered")

session = get_active_session()

MODEL = "llama3.1-70b"
MAX_HISTORY = 20

SYSTEM_PROMPT = (
    "You are a helpful, concise assistant. "
    "You have deep knowledge of data engineering, analytics, and Snowflake. "
    "Answer clearly and keep responses short unless asked for detail."
)


def call_llama(messages: list[dict]) -> str:
    """Call Snowflake Cortex COMPLETE with conversation history."""
    import json

    prompt_obj = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    prompt_json = json.dumps(prompt_obj).replace("'", "\\'")

    sql = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{MODEL}',
            PARSE_JSON($${prompt_json}$$),
            {{}}
        ) AS response
    """
    result = session.sql(sql).collect()
    if not result:
        return "No response received."

    resp = json.loads(result[0]["RESPONSE"])
    return resp.get("choices", [{}])[0].get("messages", resp.get("choices", [{}])[0].get("message", ""))


# --- Session state ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Header ---
st.title("LLM Chat Lab")
st.caption(f"Model: `{MODEL}` | Powered by Snowflake Cortex")

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")

    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
    max_tokens = st.select_slider(
        "Max tokens", options=[256, 512, 1024, 2048, 4096], value=1024
    )

    st.divider()

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.markdown("### Quick prompts")
    quick_prompts = [
        "Explain Snowflake Cortex in 3 sentences",
        "What is a Random Forest classifier?",
        "Write a SQL query to find top 10 customers by spend",
        "Explain the difference between COMPLETE and AGENT_RUN",
    ]
    for qp in quick_prompts:
        if st.button(qp, use_container_width=True, key=f"qp_{qp[:20]}"):
            st.session_state.messages.append({"role": "user", "content": qp})
            st.rerun()

# --- Chat history ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Input ---
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            import json

            history = st.session_state.messages[-MAX_HISTORY:]
            prompt_obj = [{"role": "system", "content": SYSTEM_PROMPT}] + history
            prompt_json = json.dumps(prompt_obj).replace("'", "\\'")

            sql = f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE(
                    '{MODEL}',
                    PARSE_JSON($${prompt_json}$$),
                    {{'temperature': {temperature}, 'max_tokens': {max_tokens}}}
                ) AS response
            """
            result = session.sql(sql).collect()
            resp = json.loads(result[0]["RESPONSE"])
            answer = (
                resp.get("choices", [{}])[0]
                .get("messages", "Sorry, I couldn't generate a response.")
            )

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
