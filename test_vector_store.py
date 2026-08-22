from rag.loader import load_pdf
from rag.splitter import split_documents
from rag.vector_store import create_vector_store

documents = load_pdf("uploads/harsh.pdf")

print("Documents loaded:", len(documents))

print("\nExtracted text:")
print(repr(documents[0].page_content))

chunks = split_documents(documents)

print("\nChunks created:", len(chunks))

if not chunks:
    print("ERROR: No text was extracted from the PDF.")
    exit()

vector_store = create_vector_store(chunks)

print("Vector store created successfully!")