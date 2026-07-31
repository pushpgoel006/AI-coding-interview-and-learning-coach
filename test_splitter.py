from rag.loader import load_pdf
from rag.splitter import split_documents

documents = load_pdf("uploads/CN.pdf")

chunks = split_documents(documents)

print(f"Pages Loaded: {len(documents)}")
print(f"Chunks Created: {len(chunks)}")

print("\nFirst Chunk:\n")
print(chunks[0].page_content)

print("\nMetadata:\n")
print(chunks[0].metadata)