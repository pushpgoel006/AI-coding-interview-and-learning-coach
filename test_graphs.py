from graphs.rag_graph import rag_graph

state = {
    "question": """
These are the necessities for a Data Analyst job:

- Extracting data from primary and secondary sources and removing corrupted data
- Ensuring that the data is accurate and high-quality
- Developing and managing data systems and databases
- Establishing KPIs that provide actionable insights
- Using data to analyse trends that help inform business policies and decisions
- Collaborating with engineers and developers to develop and streamline data governance strategies

Is Pushp capable of this?
"""
}

result = rag_graph.invoke(state)

print("\nFinal Answer:\n")
print(result["answer"])