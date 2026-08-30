from datetime import datetime

from database.db import get_db
from database.models import Interview, Followup, ResumeReview


def _theory_entries(db, session_id: str) -> list[dict]:
    entries = []

    interviews = (
        db.query(Interview)
        .filter(Interview.session_id == session_id, Interview.score.isnot(None))
        .all()
    )
    for interview in interviews:
        entries.append(
            {"date": interview.created_at, "topic": interview.topic, "score": interview.score}
        )

    followups = (
        db.query(Followup)
        .join(Interview, Followup.interview_id == Interview.id)
        .filter(Interview.session_id == session_id, Followup.score.isnot(None))
        .all()
    )
    for followup in followups:
        entries.append(
            {"date": followup.created_at, "topic": followup.topic, "score": followup.score}
        )

    entries.sort(key=lambda entry: entry["date"] or datetime.min)
    return entries


def get_theory_average(session_id: str) -> float | None:
    with get_db() as db:
        entries = _theory_entries(db, session_id)

    if not entries:
        return None

    return sum(entry["score"] for entry in entries) / len(entries)


def get_theory_trend(session_id: str) -> list[dict]:
    with get_db() as db:
        return _theory_entries(db, session_id)


def get_score_by_topic(session_id: str) -> list[dict]:
    with get_db() as db:
        entries = _theory_entries(db, session_id)

    by_topic: dict[str, list[int]] = {}
    for entry in entries:
        topic = entry["topic"]
        if not topic:
            continue
        by_topic.setdefault(topic, []).append(entry["score"])

    return [
        {"topic": topic, "average_score": sum(scores) / len(scores)}
        for topic, scores in by_topic.items()
    ]


def get_resume_fit_score(session_id: str) -> int | None:
    with get_db() as db:
        review = (
            db.query(ResumeReview)
            .filter(ResumeReview.session_id == session_id)
            .order_by(ResumeReview.created_at.desc())
            .first()
        )
        return review.overall_score if review else None


def get_weakest_topics(session_id: str, n: int = 3) -> list[dict]:
    topics = get_score_by_topic(session_id)
    topics.sort(key=lambda item: item["average_score"])
    return topics[:n]


def get_readiness_score(session_id: str) -> int | None:
    theory_average = get_theory_average(session_id)
    resume_fit = get_resume_fit_score(session_id)

    theory_scaled = (theory_average / 10 * 100) if theory_average is not None else None

    if theory_scaled is not None and resume_fit is not None:
        return round(0.6 * theory_scaled + 0.4 * resume_fit)
    if theory_scaled is not None:
        return round(theory_scaled)
    if resume_fit is not None:
        return round(resume_fit)
    return None
