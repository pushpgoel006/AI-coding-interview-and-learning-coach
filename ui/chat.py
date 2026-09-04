import streamlit as st

from graphs.rag_graph import rag_graph
from ui.sidebar import DOC_TYPE_LABELS


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander(f"Sources ({len(sources)})", expanded=False):
        for source in sources:
            label = DOC_TYPE_LABELS.get(source["doc_type"], source["doc_type"])
            st.caption(f"{source['file_name']} · page {source['page']} · {label}")


def _render_sub_questions(sub_questions: list[str]) -> None:
    if len(sub_questions) <= 1:
        return

    with st.expander(f"Broken into {len(sub_questions)} sub-questions", expanded=False):
        for sub_question in sub_questions:
            st.caption(f"- {sub_question}")


def render_chat(session_id: str):
    if "messages" not in st.session_state:
        st.session_state.messages = {}

    session_messages = st.session_state.messages.setdefault(session_id, [])

    for message in session_messages:
        with st.chat_message(message["role"]):
            _render_sub_questions(message.get("sub_questions", []))
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
            sub_questions = result.get("sub_questions", [])

            _render_sub_questions(sub_questions)
            st.markdown(answer)
            _render_sources(sources)

            session_messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "sub_questions": sub_questions,
                }
            )
