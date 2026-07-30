from models.llm_provider import get_llm
from prompts.question_prompts import get_question_prompt
from database.db import SessionLocal
from database.models import Interview
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