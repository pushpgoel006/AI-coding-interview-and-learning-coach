from pathlib import Path

from langchain_core.documents import Document


def build_sources(documents: list[Document]) -> list[dict]:
    seen = set()
    sources = []

    for document in documents:
        metadata = document.metadata or {}

        file_name = metadata.get("file_name")
        if not file_name:
            source = metadata.get("source")
            file_name = Path(source).name if source else "unknown"

        page = metadata.get("page", 0) + 1

        key = (file_name, page)
        if key in seen:
            continue
        seen.add(key)

        sources.append(
            {
                "file_name": file_name,
                "page": page,
                "doc_type": metadata.get("doc_type"),
            }
        )

    sources.sort(key=lambda item: (item["file_name"], item["page"]))
    return sources
