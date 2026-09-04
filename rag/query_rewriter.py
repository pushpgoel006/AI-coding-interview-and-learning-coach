from models.llm_provider import get_llm
from prompts.query_rewrite_prompt import QUERY_REWRITE_PROMPT


def rewrite_query(question: str) -> str:
    prompt = QUERY_REWRITE_PROMPT.format(question=question)
    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content.strip()
