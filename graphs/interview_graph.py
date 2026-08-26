from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.evaluator import evaluate_answer, evaluate_grounded_answer
from agents.question_generator import generate_question, generate_grounded_question
from services import interview_service


class InterviewState(TypedDict):
    jd: str
    question: str
    answer: str
    evaluation: dict
    # Optional: only present on the grounded path (a real prep session).
    # Every node reads these with .get(...), never [...], so the legacy
    # {"jd": ..., "answer": ...} call shape main.py uses is untouched.
    session_id: str
    topic: str
    difficulty: str
    sources: list[dict]
    strengths: str
    weaknesses: str
    ideal_answer: str
    grounded: bool

#node 1(question wali)
def question_node(state: InterviewState):

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
        return {
            "evaluation": result,
            "strengths": result.get("strengths", ""),
            "weaknesses": result.get("weaknesses", ""),
            "ideal_answer": result.get("ideal_answer", ""),
            "sources": result.get("sources", state.get("sources", [])),
            "grounded": result.get("grounded", False),
        }

    evaluation = evaluate_answer(
        state["question"],
        state["answer"]
    )

    return {
        "evaluation": evaluation
    }


def store_node(state: InterviewState):
    """Persist the interview -- only reachable on the grounded path, since
    there is no session to store against otherwise."""
    evaluation = state.get("evaluation") or {}
    if "error" in evaluation:
        return {}

    interview_service.record_interview(
        session_id=state["session_id"],
        topic=state.get("topic"),
        question=state["question"],
        answer=state["answer"],
        score=evaluation.get("score", 0),
        strengths=state.get("strengths", ""),
        weaknesses=state.get("weaknesses", ""),
        ideal_answer=state.get("ideal_answer", ""),
    )

    return {}


def route_after_evaluation(state: InterviewState):
    if state.get("session_id"):
        return "store"

    return END


graph = StateGraph(InterviewState)
#defining the nodes 1 and 2
graph.add_node("question_generator", question_node)

graph.add_node("evaluation", evaluation_node)

graph.add_node("store", store_node)
#here edegs define the workflow
graph.set_entry_point("question_generator")

graph.add_edge("question_generator", "evaluation")

graph.add_conditional_edges(
    "evaluation",
    route_after_evaluation,
    {
        "store": "store",
        END: END,
    },
)

graph.add_edge("store", END)

interview_graph = graph.compile()
