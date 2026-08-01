from rag.loader import load_pdf
from rag.splitter import split_documents
from rag.vector_store import create_vector_store

documents = load_pdf("uploads/Pushp_Goel_Resume.pdf")
chunks = split_documents(documents)

vector_store = create_vector_store(chunks)

print("Vector store created successfully!")