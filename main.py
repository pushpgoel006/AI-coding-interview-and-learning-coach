from fastapi import FastAPI
from pydantic import BaseModel
from agents.question_generator import generate_question

app = FastAPI() 

class JDRequest(BaseModel):
    jd: str

@app.get("/")
def home():

    return {
        "message": "AI Interview API Running"
    }

@app.post("/generate-question")
def generate_question_api(data: JDRequest):

    # sending JD to AI function
    question = generate_question(data.jd)

    # returning response
    return {
        "question": question
    }