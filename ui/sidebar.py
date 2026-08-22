import streamlit as st


def render_sidebar():

    with st.sidebar:

        st.header("📄 Documents")

        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True,
        )

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

        clear_database = st.button(
            "🗑 Clear Database",
            use_container_width=True,
        )

    return uploaded_files, process_documents, clear_database
