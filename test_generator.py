from rag.retriever import get_retriever
from rag.generator import generate_answer

query = "From which college does pushp goel is?"

retriever = get_retriever()

documents = retriever.invoke(query)

answer = generate_answer(
    query,
    documents,
)

print("\nQuestion:\n")
print(query)

print("\nAnswer:\n")
print(answer)