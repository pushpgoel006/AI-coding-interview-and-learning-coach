from langchain_chroma import Chroma
from langchain_core.documents import Document

from rag.config import CHROMA_COLLECTION, CHROMA_DIR
from rag.embeddings import get_embedding_model


class SourceAwareRetriever:
    """Retrieve top chunks from each indexed source for multi-document queries."""

    def __init__(self, vector_store: Chroma, session_id: str, k: int = 4):
        self.vector_store = vector_store
        self.session_id = session_id
        self.k = k

    def _sources(self) -> list[str]:
        metadata = self.vector_store.get(
            where={"session_id": self.session_id}, include=["metadatas"]
        ).get("metadatas", [])
        return sorted(
            {
                item["source"]
                for item in metadata
                if item and item.get("source")
            }
        )

    def invoke(self, query: str):
        sources = self._sources()

        # Preserve the existing global top-k behaviour for a single document.
        if len(sources) <= 1:
            return self.vector_store.similarity_search(
                query, k=self.k, filter={"session_id": self.session_id}
            )

        # Each source receives a semantic search, so one document cannot use
        # every global top-k slot and starve a comparison question of context.
        chunks_per_source = max(1, self.k // len(sources))
        documents = []
        for source in sources:
            documents.extend(
                self.vector_store.similarity_search(
                    query,
                    k=chunks_per_source,
                    filter={
                        "$and": [
                            {"session_id": self.session_id},
                            {"source": source},
                        ]
                    },
                )
            )

        return documents


def load_vector_store():
    """Open the persistent vector store used by the RAG graph."""
    embedding_model = get_embedding_model()
    vector_store = Chroma(
        collection_name=CHROMA_COLLECTION,
        persist_directory=str(CHROMA_DIR),
        embedding_function=embedding_model,
    )
    return vector_store


def get_retriever(session_id: str, k: int = 4):
    """Return a source-aware retriever for the RAG graph."""
    vector_store = load_vector_store()
    return SourceAwareRetriever(vector_store, session_id, k=k)


def get_documents_by_doc_type(session_id: str, doc_type: str) -> list[Document]:
    vector_store = load_vector_store()

    result = vector_store.get(
        where={"$and": [{"session_id": session_id}, {"doc_type": doc_type}]},
        include=["metadatas", "documents"],
    )

    documents = [
        Document(page_content=content, metadata=metadata)
        for content, metadata in zip(result["documents"], result["metadatas"])
    ]

    documents.sort(key=lambda document: document.metadata.get("page", 0))

    return documents

