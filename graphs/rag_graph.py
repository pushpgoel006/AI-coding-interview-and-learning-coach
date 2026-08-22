

from typing import TypedDict

from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

from rag.retriever import get_retriever
from rag.generator import generate_answer
from rag.grader import grade_documents



class GraphState(TypedDict):
    question: str
    documents: list[Document]
    grade: str
    answer: str



def retriever_node(state: GraphState):


    retriever = get_retriever()

    documents = retriever.invoke(
        state["question"]
    )

    state["documents"] = documents

    return state

def grader_node(state: GraphState):

    print(">>> GRADER NODE")

    grade = grade_documents(
        state["question"],
        state["documents"],     # <-- Corrected
    )

    print("Grade:", grade)

    state["grade"] = grade

    return state



def generate_node(state: GraphState):

    print(">>> GENERATE NODE")

    answer = generate_answer(
        state["question"],
        state["documents"],
    )

    state["answer"] = answer

    return state


def not_found_node(state: GraphState):

    print(">>> NOT FOUND NODE")

    state["answer"] = (
        "I couldn't find that information in the uploaded documents."
    )

    return state


def route_after_grader(state: GraphState):

    if state["grade"].strip().lower() == "yes":
        return "generate"

    return "not_found"



graph = StateGraph(GraphState)

# Register Nodes
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

# Connect Nodes

graph.add_edge(
    START,
    "retrieve",
)

# <-- This edge was missing
graph.add_edge(
    "retrieve",
    "grader",
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

rag_graph = graph.compile()

def retriever_node(state: GraphState):

    print(">>> RETRIEVER START")

    retriever = get_retriever()

    documents = retriever.invoke(
        state["question"]
    )

    print("Retrieved:", len(documents))

    state["documents"] = documents

    return state

def grader_node(state: GraphState):

    print(">>> GRADER START")

    grade = grade_documents(
        state["question"],
        state["documents"],
    )

    print("GRADE:", grade)

    state["grade"] = grade

    return state

def generate_node(state: GraphState):

    print(">>> GENERATOR START")

    answer = generate_answer(
        state["question"],
        state["documents"]
    )

    print("GENERATOR FINISHED")

    state["answer"] = answer

    return state