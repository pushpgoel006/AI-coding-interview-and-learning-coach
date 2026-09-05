import json
import re

from models.llm_provider import get_llm
from prompts.dsa_prompts import get_dsa_evaluation_prompt


def _strip_json_fence(text: str) -> str:
    text = text.strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        return brace_match.group(0)

    return text


def evaluate_dsa_submission(problem_statement: str, code: str, language: str) -> dict:
    prompt = get_dsa_evaluation_prompt(problem_statement, code, language)
    llm = get_llm()

    for attempt in range(3):
        response = llm.invoke(prompt)
        try:
            return json.loads(_strip_json_fence(response.content))
        except json.JSONDecodeError:
            continue

    return {"error": "Could not parse the evaluation. Please try again."}
