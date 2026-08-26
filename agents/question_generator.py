from models.llm_provider import get_llm
from prompts.question_prompts import get_question_prompt, get_grounded_question_prompt
from database.db import SessionLocal
from database.models import Interview
from rag.retriever import get_retriever
from rag.citations import build_sources
import time

llm = get_llm()

def generate_question(jd):

    prompt = get_question_prompt(jd)

    response = llm.invoke(prompt)

    return response.content


def stream_question(jd, session_id):

    llm = get_llm()

    prompt = get_question_prompt(jd)

    full_question = ""

    for chunk in llm.stream(prompt):

        time.sleep(0.1)

        full_question += chunk.content

        yield chunk.content

    db = SessionLocal()

    interview = Interview(
        id=session_id,
        jd=jd,
        question=full_question
    )

    db.add(interview)
    db.commit()
    db.close()


def generate_grounded_question(
    session_id: str, topic: str | None = None, difficulty: str = "medium"
) -> dict:
    """Generate one interview question grounded in this session's documents."""
    retriever = get_retriever(session_id)
    documents = retriever.invoke(topic or "interview question")

    if not documents:
        return {
            "question": (
                "No documents have been indexed in this prep session yet. "
                "Upload material in the sidebar before generating a question."
            ),
            "topic": topic,
            "sources": [],
        }

    context = "\n\n".join(document.page_content for document in documents)

    prompt = get_grounded_question_prompt(context, topic, difficulty)

    llm = get_llm()
    response = llm.invoke(prompt)

    return {
        "question": response.content,
        "topic": topic,
        "sources": build_sources(documents),
    }