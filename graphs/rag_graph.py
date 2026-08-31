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
    documents: list[Document]
    relevant_documents: list[Document]
    grade: str
    sources: list[dict]
    answer: str


def retriever_node(state: GraphState):
    print(">>> RETRIEVER NODE")

    retriever = get_retriever(state["session_id"])

    documents = retriever.invoke(
        state["question"]
    )

    print("Retrieved:", len(documents))

    state["documents"] = documents

    return state


def grader_node(state: GraphState):
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
    print(">>> NOT FOUND NODE")

    state["answer"] = (
        "I couldn't find that information in the uploaded documents."
    )
    state["sources"] = []

    return state


def no_documents_node(state: GraphState):
    print(">>> NO DOCUMENTS NODE")

    state["answer"] = (
        "No documents have been indexed in this prep session yet. "
        "Upload a PDF in the sidebar and press Process Documents."
    )
    state["sources"] = []

    return state


def route_after_retriever(state: GraphState):
    if not state["documents"]:
        return "no_documents"

    return "grader"


def route_after_grader(state: GraphState):
    if state["relevant_documents"]:
        return "generate"

    return "not_found"


graph = StateGraph(GraphState)

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
