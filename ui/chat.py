import streamlit as st

from graphs.rag_graph import rag_graph


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander(f"📎 Sources ({len(sources)})", expanded=False):
        for source in sources:
            st.caption(
                f"{source['file_name']} · page {source['page']} · {source['doc_type']}"
            )


def render_chat(session_id: str):
    """Render the chat experience and delegate questions to the RAG graph."""
    if "messages" not in st.session_state:
        st.session_state.messages = {}

    session_messages = st.session_state.messages.setdefault(session_id, [])

    for message in session_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            _render_sources(message.get("sources", []))

    question = st.chat_input(
        "Ask something about your documents..."
    )

    if question:

        session_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            try:
                with st.spinner("Thinking..."):

                    result = rag_graph.invoke(
                        {"question": question, "session_id": session_id}
                    )
            except Exception as error:
                st.error(f"Something went wrong answering that: {error}")
                return

            answer = result["answer"]
            sources = result.get("sources", [])

            st.markdown(answer)
            _render_sources(sources)

            session_messages.append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
