"""Acceptance test for M1 -- citations, loosened refusal, per-chunk grading.

Plain script, not pytest, matching the project's existing test file style.
Run against the real database, vector store, and LLM:

    python test_citations.py
"""

from unittest.mock import patch

from database.db import get_db
from database.models import PrepSession
from services.session_service import create_session
from rag.indexer import index_documents, list_indexed_documents, clear_session_index
from graphs.rag_graph import rag_graph

REFUSAL = "I couldn't find that information in the uploaded documents."

DATA_ANALYST_QUESTION = """
These are the necessities for a Data Analyst job:

- Extracting data from primary and secondary sources and removing corrupted data
- Ensuring that the data is accurate and high-quality
- Developing and managing data systems and databases
- Establishing KPIs that provide actionable insights
- Using data to analyse trends that help inform business policies and decisions
- Collaborating with engineers and developers to develop and streamline data governance strategies

Is Pushp capable of this?
"""


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    session = create_session("Citations Test Co", "QA")
    empty_session = create_session("Empty Session Co", "QA")
    session_id = session["id"]
    empty_session_id = empty_session["id"]

    try:
        index_documents(
            ["uploads/Pushp_Goel_Resume.pdf"], session_id, doc_type="resume"
        )
        index_documents(
            ["uploads/IBM_AI_ML_Engineer_Requirements.pdf"], session_id, doc_type="jd"
        )

        all_sources = []

        # 1. Factual question
        result = rag_graph.invoke(
            {
                "question": "What programming languages does Pushp know?",
                "session_id": session_id,
            }
        )
        all_sources.extend(result["sources"])
        check(
            "Factual question returns a non-empty, non-refusal answer",
            bool(result["answer"]) and result["answer"] != REFUSAL,
        )
        check(
            "Factual question cites the resume",
            any(s["file_name"] == "Pushp_Goel_Resume.pdf" for s in result["sources"]),
        )

        # 3. Capability question (checked before #2 so its sources feed the
        # page-number check below)
        capability_result = rag_graph.invoke(
            {"question": DATA_ANALYST_QUESTION, "session_id": session_id}
        )
        all_sources.extend(capability_result["sources"])
        answer_lower = capability_result["answer"].lower()
        check(
            "Capability question is not refused",
            capability_result["answer"] != REFUSAL,
        )
        check(
            "Capability question uses demonstrated/partial labeling",
            any(label in answer_lower for label in ["demonstrated", "partially"]),
        )

        # 2. Page numbers are 1-based
        check(
            "No source in any result has page 0",
            all(s["page"] != 0 for s in all_sources),
        )

        # 4. Unrelated question
        unrelated_result = rag_graph.invoke(
            {"question": "What is the capital of France?", "session_id": session_id}
        )
        check("Unrelated question is refused", unrelated_result["answer"] == REFUSAL)
        check("Unrelated question has no sources", unrelated_result["sources"] == [])

        # 5. Empty session -- grader and generator must never run
        with (
            patch("graphs.rag_graph.filter_relevant_documents") as mock_filter,
            patch("graphs.rag_graph.generate_answer") as mock_generate,
        ):
            empty_result = rag_graph.invoke(
                {"question": "anything", "session_id": empty_session_id}
            )
        check(
            "Empty session shows the no-documents message",
            "No documents have been indexed" in empty_result["answer"],
        )
        check("Empty session never calls the grader", not mock_filter.called)
        check("Empty session never calls the generator", not mock_generate.called)

        # 6. Citations are honest
        indexed_files = set(list_indexed_documents(session_id))
        cited_files = {s["file_name"] for s in all_sources}
        check(
            "Every cited file was actually indexed in this session",
            cited_files <= indexed_files,
        )

        print("\nAll M1 acceptance checks passed.")
    finally:
        clear_session_index(session_id)
        clear_session_index(empty_session_id)
        with get_db() as db:
            db.query(PrepSession).filter(
                PrepSession.id.in_([session_id, empty_session_id])
            ).delete(synchronize_session=False)


if __name__ == "__main__":
    main()
