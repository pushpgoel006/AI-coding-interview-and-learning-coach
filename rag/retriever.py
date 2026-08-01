from langchain_chroma import Chroma
from rag.embeddings import get_embedding_model
#retreives the vector chunks
def load_vector_store():
    embedding_model=get_embedding_model()
    vector_store=Chroma(
        persist_directory="chroma_db",
        embedding_function=embedding_model,
    )
    return vector_store

#selects the chunks that has to be used 
def get_retriever(k:int=4):
    vector_store= load_vector_store()
    retriever=vector_store.as_retriever(
        search_kwargs={"k":k}
    )
    return retriever

