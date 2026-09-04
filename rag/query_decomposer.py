from models.llm_provider import get_llm
from prompts.decompose_prompt import DECOMPOSE_PROMPT


def decompose_question(question: str) -> list[str]:
    prompt = DECOMPOSE_PROMPT.format(question=question)
    llm = get_llm()
    response = llm.invoke(prompt)

    lines = [line.strip() for line in response.content.strip().split("\n")]
    lines = [line for line in lines if line]

    if not lines or len(lines) > 5:
        return [question]

    return lines
