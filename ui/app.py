import time
from pathlib import Path

import streamlit as st

from rag.config import UPLOADS_DIR
from rag.indexer import clear_session_index, index_documents
from services.auth_service import get_user
from services.session_service import delete_session_documents, record_document
from ui.auth_page import get_cookie_manager, render_auth_page
from ui.chat import render_chat
from ui.dashboard_page import render_dashboard_page
from ui.dsa_page import render_dsa_page
from ui.interview_page import render_interview_page
from ui.resume_page import render_resume_page
from ui.session_selector import render_session_selector
from ui.sidebar import render_sidebar


def _save_uploaded_files(uploaded_files) -> list[Path]:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for uploaded_file in uploaded_files:
        destination = UPLOADS_DIR / Path(uploaded_file.name).name
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(destination)

    return saved_paths


def main() -> None:
    st.set_page_config(
        page_title="AI Interview Intelligence Platform",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    cookie_manager = get_cookie_manager()
    cookies = cookie_manager.get_all()

    if cookies is None:
        st.stop()

    if "current_user" not in st.session_state:
        cookie_user_id = cookies.get("user_id")
        if cookie_user_id:
            user = get_user(cookie_user_id)
            if user:
                st.session_state.current_user = user

    if "current_user" not in st.session_state:
        render_auth_page()
        return

    current_user = st.session_state.current_user

    st.title("AI Interview Intelligence Platform")
    st.caption("Upload interview material, then ask questions grounded in it.")

    with st.sidebar:
        st.write(f"Signed in as **{current_user['display_name']}**")
        if st.button("Log out"):
            try:
                cookie_manager.delete("user_id", key="delete_login_cookie")
            except KeyError:
                pass
            del st.session_state["current_user"]
            time.sleep(0.5)
            st.rerun()

    active_session = render_session_selector(current_user["id"])

    if not active_session:
        st.info("Create a prep session to get started.")
        return

    session_id = active_session["id"]

    uploaded_files, doc_type, process_documents, clear_database = render_sidebar(
        session_id
    )

    if process_documents:
        if not uploaded_files:
            st.sidebar.warning("Please upload at least one PDF.")
        else:
            try:
                with st.spinner("Processing documents..."):
                    total_chunks = 0
                    for uploaded_file in uploaded_files:
                        path = _save_uploaded_files([uploaded_file])[0]
                        chunk_count = index_documents(
                            [path], session_id, doc_type=doc_type
                        )
                        record_document(
                            session_id=session_id,
                            file_name=path.name,
                            file_path=str(path),
                            doc_type=doc_type,
                            chunk_count=chunk_count,
                        )
                        total_chunks += chunk_count
            except Exception as error:
                st.sidebar.error(f"Could not process documents: {error}")
            else:
                st.sidebar.success(
                    f"Documents indexed successfully! {total_chunks} chunks created."
                )
                st.rerun()

    if clear_database:
        try:
            clear_session_index(session_id)
            delete_session_documents(session_id)
        except Exception as error:
            st.sidebar.error(f"Could not clear this session's documents: {error}")
        else:
            st.session_state.get("messages", {}).pop(session_id, None)
            st.sidebar.success("This session's documents were cleared.")
            st.rerun()

    chat_tab, resume_tab, interview_tab, dsa_tab, dashboard_tab = st.tabs(
        ["Chat", "Resume Check", "Theory Round", "DSA Round", "Dashboard"]
    )

    with chat_tab:
        render_chat(session_id)

    with resume_tab:
        render_resume_page(session_id)

    with interview_tab:
        render_interview_page(session_id)

    with dsa_tab:
        render_dsa_page(session_id)

    with dashboard_tab:
        render_dashboard_page(session_id)
