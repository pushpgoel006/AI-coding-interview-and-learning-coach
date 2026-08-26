"""Owns PrepSession and Document rows. The only module allowed to touch them.

Every function returns plain dicts, never ORM objects — the db session
closes before the caller sees the result, so a returned ORM object would
raise DetachedInstanceError on attribute access.
"""
import uuid
from datetime import datetime

from database.db import get_db
from database.models import Document, PrepSession


def _session_to_dict(session: PrepSession) -> dict:
    return {
        "id": session.id,
        "company_name": session.company_name,
        "role": session.role,
        "jd_text": session.jd_text,
        "status": session.status,
        "created_at": session.created_at,
    }


def _document_to_dict(document: Document) -> dict:
    return {
        "id": document.id,
        "session_id": document.session_id,
        "file_name": document.file_name,
        "file_path": document.file_path,
        "doc_type": document.doc_type,
        "chunk_count": document.chunk_count,
        "indexed_at": document.indexed_at,
    }


def create_session(company_name: str, role: str, jd_text: str = "") -> dict:
    with get_db() as db:
        session = PrepSession(
            id=str(uuid.uuid4()),
            company_name=company_name,
            role=role,
            jd_text=jd_text,
        )
        db.add(session)
        db.flush()
        return _session_to_dict(session)


def list_sessions(include_archived: bool = False) -> list[dict]:
    with get_db() as db:
        query = db.query(PrepSession)
        if not include_archived:
            query = query.filter(PrepSession.status != "archived")
        sessions = query.order_by(PrepSession.created_at.desc()).all()
        return [_session_to_dict(s) for s in sessions]


def get_session(session_id: str) -> dict | None:
    with get_db() as db:
        session = db.query(PrepSession).filter(PrepSession.id == session_id).first()
        return _session_to_dict(session) if session else None


def archive_session(session_id: str) -> None:
    with get_db() as db:
        session = db.query(PrepSession).filter(PrepSession.id == session_id).first()
        if session:
            session.status = "archived"


def record_document(
    session_id: str,
    file_name: str,
    file_path: str,
    doc_type: str,
    chunk_count: int,
) -> dict:
    with get_db() as db:
        document = (
            db.query(Document)
            .filter(Document.session_id == session_id, Document.file_name == file_name)
            .first()
        )
        if document:
            document.file_path = file_path
            document.doc_type = doc_type
            document.chunk_count = chunk_count
            document.indexed_at = datetime.utcnow()
        else:
            document = Document(
                session_id=session_id,
                file_name=file_name,
                file_path=file_path,
                doc_type=doc_type,
                chunk_count=chunk_count,
            )
            db.add(document)
        db.flush()
        return _document_to_dict(document)


def list_documents(session_id: str) -> list[dict]:
    with get_db() as db:
        documents = (
            db.query(Document)
            .filter(Document.session_id == session_id)
            .order_by(Document.indexed_at.asc())
            .all()
        )
        return [_document_to_dict(d) for d in documents]


def delete_session_documents(session_id: str) -> None:
    with get_db() as db:
        db.query(Document).filter(Document.session_id == session_id).delete()
