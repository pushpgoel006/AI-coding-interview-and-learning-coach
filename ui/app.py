"""Streamlit application composition layer.

This module intentionally contains no RAG business logic. It saves uploaded
files, then delegates indexing and question answering to backend entry points.
"""

from pathlib import Path

import streamlit as st

from rag.config import UPLOADS_DIR
from rag.indexer import clear_index, index_documents
from ui.chat import render_chat
from ui.sidebar import render_sidebar


def _save_uploaded_files(uploaded_files) -> list[Path]:
    """Save Streamlit upload objects to the project's uploads directory."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    saved_paths = []

    for uploaded_file in uploaded_files:
        # Strip any client-provided path components before writing locally.
        destination = UPLOADS_DIR / Path(uploaded_file.name).name
        destination.write_bytes(uploaded_file.getbuffer())
        saved_paths.append(destination)

    return saved_paths


def main() -> None:
    st.set_page_config(
        page_title="AI Interview Intelligence Platform",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("AI Interview Intelligence Platform")
    st.caption("Upload interview material, then ask questions grounded in it.")

    uploaded_files, process_documents, clear_database = render_sidebar()

    if process_documents:
        if not uploaded_files:
            st.sidebar.warning("Please upload at least one PDF.")
        else:
            try:
                with st.spinner("Processing documents..."):
                    paths = _save_uploaded_files(uploaded_files)
                    chunk_count = index_documents(paths)
            except Exception as error:
                st.sidebar.error(f"Could not process documents: {error}")
            else:
                st.sidebar.success(
                    f"Documents indexed successfully! {chunk_count} chunks created."
                )

    if clear_database:
        try:
            clear_index()
        except Exception as error:
            st.sidebar.error(f"Could not clear the database: {error}")
        else:
            st.session_state.pop("messages", None)
            st.sidebar.success("Document index cleared.")
            st.rerun()

    render_chat()
