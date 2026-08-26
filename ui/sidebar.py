import streamlit as st

from services.session_service import list_documents

DOC_TYPES = ["company", "jd", "resume", "notes", "experience"]


def render_sidebar(session_id: str):

    with st.sidebar:

        st.header("📄 Documents")

        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True,
        )

        doc_type = st.selectbox("Document type", DOC_TYPES)

        process_documents = st.button(
            "⚡ Process Documents",
            use_container_width=True,
        )

        st.divider()

        st.subheader("📚 Selected Documents")

        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.caption(f"✓ {uploaded_file.name}")
        else:
            st.caption("No documents selected.")

        st.divider()

        st.subheader("📚 Indexed Documents")

        indexed_documents = list_documents(session_id)

        if indexed_documents:
            for document in indexed_documents:
                st.caption(f"{document['file_name']} · {document['doc_type']}")
        else:
            st.caption("No documents indexed yet.")

        st.divider()

        clear_database = st.button(
            "🗑 Clear This Session's Documents",
            use_container_width=True,
        )

    return uploaded_files, doc_type, process_documents, clear_database
