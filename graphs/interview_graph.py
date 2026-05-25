from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.evaluator import evaluate_answer
from agents.question_generator import generate_question


class InterviewState(TypedDict):
    jd: str
    question: str
    answer: str
    evaluation: dict

#node 1(question wali)
def question_node(state: InterviewState):

    question = generate_question(state["jd"])

    return {
        "question": question
    }

#node2(evaluation wali)
def evaluation_node(state: InterviewState):

    evaluation = evaluate_answer(
        state["question"],
        state["answer"]
    )

    return {
        "evaluation": evaluation
    }

graph = StateGraph(InterviewState)
#defining the nodes 1 and 2
graph.add_node("question_generator", question_node)

graph.add_node("evaluation", evaluation_node)
#here edegs define the workflow
graph.set_entry_point("question_generator")

graph.add_edge("question_generator", "evaluation")

graph.add_edge("evaluation", END)

interview_graph = graph.compile()