from rag.retriever import get_retriever
from rag.grader import grade_documents

query = "What programming languages does Pushp know?"

retriever = get_retriever()

documents = retriever.invoke(query)

print("Retrieved Documents:\n")

for i, doc in enumerate(documents, start=1):
    print(f"---------- Chunk {i} ----------")
    print(doc.page_content)
    print()

grade = grade_documents(
    query,
    documents,
)

print("Grade:", grade)