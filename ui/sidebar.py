import streamlit as st

from services.session_service import list_documents

DOC_TYPE_LABELS = {
    "company": "Company",
    "jd": "Job Description",
    "resume": "Resume",
    "notes": "Notes",
    "experience": "Experience",
}
DOC_TYPE_VALUES = {label: value for value, label in DOC_TYPE_LABELS.items()}


def render_sidebar(session_id: str):

    with st.sidebar:

        st.header("Documents")

        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True,
        )

        doc_type_label = st.selectbox("Document type", list(DOC_TYPE_LABELS.values()))
        doc_type = DOC_TYPE_VALUES[doc_type_label]

        process_documents = st.button(
            "Process Documents",
            use_container_width=True,
        )

        st.divider()

        st.subheader("Selected Documents")

        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.caption(f"✓ {uploaded_file.name}")
        else:
            st.caption("No documents selected.")

        st.divider()

        st.subheader("Indexed Documents")

        indexed_documents = list_documents(session_id)

        if indexed_documents:
            for document in indexed_documents:
                label = DOC_TYPE_LABELS.get(document["doc_type"], document["doc_type"])
                st.caption(f"{document['file_name']} · {label}")
        else:
            st.caption("No documents indexed yet.")

        st.divider()

        clear_database = st.button(
            "Clear This Session's Documents",
            use_container_width=True,
        )

    return uploaded_files, doc_type, process_documents, clear_database
