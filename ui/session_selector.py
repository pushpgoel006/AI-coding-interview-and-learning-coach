import streamlit as st

from services.session_service import create_session, get_session, list_sessions


def render_session_selector() -> dict | None:
    """Render the prep-session picker at the top of the sidebar.

    Returns the active session as a dict, or None if no session exists yet.
    """
    with st.sidebar:
        st.header("🗂️ Prep Session")

        sessions = list_sessions()

        if sessions:
            labels = [f"{s['company_name']} — {s['role']}" for s in sessions]
            ids = [s["id"] for s in sessions]

            current_id = st.session_state.get("active_session_id")
            default_index = ids.index(current_id) if current_id in ids else 0

            selected_index = st.selectbox(
                "Active session",
                options=range(len(labels)),
                format_func=lambda i: labels[i],
                index=default_index,
            )
            st.session_state.active_session_id = ids[selected_index]

        with st.expander("➕ New prep session"):
            company_name = st.text_input("Company name", key="new_session_company")
            role = st.text_input("Role", key="new_session_role")
            jd_text = st.text_area(
                "Job description (optional)", key="new_session_jd"
            )
            create_clicked = st.button("Create", key="create_session_button")

            if create_clicked:
                if not company_name.strip() or not role.strip():
                    st.warning("Company name and role are required.")
                else:
                    new_session = create_session(company_name.strip(), role.strip(), jd_text)
                    st.session_state.active_session_id = new_session["id"]
                    st.rerun()

        st.divider()

    active_id = st.session_state.get("active_session_id")
    return get_session(active_id) if active_id else None
