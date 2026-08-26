"""Owns ResumeReview rows. The only module allowed to touch them.

Every function returns plain dicts, never ORM objects -- same rule as
session_service.py and for the same reason (DetachedInstanceError once the
db session closes).
"""
from database.db import get_db
from database.models import ResumeReview


def _review_to_dict(review: ResumeReview) -> dict:
    return {
        "id": review.id,
        "session_id": review.session_id,
        "overall_score": review.overall_score,
        "matched_skills": review.matched_skills,
        "missing_skills": review.missing_skills,
        "suggestions": review.suggestions,
        "created_at": review.created_at,
    }


def save_review(
    session_id: str,
    overall_score: int,
    matched_skills: list[str],
    missing_skills: list[str],
    suggestions: str,
) -> dict:
    with get_db() as db:
        review = ResumeReview(
            session_id=session_id,
            overall_score=overall_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            suggestions=suggestions,
        )
        db.add(review)
        db.flush()
        return _review_to_dict(review)


def list_reviews(session_id: str) -> list[dict]:
    with get_db() as db:
        reviews = (
            db.query(ResumeReview)
            .filter(ResumeReview.session_id == session_id)
            .order_by(ResumeReview.created_at.desc())
            .all()
        )
        return [_review_to_dict(review) for review in reviews]


def get_latest_review(session_id: str) -> dict | None:
    reviews = list_reviews(session_id)
    return reviews[0] if reviews else None
