from langchain_chroma import Chroma

from rag.config import CHROMA_COLLECTION, CHROMA_DIR
from rag.embeddings import get_embedding_model


def create_vector_store(chunks):
    """Add document chunks to the persistent document collection."""
    embeddings = get_embedding_model()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION,
        persist_directory=str(CHROMA_DIR),
    )
    return vector_store
