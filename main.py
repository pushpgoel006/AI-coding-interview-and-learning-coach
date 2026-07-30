from fastapi import FastAPI
from pydantic import BaseModel
from agents.question_generator import generate_question
from agents.evaluator import evaluate_answer
from graphs.interview_graph import interview_graph
from database.models import Interview, Followup 
from database.db import  SessionLocal
from fastapi.responses import StreamingResponse
from agents.question_generator import stream_question
from agents.evaluator import stream_evaluation
from agents.followup_generator import generate_followup
import uuid

app = FastAPI() 
#pydantic library
class JDRequest(BaseModel):
    jd: str

class EvaluationRequest(BaseModel):
    session_id: str
    answer: str

class InterviewRequest(BaseModel):
    jd: str
    answer: str

class StreamQuestionRequest(BaseModel):
    session_id: str
    jd: str

class FollowUpRequest(BaseModel):
    session_id:str

class FollowupEvaluationRequest(BaseModel):
    followup_id: int
    answer: str


@app.get("/")
def home():

    return {
        "message": "AI Interview API Running"
    }

@app.post("/generate-question")
def generate_question_api(data: JDRequest):
    db= SessionLocal()

    question = generate_question(data.jd)

    session_id=str(uuid.uuid4())#uuid4 used as it produces random generation of ID

    interview = Interview(
        id=session_id,
        jd=data.jd,
        question=question
    )

    db.add(interview)
    db.commit()
    db.close()

    return {
        "session_id": session_id,
        "question": question
    }

@app.post("/evaluate-answer")
def evaluate_answer_api(data: EvaluationRequest):
    db=SessionLocal()
    interview=db.query(Interview).filter(
        Interview.id==data.session_id
        ).first()
    
    if interview is None:
        db.close()
        return {
        "error": "Invalid session ID"
        }

    result = evaluate_answer(
        interview.question,
        data.answer
    )   
    interview.answer= data.answer
    interview.score=result["score"]
    question=interview.question
    db.commit()
    db.close()

    return {
        "question": question,
        "evaluation": result
    }



@app.post("/start-interview")
def start_interview(data: InterviewRequest):

    result = interview_graph.invoke({

        "jd": data.jd,
        "answer": data.answer
    })

    return result

# adding a new endpoint for SSE streaming
@app.post("/stream-question")
def stream_question_api(data: StreamQuestionRequest):
    return StreamingResponse(
        stream_question(
            data.jd,
            data.session_id
            ),
        media_type="text/plain"
    )


#firstly creating a session id which can be used to save the question generated in chunks
@app.post("/create-session")
def create_session(data: JDRequest):

    session_id = str(uuid.uuid4())

    return {
        "session_id": session_id
    }

@app.post("/stream-evaluation")
def stream_evaluation_api(data: EvaluationRequest):

    db = SessionLocal()

    interview = db.query(Interview).filter(
        Interview.id == data.session_id
    ).first()

    if interview is None:
        db.close()
        return {
            "error": "Invalid session ID"
        }

    return StreamingResponse(
        stream_evaluation(
            interview.question,
            data.answer
        ),
        media_type="text/plain"
    )

@app.post("/followup-question")
def followup_question_api(data: FollowUpRequest):

    db = SessionLocal()

    interview = db.query(Interview).filter(
        Interview.id == data.session_id
    ).first()

    if interview is None:

        db.close()

        return {
            "error": "Invalid session ID"
        }

    followup_question = generate_followup(
        interview.question,
        interview.answer,
        interview.score
    )
    existing_followups = db.query(Followup).filter(
        Followup.interview_id == interview.id
        ).count()
    
    followup_number = existing_followups + 1
    

    new_followup = Followup(
        interview_id=interview.id,
        question=followup_question,
        followup_number=followup_number
    )
    db.add(new_followup)
    db.commit()
    db.refresh(new_followup)

    db.close()

    return {
    "followup_id": new_followup.id,
    "followup_number": new_followup.followup_number,
    "question": new_followup.question
    }

@app.post("/evaluate-followup")
def evaluate_followup_api(
    data: FollowupEvaluationRequest):
    db = SessionLocal()

    followup = db.query(Followup).filter(
        Followup.id == data.followup_id
    ).first()
    
    if followup is None:
        db.close()
        return {
            "error": "Invalid followup ID"
        }

@app.post("/stream-followup-evaluation")
def stream_followup_evaluation(
    data: FollowupEvaluationRequest):
    db = SessionLocal()

    followup = db.query(Followup).filter(
        Followup.id == data.followup_id
    ).first()

    if followup is None:
        db.close()
        return{
            "error":"Invalid Follow Up"
        }
    
    return StreamingResponse(

        stream_evaluation(
            followup.question,
            data.answer
        ),
        media_type="text/plain")