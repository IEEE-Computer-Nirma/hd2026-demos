"""My watchlist — full CRUD over an app-owned Snowflake table."""

import streamlit as st

from utils.db import (
    latest_unemployment_by_state_map,
    load_company_names,
    load_state_names,
    watchlist_create,
    watchlist_delete,
    watchlist_list,
    watchlist_update,
)

st.title("My watchlist")
st.caption("A personal, editable list backed by a Snowflake table — full Create / Read / Update / Delete")

ENTITY_TYPES = ["State (Unemployment)", "Company", "Economic Indicator"]

# ----- CREATE -----
with st.container(border=True):
    st.subheader("Add to watchlist", anchor=False)
    with st.form("create_watchlist_item", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            entity_type = st.selectbox("Entity type", options=ENTITY_TYPES)
        with c2:
            if entity_type == "State (Unemployment)":
                entity_name = st.selectbox("State", options=load_state_names())
            elif entity_type == "Company":
                entity_name = st.selectbox("Company", options=load_company_names())
            else:
                entity_name = st.text_input("Indicator name", placeholder="e.g. CPI: All items")

        c3, c4 = st.columns(2)
        with c3:
            target_value = st.number_input("Target value (optional)", value=0.0, step=0.1, format="%.2f")
        with c4:
            has_target = st.checkbox("Set a target value", value=False)

        notes = st.text_area("Notes", placeholder="Why are you tracking this?")
        submitted = st.form_submit_button("Add to watchlist", type="primary", icon=":material/add:")

        if submitted:
            if not entity_name:
                st.error("Please provide an entity name.", icon=":material/error:")
            else:
                watchlist_create(
                    entity_type=entity_type,
                    entity_name=entity_name,
                    target_value=target_value if has_target else None,
                    notes=notes,
                )
                st.success(f"Added **{entity_name}** to your watchlist.", icon=":material/check_circle:")
                st.rerun()

# ----- READ -----
st.subheader("Current watchlist", anchor=False)

df = watchlist_list()

if df.empty:
    st.caption("Your watchlist is empty. Add an item above to get started.")
else:
    unemployment_map = latest_unemployment_by_state_map()
    df = df.copy()
    df["LATEST_VALUE"] = df.apply(
        lambda r: unemployment_map.get(r["ENTITY_NAME"])
        if r["ENTITY_TYPE"] == "State (Unemployment)"
        else None,
        axis=1,
    )

    st.dataframe(
        df.rename(
            columns={
                "ID": "ID",
                "ENTITY_TYPE": "Type",
                "ENTITY_NAME": "Name",
                "TARGET_VALUE": "Target",
                "LATEST_VALUE": "Latest unemployment %",
                "NOTES": "Notes",
                "UPDATED_AT": "Last updated",
            }
        )[["ID", "Type", "Name", "Target", "Latest unemployment %", "Notes", "Last updated"]],
        use_container_width=True,
        hide_index=True,
    )

    # ----- UPDATE / DELETE -----
    st.subheader("Edit or delete an entry", anchor=False)

    id_to_label = {
        int(row.ID): f"#{int(row.ID)} — {row.ENTITY_TYPE}: {row.ENTITY_NAME}" for row in df.itertuples()
    }
    selected_id = st.selectbox(
        "Select an item to edit or delete",
        options=list(id_to_label.keys()),
        format_func=lambda i: id_to_label[i],
    )

    selected_row = df[df["ID"] == selected_id].iloc[0]

    with st.form("edit_watchlist_item"):
        edit_target = st.number_input(
            "Target value",
            value=float(selected_row["TARGET_VALUE"]) if selected_row["TARGET_VALUE"] is not None else 0.0,
            step=0.1,
            format="%.2f",
        )
        edit_notes = st.text_area("Notes", value=selected_row["NOTES"] or "")

        edit_col, delete_col = st.columns(2)
        with edit_col:
            save_clicked = st.form_submit_button("Save changes", type="primary", icon=":material/save:")
        with delete_col:
            delete_clicked = st.form_submit_button("Delete entry", icon=":material/delete:")

        if save_clicked:
            watchlist_update(row_id=int(selected_id), target_value=edit_target, notes=edit_notes)
            st.success(f"Updated entry #{selected_id}.", icon=":material/check_circle:")
            st.rerun()

        if delete_clicked:
            watchlist_delete([int(selected_id)])
            st.success(f"Deleted entry #{selected_id}.", icon=":material/check_circle:")
            st.rerun()
