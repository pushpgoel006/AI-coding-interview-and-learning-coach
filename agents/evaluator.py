from models.llm_provider import get_llm
from prompts.evaluation_prompt import get_evaluation_prompt
import json
import time

llm=get_llm()

def evaluate_answer(question,answer):
    prompt1=get_evaluation_prompt(question,answer)
    response=llm.invoke(prompt1)
    parsed_response=json.loads(response.content)
    return parsed_response

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