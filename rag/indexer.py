"""High-level document-indexing operations exposed to application clients.

This module is the only indexing API that the Streamlit application needs. It
composes the existing loader, splitter, and vector-store modules without
duplicating their implementation details.
"""

from collections.abc import Iterable
from pathlib import Path

from rag.loader import load_pdf
from rag.retriever import load_vector_store
from rag.splitter import split_documents
from rag.vector_store import create_vector_store


def index_documents(
    file_paths: Iterable[str | Path], session_id: str, doc_type: str = "company"
) -> int:
    """Load, split, and add uploaded PDFs to a prep session's index.

    Args:
        file_paths: Paths to PDF files that have already been saved locally.
        session_id: The prep session these documents belong to.
        doc_type: One of company / jd / resume / notes / experience.

    Returns:
        The number of chunks created and stored.

    Raises:
        FileNotFoundError: If an expected PDF does not exist.
        ValueError: If no paths or no extractable text were provided.
    """
    paths = [Path(path) for path in file_paths]
    if not paths:
        raise ValueError("Select at least one PDF to index.")

    all_chunks = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"Document not found: {path}")

        documents = load_pdf(str(path))
        for document in documents:
            document.metadata = {
                **document.metadata,
                "source": str(path),
                "file_name": path.name,
                "session_id": session_id,
                "doc_type": doc_type,
            }
        all_chunks.extend(split_documents(documents))

    if not all_chunks:
        raise ValueError("No text could be extracted from the uploaded documents.")

    # A session accumulates documents (resume, JD, notes, ...) over multiple
    # uploads, so the existing index is never wiped before adding new chunks.
    create_vector_store(all_chunks)
    return len(all_chunks)


def list_indexed_documents(session_id: str) -> list[str]:
    """Return distinct file names indexed for this prep session."""
    vector_store = load_vector_store()
    metadata = vector_store.get(
        where={"session_id": session_id}, include=["metadatas"]
    ).get("metadatas", [])

    return sorted(
        {
            item.get("file_name") or Path(item["source"]).name
            for item in metadata
            if item and (item.get("file_name") or item.get("source"))
        }
    )


def clear_session_index(session_id: str) -> None:
    """Remove only this prep session's chunks from the vector store."""
    vector_store = load_vector_store()
    found = vector_store.get(where={"session_id": session_id})
    ids = found.get("ids", [])
    if ids:
        vector_store.delete(ids=ids)


def clear_index() -> None:
    """Developer/debug utility: wipe the entire persistent Chroma collection
    across every session. Not called by the UI."""
    vector_store = load_vector_store()
    vector_store.delete_collection()
