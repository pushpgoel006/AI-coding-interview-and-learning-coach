from models.llm_provider import get_llm
from prompts.followup_prompts import get_followup_prompt, get_grounded_followup_prompt
from rag.retriever import get_retriever
from rag.citations import build_sources

llm = get_llm()

def generate_followup(question, answer, score):

    prompt = get_followup_prompt(
        question,
        answer,
        score
    )

    response = llm.invoke(prompt)

    return response.content


def generate_grounded_followup(
    session_id: str,
    original_question: str,
    original_answer: str,
    history: list[dict],
    latest_answer: str,
    score: int,
) -> dict:
    documents = get_retriever(session_id).invoke(original_question)

    if not documents:
        return {
            "question": (
                "No documents have been indexed in this prep session yet. "
                "Upload material in the sidebar before generating a follow-up."
            ),
            "sources": [],
        }

    context = "\n\n".join(document.page_content for document in documents)

    prompt = get_grounded_followup_prompt(
        context=context,
        original_question=original_question,
        original_answer=original_answer,
        history=history,
        latest_answer=latest_answer,
        score=score,
    )

    response = get_llm().invoke(prompt)

    return {
        "question": response.content,
        "sources": build_sources(documents),
    }