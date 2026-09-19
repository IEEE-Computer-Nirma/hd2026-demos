"""
snowflake_connection.py

Dual-environment Snowflake connection helper.
- Snowflake Workspace: uses st.connection("snowflake") (embedded identity).
- Local development: falls back to snowflake.connector with .env credentials.
"""

import os
import streamlit as st


def _is_running_in_snowflake() -> bool:
    """Detect whether we are inside a Snowflake Workspace / SiS runtime."""
    return os.path.isfile("/snowflake/session/token")


def get_connection():
    """
    Return a Snowflake connection appropriate for the current environment.

    In Snowflake Workspace: returns the SnowflakeConnection from st.connection.
    Locally: returns a snowflake.connector connection using .env variables.
    """
    if _is_running_in_snowflake():
        return st.connection(
            "snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL")
        )

    # Local fallback — uses snowflake.connector + .env
    from dotenv import load_dotenv
    import snowflake.connector

    load_dotenv()
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def is_workspace() -> bool:
    """Public helper so other modules can branch on the runtime."""
    return _is_running_in_snowflake()
