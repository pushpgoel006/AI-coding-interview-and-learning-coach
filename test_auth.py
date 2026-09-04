from database.db import get_db
from database.models import PrepSession, User
from services.auth_service import register_user, verify_login
from services.session_service import create_session, get_session, list_sessions

EMAIL_A = "test-auth-a@example.com"
EMAIL_B = "test-auth-b@example.com"


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def _cleanup() -> None:
    with get_db() as db:
        users = db.query(User).filter(User.email.in_([EMAIL_A, EMAIL_B])).all()
        ids = [u.id for u in users]
        if ids:
            db.query(PrepSession).filter(PrepSession.owner_id.in_(ids)).delete(
                synchronize_session=False
            )
            db.query(User).filter(User.id.in_(ids)).delete(synchronize_session=False)


def main() -> None:
    _cleanup()

    user_a = register_user(EMAIL_A, "passwordA123", "Test User A")
    user_b = register_user(EMAIL_B, "passwordB123", "Test User B")
    check(
        "Registered user A and user B with different emails",
        user_a["id"] != user_b["id"],
    )

    try:
        register_user(EMAIL_A, "anotherpassword", "Dup User")
        check("Registering A's email again raises ValueError", False)
    except ValueError:
        check("Registering A's email again raises ValueError", True)

    check(
        "verify_login with A's correct password returns a dict",
        verify_login(EMAIL_A, "passwordA123") is not None,
    )
    check(
        "verify_login with A's wrong password returns None",
        verify_login(EMAIL_A, "wrongpassword") is None,
    )

    session_a1 = create_session(user_a["id"], "Amazon", "SDE")
    session_a2 = create_session(user_a["id"], "IBM", "Data Scientist")
    session_b1 = create_session(user_b["id"], "Google", "SWE")

    a_sessions = list_sessions(user_a["id"])
    a_ids = {s["id"] for s in a_sessions}
    check(
        "list_sessions(A) returns exactly A's two sessions, never B's",
        len(a_sessions) == 2
        and a_ids == {session_a1["id"], session_a2["id"]}
        and session_b1["id"] not in a_ids,
    )

    check(
        "get_session(B's session, owner_id=A) returns None",
        get_session(session_b1["id"], owner_id=user_a["id"]) is None,
    )

    check(
        "get_session(A's session, owner_id=A) returns the session",
        get_session(session_a1["id"], owner_id=user_a["id"]) is not None,
    )

    _cleanup()

    print("\nAll M8 Part A acceptance checks passed.")


if __name__ == "__main__":
    main()
