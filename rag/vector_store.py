from langchain_chroma import Chroma
from rag.embeddings import get_embedding_model

#only reason this is here to just store what i get from embedding the vectors it stores here thats it mf
def create_vector_store(chunks):
    embeddings=get_embedding_model()
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="chroma_db"
    )
    return vector_store
