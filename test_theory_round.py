"""Acceptance test for M3 -- theory mock round.

Plain script, not pytest, matching the project's existing test file style.
Run against the real database, vector store, and LLM:

    python test_theory_round.py
"""

from unittest.mock import patch, MagicMock

from database.db import get_db
from database.models import PrepSession, Interview
from services.session_service import create_session
from services.interview_service import list_interviews
from rag.indexer import index_documents, clear_session_index
from agents.question_generator import generate_grounded_question
from agents.evaluator import evaluate_grounded_answer, evaluate_answer
from graphs.interview_graph import interview_graph


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    session = create_session("Theory Round Test", "QA")
    session_id = session["id"]

    try:
        index_documents(
            ["uploads/Pushp_Goel_Resume.pdf"], session_id, doc_type="resume"
        )
        index_documents(
            ["uploads/IBM_AI_ML_Engineer_Requirements.pdf"], session_id, doc_type="jd"
        )

        # 1. Grounded question generation.
        question_result = generate_grounded_question(session_id, topic="Python")
        check(
            "generate_grounded_question returns a non-empty question and sources",
            bool(question_result["question"]) and len(question_result["sources"]) > 0,
        )

        # 2. Grounded evaluation shape.
        evaluation = evaluate_grounded_answer(
            session_id,
            question_result["question"],
            "I used Python and OpenCV to build a real-time computer vision pipeline.",
        )
        check(
            "score is an int in 0..10",
            isinstance(evaluation["score"], int) and 0 <= evaluation["score"] <= 10,
        )
        check(
            "strengths/weaknesses/ideal_answer are non-empty",
            bool(evaluation["strengths"])
            and bool(evaluation["weaknesses"])
            and bool(evaluation["ideal_answer"]),
        )
        check("sources are non-empty", len(evaluation["sources"]) > 0)
        check("grounded is a bool", isinstance(evaluation["grounded"], bool))

        # 3. Persistence via the graph's grounded path.
        graph_result = interview_graph.invoke(
            {
                "session_id": session_id,
                "topic": "Python",
                "answer": "I used Python and OpenCV to build a real-time computer vision pipeline.",
            }
        )
        check("graph grounded run produced an evaluation", "evaluation" in graph_result)

        persisted = list_interviews(session_id)
        check("at least one interview was persisted", len(persisted) >= 1)
        latest = persisted[0]
        check(
            "persisted row has topic/ideal_answer/strengths/weaknesses populated",
            bool(latest["topic"])
            and bool(latest["ideal_answer"])
            and bool(latest["strengths"])
            and bool(latest["weaknesses"]),
        )

        # 4. Legacy path is unchanged and never touches interview_service.
        with patch("graphs.interview_graph.interview_service") as mock_service:
            legacy_result = interview_graph.invoke(
                {
                    "jd": "Looking for a Python backend engineer.",
                    "answer": "I have 3 years of Django experience.",
                }
            )
        check(
            "legacy call returns exactly the old shape",
            set(legacy_result.keys()) == {"jd", "answer", "question", "evaluation"},
        )
        check(
            "legacy call never touches interview_service",
            not mock_service.record_interview.called,
        )

        # 5. The pre-existing crash is fixed.
        with patch("agents.evaluator.llm") as mock_llm:
            mock_llm.invoke.return_value = MagicMock(content="not valid json {{{")
            crash_result = evaluate_answer("What is a hash map?", "A key-value store.")
        check(
            "evaluate_answer returns an error dict on malformed JSON instead of raising",
            crash_result == {"error": "Could not parse the evaluation. Please try again."},
        )

        print("\nAll M3 acceptance checks passed.")
    finally:
        clear_session_index(session_id)
        with get_db() as db:
            db.query(Interview).filter(Interview.session_id == session_id).delete(
                synchronize_session=False
            )
            db.query(PrepSession).filter(PrepSession.id == session_id).delete(
                synchronize_session=False
            )


if __name__ == "__main__":
    main()
