from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.evaluator import evaluate_answer, evaluate_grounded_answer
from agents.question_generator import generate_question, generate_grounded_question
from agents.followup_generator import generate_grounded_followup
from services import interview_service


class InterviewState(TypedDict):
    jd: str
    question: str
    answer: str
    evaluation: dict
    session_id: str
    topic: str
    difficulty: str
    sources: list[dict]
    strengths: str
    weaknesses: str
    ideal_answer: str
    grounded: bool
    interview_id: str
    followup_number: int
    max_followups: int
    messages: list[dict]
    original_question: str
    original_answer: str
    next_question: str | None

#node 1(question wali)
def question_node(state: InterviewState):

    if state.get("question"):
        return {}

    if state.get("session_id"):
        result = generate_grounded_question(
            state["session_id"],
            topic=state.get("topic"),
            difficulty=state.get("difficulty", "medium"),
        )
        return {
            "question": result["question"],
            "topic": result["topic"],
            "sources": result["sources"],
        }

    question = generate_question(state["jd"])

    return {
        "question": question
    }

#node2(evaluation wali)
def evaluation_node(state: InterviewState):

    if state.get("session_id"):
        result = evaluate_grounded_answer(
            state["session_id"],
            state["question"],
            state["answer"],
        )
        update = {
            "evaluation": result,
            "strengths": result.get("strengths", ""),
            "weaknesses": result.get("weaknesses", ""),
            "ideal_answer": result.get("ideal_answer", ""),
            "sources": result.get("sources", state.get("sources", [])),
            "grounded": result.get("grounded", False),
        }
        if not state.get("followup_number"):
            update["original_question"] = state["question"]
            update["original_answer"] = state["answer"]
        return update

    evaluation = evaluate_answer(
        state["question"],
        state["answer"]
    )

    return {
        "evaluation": evaluation
    }


def store_node(state: InterviewState):
    evaluation = state.get("evaluation") or {}
    if "error" in evaluation:
        return {}

    saved = interview_service.record_interview(
        session_id=state["session_id"],
        topic=state.get("topic"),
        question=state["question"],
        answer=state["answer"],
        score=evaluation.get("score", 0),
        strengths=state.get("strengths", ""),
        weaknesses=state.get("weaknesses", ""),
        ideal_answer=state.get("ideal_answer", ""),
    )

    return {"interview_id": saved["id"]}


def store_followup_node(state: InterviewState):
    evaluation = state.get("evaluation") or {}
    if "error" in evaluation:
        return {}

    interview_service.record_followup(
        interview_id=state["interview_id"],
        followup_number=state["followup_number"],
        topic=state.get("topic"),
        question=state["question"],
        answer=state["answer"],
        score=evaluation.get("score", 0),
    )

    return {}


def followup_node(state: InterviewState):
    current_number = state.get("followup_number", 0)
    max_followups = state.get("max_followups", 3)

    if current_number >= max_followups:
        return {"next_question": None}

    evaluation = state.get("evaluation") or {}
    if "error" in evaluation:
        return {"next_question": None}

    messages = list(state.get("messages", []))
    if current_number > 0:
        messages.append({"question": state["question"], "answer": state["answer"]})

    result = generate_grounded_followup(
        state["session_id"],
        original_question=state["original_question"],
        original_answer=state["original_answer"],
        history=messages,
        latest_answer=state["answer"],
        score=evaluation.get("score", 0),
    )

    return {
        "next_question": result["question"],
        "sources": result.get("sources", state.get("sources", [])),
        "messages": messages,
    }


def route_after_evaluation(state: InterviewState):
    if not state.get("session_id"):
        return END

    if state.get("followup_number", 0) > 0:
        return "store_followup"

    return "store"


graph = StateGraph(InterviewState)
#defining the nodes 1 and 2
graph.add_node("question_generator", question_node)

graph.add_node("evaluation", evaluation_node)

graph.add_node("store", store_node)

graph.add_node("store_followup", store_followup_node)

graph.add_node("followup", followup_node)
#here edegs define the workflow
graph.set_entry_point("question_generator")

graph.add_edge("question_generator", "evaluation")

graph.add_conditional_edges(
    "evaluation",
    route_after_evaluation,
    {
        "store": "store",
        "store_followup": "store_followup",
        END: END,
    },
)

graph.add_edge("store", "followup")
graph.add_edge("store_followup", "followup")
graph.add_edge("followup", END)

interview_graph = graph.compile()
