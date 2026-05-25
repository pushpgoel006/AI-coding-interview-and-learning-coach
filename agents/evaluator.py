from models.llm_provider import get_llm
from prompts.evaluation_prompt import get_evaluation_prompt
import json

llm=get_llm()

def evaluate_answer(question,answer):
    prompt1=get_evaluation_prompt(question,answer)
    response=llm.invoke(prompt1)
    parsed_response=json.loads(response.content)
    return parsed_response