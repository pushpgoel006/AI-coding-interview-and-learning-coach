"""LangGraph workflow for the RAG pipeline.

This module only orchestrates. Every node delegates to a function in the
``rag`` package, so the retrieval, grading, and generation logic stays in one
place and this file stays readable.

State flow (the shared "backpack"):
    {question, session_id}
      -> retrieve      adds documents
      -> route         empty -> no_documents, else -> grader
      -> grader        adds relevant_documents, grade
      -> route         empty -> not_found, else -> generate
      -> generate / not_found / no_documents  adds answer, sources
"""

from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from rag.retriever import get_retriever
from rag.generator import generate_answer
from rag.grader import filter_relevant_documents
from rag.citations import build_sources


class GraphState(TypedDict):
    question: str
    session_id: str
    documents: list[Document]           # everything retrieved
    relevant_documents: list[Document]  # what survived grading
    grade: str                          # summary string, for the debug trace
    sources: list[dict]                 # built from relevant_documents
    answer: str


# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------

def retriever_node(state: GraphState):
    """Fetch the chunks that are semantically closest to the question."""
    print(">>> RETRIEVER NODE")

    retriever = get_retriever(state["session_id"])

    documents = retriever.invoke(
        state["question"]
    )

    print("Retrieved:", len(documents))

    state["documents"] = documents

    return state


def grader_node(state: GraphState):
    """Grade each retrieved chunk individually and keep the relevant ones."""
    print(">>> GRADER NODE")

    relevant_documents, grade = filter_relevant_documents(
        state["question"],
        state["documents"],
    )

    print("Grade:", grade)

    state["relevant_documents"] = relevant_documents
    state["grade"] = grade

    return state


def generate_node(state: GraphState):
    """Produce the final answer from the chunks that survived grading."""
    print(">>> GENERATE NODE")

    answer = generate_answer(
        state["question"],
        state["relevant_documents"],
    )

    print("Generation finished")

    state["answer"] = answer
    state["sources"] = build_sources(state["relevant_documents"])

    return state


def not_found_node(state: GraphState):
    """Fallback used when no retrieved chunk was judged relevant."""
    print(">>> NOT FOUND NODE")

    state["answer"] = (
        "I couldn't find that information in the uploaded documents."
    )
    state["sources"] = []

    return state


def no_documents_node(state: GraphState):
    """Fallback used when the session has nothing indexed at all."""
    print(">>> NO DOCUMENTS NODE")

    state["answer"] = (
        "No documents have been indexed in this prep session yet. "
        "Upload a PDF in the sidebar and press Process Documents."
    )
    state["sources"] = []

    return state


def route_after_retriever(state: GraphState):
    """Skip grading and generation entirely when nothing was retrieved."""
    if not state["documents"]:
        return "no_documents"

    return "grader"


def route_after_grader(state: GraphState):
    """Send relevant context to the generator, everything else to not_found."""
    if state["relevant_documents"]:
        return "generate"

    return "not_found"


# --------------------------------------------------------------------------
# Graph wiring
# --------------------------------------------------------------------------

graph = StateGraph(GraphState)

# Register nodes
graph.add_node(
    "retrieve",
    retriever_node,
)

graph.add_node(
    "grader",
    grader_node,
)

graph.add_node(
    "generate",
    generate_node,
)

graph.add_node(
    "not_found",
    not_found_node,
)

graph.add_node(
    "no_documents",
    no_documents_node,
)

# Connect nodes
graph.add_edge(
    START,
    "retrieve",
)

graph.add_conditional_edges(
    "retrieve",
    route_after_retriever,
    {
        "grader": "grader",
        "no_documents": "no_documents",
    },
)

graph.add_conditional_edges(
    "grader",
    route_after_grader,
    {
        "generate": "generate",
        "not_found": "not_found",
    },
)

graph.add_edge(
    "generate",
    END,
)

graph.add_edge(
    "not_found",
    END,
)

graph.add_edge(
    "no_documents",
    END,
)

rag_graph = graph.compile()
