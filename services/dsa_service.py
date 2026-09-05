from database.db import get_db
from database.models import DsaAttempt


def _attempt_to_dict(attempt: DsaAttempt) -> dict:
    return {
        "id": attempt.id,
        "session_id": attempt.session_id,
        "topic": attempt.topic,
        "difficulty": attempt.difficulty,
        "problem_slug": attempt.problem_slug,
        "problem_title": attempt.problem_title,
        "code": attempt.code,
        "language": attempt.language,
        "score": attempt.score,
        "correctness_notes": attempt.correctness_notes,
        "complexity_notes": attempt.complexity_notes,
        "suggestions": attempt.suggestions,
        "created_at": attempt.created_at,
    }


def record_attempt(
    session_id: str,
    topic: str | None,
    difficulty: str | None,
    problem_slug: str | None,
    problem_title: str | None,
    code: str,
    language: str,
    score: int,
    correctness_notes: str,
    complexity_notes: str,
    suggestions: str,
) -> dict:
    with get_db() as db:
        attempt = DsaAttempt(
            session_id=session_id,
            topic=topic,
            difficulty=difficulty,
            problem_slug=problem_slug,
            problem_title=problem_title,
            code=code,
            language=language,
            score=score,
            correctness_notes=correctness_notes,
            complexity_notes=complexity_notes,
            suggestions=suggestions,
        )
        db.add(attempt)
        db.flush()
        return _attempt_to_dict(attempt)


def list_attempts(session_id: str) -> list[dict]:
    with get_db() as db:
        attempts = (
            db.query(DsaAttempt)
            .filter(DsaAttempt.session_id == session_id)
            .order_by(DsaAttempt.created_at.desc())
            .all()
        )
        return [_attempt_to_dict(attempt) for attempt in attempts]
