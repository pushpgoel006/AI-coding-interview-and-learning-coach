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


def index_documents(file_paths: Iterable[str | Path]) -> int:
    """Load, split, and replace the persistent index with uploaded PDFs.

    Args:
        file_paths: Paths to PDF files that have already been saved locally.

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
            }
        all_chunks.extend(split_documents(documents))

    if not all_chunks:
        raise ValueError("No text could be extracted from the uploaded documents.")

    # Processing is based on the current Streamlit selection. Replacing the
    # old collection prevents stale files and repeated button clicks from
    # affecting retrieval for the newly uploaded document set.
    clear_index()
    create_vector_store(all_chunks)
    return len(all_chunks)


def list_indexed_documents() -> list[str]:
    """Return distinct file names currently represented in the vector store."""
    vector_store = load_vector_store()
    metadata = vector_store.get(include=["metadatas"]).get("metadatas", [])

    return sorted(
        {
            item.get("file_name") or Path(item["source"]).name
            for item in metadata
            if item and (item.get("file_name") or item.get("source"))
        }
    )


def clear_index() -> None:
    """Remove the application's persistent Chroma collection."""
    vector_store = load_vector_store()
    vector_store.delete_collection()
