import uuid

from database.db import get_db
from database.models import Interview, Followup


def _interview_to_dict(interview: Interview) -> dict:
    return {
        "id": interview.id,
        "session_id": interview.session_id,
        "topic": interview.topic,
        "question": interview.question,
        "answer": interview.answer,
        "score": interview.score,
        "strengths": interview.strengths,
        "weaknesses": interview.weaknesses,
        "ideal_answer": interview.ideal_answer,
        "created_at": interview.created_at,
    }


def record_interview(
    session_id: str,
    topic: str | None,
    question: str,
    answer: str,
    score: int,
    strengths: str,
    weaknesses: str,
    ideal_answer: str,
) -> dict:
    with get_db() as db:
        interview = Interview(
            id=str(uuid.uuid4()),
            session_id=session_id,
            topic=topic,
            question=question,
            answer=answer,
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            ideal_answer=ideal_answer,
        )
        db.add(interview)
        db.flush()
        return _interview_to_dict(interview)


def list_interviews(session_id: str) -> list[dict]:
    with get_db() as db:
        interviews = (
            db.query(Interview)
            .filter(Interview.session_id == session_id)
            .order_by(Interview.created_at.desc())
            .all()
        )
        return [_interview_to_dict(interview) for interview in interviews]


def get_interview(interview_id: str) -> dict | None:
    with get_db() as db:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        return _interview_to_dict(interview) if interview else None


def _followup_to_dict(followup: Followup) -> dict:
    return {
        "id": followup.id,
        "interview_id": followup.interview_id,
        "followup_number": followup.followup_number,
        "topic": followup.topic,
        "question": followup.question,
        "answer": followup.answer,
        "score": followup.score,
        "created_at": followup.created_at,
    }


def record_followup(
    interview_id: str,
    followup_number: int,
    topic: str | None,
    question: str,
    answer: str,
    score: int,
) -> dict:
    with get_db() as db:
        followup = Followup(
            interview_id=interview_id,
            followup_number=followup_number,
            topic=topic,
            question=question,
            answer=answer,
            score=score,
        )
        db.add(followup)
        db.flush()
        return _followup_to_dict(followup)


def list_followups(interview_id: str) -> list[dict]:
    with get_db() as db:
        followups = (
            db.query(Followup)
            .filter(Followup.interview_id == interview_id)
            .order_by(Followup.followup_number.asc())
            .all()
        )
        return [_followup_to_dict(followup) for followup in followups]
