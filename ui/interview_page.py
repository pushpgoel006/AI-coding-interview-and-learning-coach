import streamlit as st

from agents.question_generator import generate_grounded_question
from graphs.interview_graph import interview_graph


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander(f"📎 Sources ({len(sources)})", expanded=False):
        for source in sources:
            st.caption(
                f"{source['file_name']} · page {source['page']} · {source['doc_type']}"
            )


def _render_turn(label: str, question: str, answer: str, result: dict) -> None:
    st.markdown(f"**{label}:** {question}")
    st.markdown(f"*Your answer:* {answer}")
    st.metric("Score", f"{result.get('score', 0)}/10")

    st.markdown("**Strengths**")
    st.write(result.get("strengths", ""))

    st.markdown("**Weaknesses**")
    st.write(result.get("weaknesses", ""))

    st.markdown("**Ideal Answer**")
    st.write(result.get("ideal_answer", ""))
    _render_sources(result.get("sources", []))

    if not result.get("grounded", False):
        st.caption(
            "⚠️ This ideal answer could not be confirmed against your "
            "uploaded material."
        )
    st.divider()


def render_interview_page(session_id: str) -> None:
    st.subheader("🎤 Theory Mock Round")

    thread_key = f"interview_thread_{session_id}"
    state_key = f"interview_state_{session_id}"
    pending_key = f"interview_pending_{session_id}"

    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Topic (optional)", key=f"interview_topic_{session_id}")
    with col2:
        difficulty = st.selectbox(
            "Difficulty",
            ["easy", "medium", "hard"],
            index=1,
            key=f"interview_difficulty_{session_id}",
        )

    if st.button("🎲 New Question", use_container_width=True):
        try:
            with st.spinner("Generating a question..."):
                result = generate_grounded_question(
                    session_id, topic=topic or None, difficulty=difficulty
                )
        except Exception as error:
            st.error(f"Something went wrong generating a question: {error}")
        else:
            st.session_state[pending_key] = {
                "question": result["question"],
                "sources": result.get("sources", []),
                "followup_number": 0,
            }
            st.session_state[thread_key] = []
            st.session_state[state_key] = {
                "session_id": session_id,
                "topic": result.get("topic"),
                "difficulty": difficulty,
            }

    for turn in st.session_state.get(thread_key, []):
        label = (
            "Question"
            if turn["followup_number"] == 0
            else f"Follow-up #{turn['followup_number']}"
        )
        _render_turn(label, turn["question"], turn["answer"], turn["result"])

    pending = st.session_state.get(pending_key)

    if not pending:
        if not st.session_state.get(thread_key):
            st.info("Click 'New Question' to get started.")
        else:
            st.success("Thread complete -- no more follow-ups.")
        return

    label = (
        "Question"
        if pending["followup_number"] == 0
        else f"Follow-up #{pending['followup_number']}"
    )
    st.markdown(f"**{label}:** {pending['question']}")
    _render_sources(pending.get("sources", []))

    answer = st.text_area(
        "Your answer", key=f"interview_answer_{session_id}_{pending['followup_number']}"
    )

    if st.button("✅ Submit Answer", use_container_width=True):
        if not answer.strip():
            st.warning("Write an answer before submitting.")
        else:
            graph_input = {
                **st.session_state.get(state_key, {}),
                "question": pending["question"],
                "answer": answer,
                "followup_number": pending["followup_number"],
            }
            try:
                with st.spinner("Evaluating your answer..."):
                    graph_result = interview_graph.invoke(graph_input)
            except Exception as error:
                st.error(f"Something went wrong evaluating that: {error}")
            else:
                evaluation = graph_result.get("evaluation") or {}
                if "error" in evaluation:
                    st.error(evaluation["error"])
                else:
                    st.session_state.setdefault(thread_key, []).append(
                        {
                            "followup_number": pending["followup_number"],
                            "question": pending["question"],
                            "answer": answer,
                            "result": evaluation,
                        }
                    )
                    st.session_state[state_key] = graph_result

                    next_question = graph_result.get("next_question")
                    if next_question:
                        st.session_state[pending_key] = {
                            "question": next_question,
                            "sources": graph_result.get("sources", []),
                            "followup_number": pending["followup_number"] + 1,
                        }
                    else:
                        st.session_state.pop(pending_key, None)

                    st.rerun()
