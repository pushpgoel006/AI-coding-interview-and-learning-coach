from fastapi import FastAPI
from pydantic import BaseModel
from agents.question_generator import generate_question
from agents.evaluator import evaluate_answer
from graphs.interview_graph import interview_graph

app = FastAPI() 

class JDRequest(BaseModel):
    jd: str

class EvaluationRequest(BaseModel):
    question: str
    answer: str

class InterviewRequest(BaseModel):
    jd: str
    answer: str
@app.get("/")
def home():

    return {
        "message": "AI Interview API Running"
    }

@app.post("/generate-question")
def generate_question_api(data: JDRequest):
    question = generate_question(
        data.jd
    )
    return {
        "question": question
    }

@app.post("/evaluate-answer")
def evaluate_answer_api(data: EvaluationRequest):

    result = evaluate_answer(
        data.question,
        data.answer
    )

    return {
        "evaluation": result
    }


@app.post("/start-interview")
def start_interview(data: InterviewRequest):

    result = interview_graph.invoke({

        "jd": data.jd,
        "answer": data.answer
    })

    return result