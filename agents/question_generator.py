from  models.llm_provider import get_llm
from prompts.question_prompts import get_question_prompt
llm=get_llm()
def generate_question(jd):
    prompt = get_question_prompt(jd)

    response=llm.invoke(prompt)
    return response.content
