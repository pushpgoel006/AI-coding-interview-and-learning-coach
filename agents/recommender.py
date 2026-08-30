from models.llm_provider import get_llm
from prompts.recommender_prompts import get_recommendation_prompt
from rag.retriever import get_retriever
from rag.citations import build_sources


def generate_recommendation(session_id: str, topic: str) -> dict:
    documents = get_retriever(session_id).invoke(topic)

    if not documents:
        return {
            "advice": (
                "No documents have been indexed in this prep session yet. "
                "Upload material in the sidebar to get grounded advice."
            ),
            "sources": [],
        }

    context = "\n\n".join(document.page_content for document in documents)

    prompt = get_recommendation_prompt(topic, context)
    response = get_llm().invoke(prompt)

    return {
        "advice": response.content,
        "sources": build_sources(documents),
    }
