from models.llm_provider import get_llm

llm = get_llm()

for chunk in llm.stream("Explain overfitting in one paragraph"):
    print(chunk.content, end="", flush=True)