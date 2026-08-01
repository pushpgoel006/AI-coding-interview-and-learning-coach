from rag.retriever import get_retriever

retriever = get_retriever()

query = "What AI projects has the candidate worked on?"

results = retriever.invoke(query)

print(f"\nQuery: {query}")

for i, doc in enumerate(results, start=1):
    print(f"\n========== Result {i} ==========")
    print(doc.page_content)
    print("\nMetadata:")
    print(doc.metadata)