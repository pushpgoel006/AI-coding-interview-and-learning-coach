#helps in connection sqlite, create engine and save sessions
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()


def _with_psycopg_driver(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _with_psycopg_driver(os.getenv("DATABASE_URL", "sqlite:///./interviews.db"))

# engine acts as  a manager between python and the database
engine = create_engine(DATABASE_URL)

# temp converstiaon withdatabase
SessionLocal = sessionmaker(bind=engine)

# a base class needed whenever you need to create a class
Base = declarative_base()


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()