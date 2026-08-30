"""Acceptance test for M6 -- dashboard.

Plain script, not pytest, matching the project's existing test file style.
Run against the real database, vector store, and LLM:

    python test_dashboard.py
"""

from database.db import get_db
from database.models import PrepSession, Interview, Followup, ResumeReview
from services.session_service import create_session
from services.interview_service import record_interview, record_followup
from services.resume_service import save_review
from rag.indexer import index_documents, clear_session_index
from services.analytics import (
    get_theory_average,
    get_theory_trend,
    get_score_by_topic,
    get_resume_fit_score,
    get_weakest_topics,
    get_readiness_score,
)
from agents.recommender import generate_recommendation


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    empty_session = create_session("Dashboard Test Empty", "QA")
    session = create_session("Dashboard Test Co", "QA")
    empty_sid = empty_session["id"]
    session_id = session["id"]
    interview_ids: list[str] = []

    try:
        # 1. Brand-new empty session is safe.
        check(
            "Every analytics function returns a safe empty value against an empty session",
            get_theory_average(empty_sid) is None
            and get_theory_trend(empty_sid) == []
            and get_score_by_topic(empty_sid) == []
            and get_resume_fit_score(empty_sid) is None
            and get_weakest_topics(empty_sid) == []
            and get_readiness_score(empty_sid) is None,
        )

        # Seed a deliberately lopsided history: strong on SQL, weak on
        # Python, plus one no-topic interview that must never surface as a
        # "weak topic".
        i_sql_1 = record_interview(session_id, "SQL", "q1", "a1", 9, "s", "w", "ideal")
        i_sql_2 = record_interview(session_id, "SQL", "q2", "a2", 8, "s", "w", "ideal")
        i_py = record_interview(session_id, "Python", "q3", "a3", 2, "s", "w", "ideal")
        record_followup(i_py["id"], 1, "Python", "fq1", "fa1", 3)
        i_blank = record_interview(session_id, None, "q4", "a4", 5, "s", "w", "ideal")
        interview_ids = [i_sql_1["id"], i_sql_2["id"], i_py["id"], i_blank["id"]]

        save_review(
            session_id,
            overall_score=70,
            matched_skills=["Python"],
            missing_skills=["SQL"],
            suggestions="Practice SQL joins.",
        )

        # 2. Theory average is correct: (9+8+2+3+5)/5 = 5.4
        average = get_theory_average(session_id)
        check(
            "Theory average matches the hand-computed value",
            average is not None and abs(average - 5.4) < 0.01,
        )

        # 3. Score by topic is correct.
        by_topic = {entry["topic"]: entry["average_score"] for entry in get_score_by_topic(session_id)}
        check(
            "SQL scores higher than Python in the topic breakdown",
            by_topic.get("SQL", 0) > by_topic.get("Python", 10),
        )

        # 4. Weakest topics excludes the blank one.
        weakest = get_weakest_topics(session_id)
        check(
            "Weakest topics ranks Python first and never includes a blank topic",
            weakest[0]["topic"] == "Python" and all(w["topic"] for w in weakest),
        )

        # 5. Readiness score is a sane blend.
        readiness = get_readiness_score(session_id)
        resume_fit = get_resume_fit_score(session_id)
        theory_scaled = average / 10 * 100
        low, high = sorted([theory_scaled, resume_fit])
        check(
            "Readiness score sits between the theory and resume-fit signals",
            readiness is not None and low <= readiness <= high,
        )

        # 6. Recommendation is grounded.
        index_documents(
            ["uploads/Pushp_Goel_Resume.pdf"], session_id, doc_type="resume"
        )
        recommendation = generate_recommendation(session_id, "Python")
        check(
            "generate_recommendation returns non-empty advice and sources",
            bool(recommendation["advice"]) and len(recommendation["sources"]) > 0,
        )

        print("\nAll M6 acceptance checks passed.")
    finally:
        clear_session_index(session_id)
        with get_db() as db:
            if interview_ids:
                db.query(Followup).filter(
                    Followup.interview_id.in_(interview_ids)
                ).delete(synchronize_session=False)
                db.query(Interview).filter(
                    Interview.id.in_(interview_ids)
                ).delete(synchronize_session=False)
            db.query(ResumeReview).filter(
                ResumeReview.session_id == session_id
            ).delete(synchronize_session=False)
            db.query(PrepSession).filter(
                PrepSession.id.in_([session_id, empty_sid])
            ).delete(synchronize_session=False)


if __name__ == "__main__":
    main()
