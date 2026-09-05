from typing import TypedDict

from langgraph.graph import StateGraph, END

from rag.leetcode_client import fetch_problem
from agents.dsa_evaluator import evaluate_dsa_submission
from services import dsa_service


class DsaState(TypedDict):
    session_id: str
    topic: str
    difficulty: str
    slug: str
    title: str
    statement: str
    source: str
    code: str
    language: str
    evaluation: dict


def fetch_problem_node(state: DsaState):
    result = fetch_problem(state["topic"], state["difficulty"])

    return {
        "slug": result["slug"],
        "title": result["title"],
        "statement": result["statement"],
        "source": result["source"],
    }


def evaluate_node(state: DsaState):
    result = evaluate_dsa_submission(
        state["statement"],
        state["code"],
        state.get("language", "python"),
    )

    return {"evaluation": result}


def store_node(state: DsaState):
    evaluation = state.get("evaluation") or {}
    if "error" in evaluation:
        return {}

    dsa_service.record_attempt(
        session_id=state["session_id"],
        topic=state.get("topic"),
        difficulty=state.get("difficulty"),
        problem_slug=state.get("slug"),
        problem_title=state.get("title"),
        code=state["code"],
        language=state.get("language", "python"),
        score=evaluation.get("score", 0),
        correctness_notes=evaluation.get("correctness_notes", ""),
        complexity_notes=evaluation.get("complexity_notes", ""),
        suggestions=evaluation.get("suggestions", ""),
    )

    return {}


def route_start(state: DsaState):
    if state.get("code"):
        return "evaluate"
    return "fetch_problem"


graph = StateGraph(DsaState)

graph.add_node("fetch_problem", fetch_problem_node)
graph.add_node("evaluate", evaluate_node)
graph.add_node("store", store_node)

graph.set_conditional_entry_point(
    route_start,
    {"fetch_problem": "fetch_problem", "evaluate": "evaluate"},
)

graph.add_edge("fetch_problem", END)
graph.add_edge("evaluate", "store")
graph.add_edge("store", END)

dsa_graph = graph.compile()
