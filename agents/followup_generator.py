from models.llm_provider import get_llm
from prompts.followup_prompts import get_followup_prompt

llm = get_llm()

def generate_followup(question, answer, score):

    prompt = get_followup_prompt(
        question,
        answer,
        score
    )

    response = llm.invoke(prompt)

    return response.content