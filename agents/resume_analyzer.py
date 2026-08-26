import json
import re
import time

from groq import RateLimitError
from langchain_core.documents import Document

from models.llm_provider import get_llm
from prompts.resume_prompts import RESUME_ANALYSIS_PROMPT


def format_context(documents: list[Document]) -> str:
    return "\n\n".join(document.page_content for document in documents)


def _invoke_with_retry(llm, prompt, max_attempts: int = 3):
    """Retry on a transient rate limit -- ground-checking sends the full
    resume in every call, so a large resume/JD pair can burst past a
    provider's tokens-per-minute cap even though each call is legitimate."""
    for attempt in range(max_attempts):
        try:
            return llm.invoke(prompt)
        except RateLimitError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(15 * (attempt + 1))


def _strip_json_fence(text: str) -> str:
    """Strip a leading/trailing ```json ... ``` fence if the model added one."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    return match.group(1).strip() if match else text


def analyze_resume(resume_context: str, jd_context: str) -> dict:
    """Compare a resume against a JD and return a parsed verdict dict.

    Never raises on bad LLM output -- returns {"error": "..."} instead, so a
    malformed response cannot crash the caller.
    """
    prompt = RESUME_ANALYSIS_PROMPT.format(
        resume_context=resume_context,
        jd_context=jd_context,
    )

    llm = get_llm()
    response = _invoke_with_retry(llm, prompt)

    try:
        return json.loads(_strip_json_fence(response.content))
    except json.JSONDecodeError:
        return {"error": "Could not parse the analysis. Please try again."}


def ground_check_verdicts(verdicts: list[dict], resume_context: str) -> list[dict]:
    """Re-verify each "clearly demonstrated" verdict against the resume text.

    Only ever downgrades a verdict -- never upgrades one, never invents a new
    evidence line when downgrading.
    """
    llm = get_llm()
    checked = []

    for verdict in verdicts:
        if verdict.get("verdict") != "clearly demonstrated":
            checked.append(verdict)
            continue

        prompt = (
            "Does the RESUME below actually support this claim? "
            "Answer ONLY yes or no.\n\n"
            f"Claim: {verdict.get('evidence', '')}\n\n"
            f"RESUME:\n{resume_context}"
        )
        response = _invoke_with_retry(llm, prompt)
        supported = response.content.strip().lower().startswith("yes")

        if supported:
            checked.append(verdict)
        else:
            downgraded = dict(verdict)
            downgraded["verdict"] = "not demonstrated"
            downgraded["evidence"] = ""
            checked.append(downgraded)

    return checked
