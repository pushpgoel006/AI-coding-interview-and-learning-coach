from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# it splits data into chunks
def split_documents(documents: list[Document]) -> list[Document]:
    

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
    )

    chunks = splitter.split_documents(documents)

    return chunks