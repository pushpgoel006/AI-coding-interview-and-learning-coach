"""LangGraph workflow for the resume checker.

This module only orchestrates. Every node delegates to a function in the
``rag``, ``agents``, or ``services`` packages.

State flow (the shared "backpack"):
    {session_id}
      -> retrieve            adds resume_documents, jd_documents
      -> route                missing -> missing_documents, else -> analyze
      -> analyze              adds analysis, resume_context
      -> route                error -> analysis_failed, else -> ground_check
      -> ground_check         adds verdicts (possibly downgraded)
      -> store                adds review
"""

from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from rag.retriever import get_documents_by_doc_type
from agents.resume_analyzer import format_context, analyze_resume, ground_check_verdicts
from services.resume_service import save_review

ALLOWED_VERDICTS = {"clearly demonstrated", "partially demonstrated", "not demonstrated"}


class ResumeGraphState(TypedDict):
    session_id: str
    resume_documents: list[Document]
    jd_documents: list[Document]
    resume_context: str
    analysis: dict
    review: dict   # the persisted, UI-ready result


# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------

def retrieve_node(state: ResumeGraphState):
    """Fetch every resume chunk and every JD chunk for this session."""
    print(">>> RESUME RETRIEVE NODE")

    resume_documents = get_documents_by_doc_type(state["session_id"], "resume")
    jd_documents = get_documents_by_doc_type(state["session_id"], "jd")

    print("Resume chunks:", len(resume_documents), "| JD chunks:", len(jd_documents))

    state["resume_documents"] = resume_documents
    state["jd_documents"] = jd_documents

    return state


def missing_documents_node(state: ResumeGraphState):
    """Fallback used when the resume, the JD, or both are not indexed yet."""
    print(">>> MISSING DOCUMENTS NODE")

    if not state["resume_documents"] and not state["jd_documents"]:
        message = (
            "Upload a resume and a job description to this session before "
            "running the check."
        )
    elif not state["resume_documents"]:
        message = "Upload a resume to this session before running the check."
    else:
        message = "Upload a job description to this session before running the check."

    state["review"] = {"error": message}

    return state


def analyze_node(state: ResumeGraphState):
    """Compare the resume against the JD."""
    print(">>> ANALYZE NODE")

    resume_context = format_context(state["resume_documents"])
    jd_context = format_context(state["jd_documents"])

    analysis = analyze_resume(resume_context, jd_context)

    print("Analysis parsed:", "error" not in analysis)

    state["resume_context"] = resume_context
    state["analysis"] = analysis

    return state


def analysis_failed_node(state: ResumeGraphState):
    """Fallback used when the LLM's response could not be parsed."""
    print(">>> ANALYSIS FAILED NODE")

    state["review"] = {"error": state["analysis"]["error"]}

    return state


def ground_check_node(state: ResumeGraphState):
    """Re-verify every "clearly demonstrated" verdict against the resume."""
    print(">>> GROUND CHECK NODE")

    verdicts = ground_check_verdicts(
        state["analysis"]["verdicts"],
        state["resume_context"],
    )

    print("Verdicts checked:", len(verdicts))

    state["analysis"]["verdicts"] = verdicts

    return state


def store_node(state: ResumeGraphState):
    """Persist the review and hand the UI a single ready-to-render dict."""
    print(">>> STORE NODE")

    # The model does not always return every field on every verdict object
    # even when the outer JSON parses cleanly -- drop anything unusable
    # rather than crash or display a blank requirement.
    verdicts = [
        verdict
        for verdict in state["analysis"]["verdicts"]
        if verdict.get("requirement") and verdict.get("verdict") in ALLOWED_VERDICTS
    ]

    matched_skills = [
        verdict["requirement"]
        for verdict in verdicts
        if verdict["verdict"] in ("clearly demonstrated", "partially demonstrated")
    ]
    missing_skills = [
        verdict["requirement"]
        for verdict in verdicts
        if verdict["verdict"] == "not demonstrated"
    ]

    saved = save_review(
        session_id=state["session_id"],
        overall_score=state["analysis"]["overall_score"],
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        suggestions=state["analysis"].get("suggestions", ""),
    )

    state["review"] = {**saved, "verdicts": verdicts}

    return state


def route_after_retrieve(state: ResumeGraphState):
    if not state["resume_documents"] or not state["jd_documents"]:
        return "missing_documents"

    return "analyze"


def route_after_analyze(state: ResumeGraphState):
    if "error" in state["analysis"]:
        return "analysis_failed"

    return "ground_check"


# --------------------------------------------------------------------------
# Graph wiring
# --------------------------------------------------------------------------

graph = StateGraph(ResumeGraphState)

graph.add_node("retrieve", retrieve_node)
graph.add_node("missing_documents", missing_documents_node)
graph.add_node("analyze", analyze_node)
graph.add_node("analysis_failed", analysis_failed_node)
graph.add_node("ground_check", ground_check_node)
graph.add_node("store", store_node)

graph.add_edge(START, "retrieve")

graph.add_conditional_edges(
    "retrieve",
    route_after_retrieve,
    {
        "missing_documents": "missing_documents",
        "analyze": "analyze",
    },
)

graph.add_conditional_edges(
    "analyze",
    route_after_analyze,
    {
        "analysis_failed": "analysis_failed",
        "ground_check": "ground_check",
    },
)

graph.add_edge("ground_check", "store")

graph.add_edge("missing_documents", END)
graph.add_edge("analysis_failed", END)
graph.add_edge("store", END)

resume_graph = graph.compile()
