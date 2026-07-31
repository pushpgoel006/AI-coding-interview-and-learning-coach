from rag.embeddings import get_embedding_model

embedding_model = get_embedding_model()

vector = embedding_model.embed_query("I love artificial intelligence")

print(f"Vector Length: {len(vector)}")
print(vector[:10])  # First 10 values