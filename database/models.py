#helps defining table structure
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, JSON
from database.db import Base
from  sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True)
    email         = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name  = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("PrepSession", back_populates="owner")


class PrepSession(Base):
    __tablename__ = "prep_sessions"

    id           = Column(String, primary_key=True)
    company_name = Column(String, nullable=False)
    role         = Column(String, nullable=False)
    jd_text      = Column(Text, default="")
    status       = Column(String, default="active")
    created_at   = Column(DateTime, default=datetime.utcnow)

    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    owner    = relationship("User", back_populates="sessions")

    documents  = relationship("Document", back_populates="session",
                              cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="session")


class Document(Base):
    __tablename__ = "documents"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    session_id  = Column(String, ForeignKey("prep_sessions.id"))
    file_name   = Column(String)
    file_path   = Column(String)
    doc_type    = Column(String)
    chunk_count = Column(Integer, default=0)
    indexed_at  = Column(DateTime, default=datetime.utcnow)

    session = relationship("PrepSession", back_populates="documents")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String, primary_key=True)

    jd = Column(Text)

    question = Column(Text)

    answer = Column(Text)

    score = Column(Integer)

    session_id = Column(String, ForeignKey("prep_sessions.id"), nullable=True)
    session    = relationship("PrepSession", back_populates="interviews")

    topic        = Column(String, nullable=True)
    ideal_answer = Column(Text, default="")
    strengths    = Column(Text, default="")
    weaknesses   = Column(Text, default="")
    created_at   = Column(DateTime, default=datetime.utcnow)

    followups= relationship(
        "Followup",
        back_populates="interview"
    )


class Followup(Base):
    __tablename__ = "followups"

    id=Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    interview_id=Column(
        String,
        ForeignKey("interviews.id")

    )

    question=Column(Text)
    answer=Column(Text)
    score=Column(Integer)
    followup_number= Column(Integer)
    topic      = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    interview = relationship(
        "Interview",
        back_populates="followups"
    )


class ResumeReview(Base):
    __tablename__ = "resume_reviews"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    session_id     = Column(String, ForeignKey("prep_sessions.id"))
    overall_score  = Column(Integer)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    suggestions    = Column(Text, default="")
    created_at     = Column(DateTime, default=datetime.utcnow)


class DsaAttempt(Base):
    __tablename__ = "dsa_attempts"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    session_id        = Column(String, ForeignKey("prep_sessions.id"))
    topic             = Column(String, nullable=True)
    difficulty        = Column(String, nullable=True)
    problem_slug      = Column(String, nullable=True)
    problem_title     = Column(String, nullable=True)
    code              = Column(Text)
    language          = Column(String, default="python")
    score             = Column(Integer)
    correctness_notes = Column(Text, default="")
    complexity_notes  = Column(Text, default="")
    suggestions       = Column(Text, default="")
    created_at        = Column(DateTime, default=datetime.utcnow)

    session = relationship("PrepSession")
