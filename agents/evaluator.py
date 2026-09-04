import re

from models.llm_provider import get_llm
from prompts.evaluation_prompt import get_evaluation_prompt, get_grounded_evaluation_prompt
from rag.retriever import get_retriever
from rag.citations import build_sources
import json
import time

llm=get_llm()


def _strip_json_fence(text: str) -> str:
    text = text.strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        return brace_match.group(0)

    return text


def evaluate_answer(question,answer):
    prompt1=get_evaluation_prompt(question,answer)

    for attempt in range(3):
        response = llm.invoke(prompt1)
        try:
            return json.loads(_strip_json_fence(response.content))
        except json.JSONDecodeError:
            continue

    return {"error": "Could not parse the evaluation. Please try again."}

def stream_evaluation(question, answer):
    prompt=get_evaluation_prompt(
        question,
        answer
    )
    if len(answer.strip()) < 5:
        return {
            "score": 0,
            "strengths": "",
            "weaknesses": "Answer is too short to evaluate.",
            "ideal_answer": "Provide a meaningful answer to the question."
        }
    for chunk in llm.stream(prompt):
        time.sleep(0.1)
        yield chunk.content


def ground_check_ideal_answer(ideal_answer: str, context: str) -> bool:
    if not ideal_answer or not context:
        return False

    prompt = (
        "Does the CONTEXT below actually support this ideal answer? "
        "Answer ONLY yes or no.\n\n"
        f"Ideal answer: {ideal_answer}\n\n"
        f"CONTEXT:\n{context}"
    )
    response = get_llm().invoke(prompt)
    return response.content.strip().lower().startswith("yes")


def evaluate_grounded_answer(session_id: str, question: str, answer: str) -> dict:
    documents = get_retriever(session_id).invoke(question)
    context = "\n\n".join(document.page_content for document in documents)

    prompt = get_grounded_evaluation_prompt(question, answer, context)
    llm = get_llm()

    parsed = None
    for attempt in range(3):
        response = llm.invoke(prompt)
        try:
            parsed = json.loads(_strip_json_fence(response.content))
            break
        except json.JSONDecodeError:
            continue

    if parsed is None:
        return {"error": "Could not parse the evaluation. Please try again."}

    parsed["sources"] = build_sources(documents)
    parsed["grounded"] = ground_check_ideal_answer(parsed.get("ideal_answer", ""), context)

    return parsed