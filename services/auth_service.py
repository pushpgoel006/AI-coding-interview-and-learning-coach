import uuid

import bcrypt

from database.db import get_db
from database.models import User

_DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "created_at": user.created_at,
    }


def register_user(email: str, password: str, display_name: str) -> dict:
    email = email.strip()
    display_name = display_name.strip()

    if not email or "@" not in email:
        raise ValueError("Enter a valid email address.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not display_name:
        raise ValueError("Display name is required.")

    with get_db() as db:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("An account with this email already exists.")

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            password_hash=password_hash.decode("utf-8"),
            display_name=display_name,
        )
        db.add(user)
        db.flush()
        return _user_to_dict(user)


def verify_login(email: str, password: str) -> dict | None:
    email = email.strip()

    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            bcrypt.checkpw(password.encode("utf-8"), _DUMMY_HASH)
            return None

        if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            return None

        return _user_to_dict(user)


def get_user(user_id: str) -> dict | None:
    with get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return _user_to_dict(user) if user else None
