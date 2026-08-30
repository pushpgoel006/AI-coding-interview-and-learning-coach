"""Acceptance test for M4 -- follow-up round with memory.

Plain script, not pytest, matching the project's existing test file style.
Run against the real database, vector store, and LLM:

    python test_followup_round.py
"""

import re
from unittest.mock import patch

from database.db import get_db
from database.models import PrepSession, Interview, Followup
from services.session_service import create_session
from services.interview_service import list_followups
from rag.indexer import index_documents, clear_session_index
from graphs.interview_graph import interview_graph


def _normalize(text: str) -> str:
    """Lowercase, collapse Unicode hyphen variants to ASCII '-', strip other
    punctuation -- the model sometimes uses a different hyphen glyph than
    plain text, and attaches commas/semicolons/parens directly to words,
    which breaks a naive substring check on otherwise identical content."""
    text = text.lower()
    dash_variants = "".join(chr(code) for code in range(0x2010, 0x2016)) + chr(0x2212)
    for dash in dash_variants:
        text = text.replace(dash, "-")
    return re.sub(r"[^\w\s-]", " ", text)


def _references(question: str, source_text: str) -> bool:
    """True if a meaningful fraction of source_text's distinctive words show
    up in question -- proof of a real callback, not just topical overlap."""
    norm_question = _normalize(question)
    words = [w for w in _normalize(source_text).split() if len(w) > 4]
    if not words:
        return False
    question_prefixes = {w[:6] for w in norm_question.split() if len(w) > 4}
    matched = sum(1 for word in words if word[:6] in question_prefixes)
    return matched / len(words) >= 0.3


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    session = create_session("Followup Round Test", "QA")
    session_id = session["id"]
    interview_id = None

    try:
        index_documents(
            ["uploads/Pushp_Goel_Resume.pdf"], session_id, doc_type="resume"
        )
        index_documents(
            ["uploads/IBM_AI_ML_Engineer_Requirements.pdf"], session_id, doc_type="jd"
        )

        # Round 0: original question.
        state = interview_graph.invoke(
            {
                "session_id": session_id,
                "topic": "Computer Vision",
                "answer": (
                    "I used OpenCV and MediaPipe to build a real-time "
                    "push-up form analyzer that tracks joint angles."
                ),
            }
        )
        interview_id = state["interview_id"]
        check(
            "Original round produced a follow-up to ask",
            bool(state["next_question"]),
        )

        followup_answers = [
            "I used a Kalman filter to smooth noisy joint angle estimates from MediaPipe.",
            "I tuned the filter's process noise covariance empirically using recorded video.",
            "The main trade-off was added latency versus smoother, less jittery angle tracking.",
        ]

        first_followup_answer = None
        thread_questions = []

        next_q = state["next_question"]
        for i, answer in enumerate(followup_answers, start=1):
            state = interview_graph.invoke(
                {**state, "question": next_q, "answer": answer, "followup_number": i}
            )
            thread_questions.append(next_q)
            if i == 1:
                first_followup_answer = answer
            next_q = state["next_question"]

        # 1. Depth limit.
        check(
            "Thread stops after exactly 3 follow-ups (no 4th offered)",
            state["next_question"] is None,
        )

        # 2. A later follow-up references the FIRST follow-up's answer, not
        # just the original one -- proof conversation memory is used.
        later_questions = thread_questions[1:]  # follow-ups 2 and 3
        check(
            "A later follow-up's question references the first follow-up's answer",
            any(_references(q, first_followup_answer) for q in later_questions),
        )

        # 3. Persistence.
        followups = list_followups(interview_id)
        check(
            "Exactly 3 follow-ups persisted, numbered 1/2/3 in order",
            [f["followup_number"] for f in followups] == [1, 2, 3],
        )
        check(
            "Every persisted follow-up has a real score",
            all(f["score"] is not None for f in followups),
        )

        # 4. Legacy path unaffected.
        with patch("graphs.interview_graph.interview_service") as mock_service:
            legacy_result = interview_graph.invoke(
                {
                    "jd": "Looking for a Python backend engineer.",
                    "answer": "I have 3 years of Django experience.",
                }
            )
        check(
            "Legacy call still returns exactly the old shape",
            set(legacy_result.keys()) == {"jd", "answer", "question", "evaluation"},
        )
        check(
            "Legacy call never touches interview_service",
            not mock_service.record_interview.called
            and not mock_service.record_followup.called,
        )

        print("\nAll M4 acceptance checks passed.")
    finally:
        clear_session_index(session_id)
        with get_db() as db:
            if interview_id:
                db.query(Followup).filter(
                    Followup.interview_id == interview_id
                ).delete(synchronize_session=False)
                db.query(Interview).filter(Interview.id == interview_id).delete(
                    synchronize_session=False
                )
            db.query(PrepSession).filter(PrepSession.id == session_id).delete(
                synchronize_session=False
            )


if __name__ == "__main__":
    main()
