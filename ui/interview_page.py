import streamlit as st

from agents.question_generator import generate_grounded_question
from agents.evaluator import evaluate_grounded_answer
from services.interview_service import record_interview


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return

    with st.expander(f"📎 Sources ({len(sources)})", expanded=False):
        for source in sources:
            st.caption(
                f"{source['file_name']} · page {source['page']} · {source['doc_type']}"
            )


def render_interview_page(session_id: str) -> None:
    """Render the theory mock round: question -> answer -> evaluation."""
    st.subheader("🎤 Theory Mock Round")

    question_key = f"interview_question_{session_id}"
    evaluation_key = f"interview_evaluation_{session_id}"

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
            st.session_state[question_key] = result
            st.session_state.pop(evaluation_key, None)

    question_data = st.session_state.get(question_key)

    if not question_data:
        st.info("Click 'New Question' to get started.")
        return

    st.markdown(f"**Question:** {question_data['question']}")
    _render_sources(question_data.get("sources", []))

    answer = st.text_area("Your answer", key=f"interview_answer_{session_id}")

    if st.button("✅ Submit Answer", use_container_width=True):
        if not answer.strip():
            st.warning("Write an answer before submitting.")
        else:
            try:
                with st.spinner("Evaluating your answer..."):
                    evaluation = evaluate_grounded_answer(
                        session_id, question_data["question"], answer
                    )
            except Exception as error:
                st.error(f"Something went wrong evaluating that: {error}")
            else:
                if "error" in evaluation:
                    st.error(evaluation["error"])
                else:
                    record_interview(
                        session_id=session_id,
                        topic=question_data.get("topic"),
                        question=question_data["question"],
                        answer=answer,
                        score=evaluation.get("score", 0),
                        strengths=evaluation.get("strengths", ""),
                        weaknesses=evaluation.get("weaknesses", ""),
                        ideal_answer=evaluation.get("ideal_answer", ""),
                    )
                    st.session_state[evaluation_key] = evaluation

    evaluation = st.session_state.get(evaluation_key)
    if evaluation:
        st.metric("Score", f"{evaluation.get('score', 0)}/10")

        st.markdown("**Strengths**")
        st.write(evaluation.get("strengths", ""))

        st.markdown("**Weaknesses**")
        st.write(evaluation.get("weaknesses", ""))

        st.markdown("**Ideal Answer**")
        st.write(evaluation.get("ideal_answer", ""))
        _render_sources(evaluation.get("sources", []))

        if not evaluation.get("grounded", False):
            st.caption(
                "⚠️ This ideal answer could not be confirmed against your "
                "uploaded material."
            )
