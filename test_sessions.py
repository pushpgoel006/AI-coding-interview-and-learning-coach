"""Acceptance test for M0 -- prep session scoping.

Plain script, not pytest, matching the project's existing test file style.
Run against the real database and vector store:

    python test_sessions.py
"""

from services.session_service import create_session, list_sessions
from rag.indexer import index_documents, list_indexed_documents, clear_session_index
from rag.retriever import get_retriever

UPLOADS = "uploads"
FILE_A = f"{UPLOADS}/Pushp_Goel_Resume.pdf"
FILE_A2 = f"{UPLOADS}/Pushp_Goel_Bonafide.pdf"
FILE_B = f"{UPLOADS}/CN.pdf"


def check(label: str, condition: bool) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    # 1. Create session A and session B.
    session_a = create_session("Amazon", "SDE Intern")
    session_b = create_session("TCS", "Analyst")
    ids = {s["id"] for s in list_sessions()}
    check(
        "Both sessions were created",
        session_a["id"] in ids and session_b["id"] in ids,
    )

    # 2. Index one PDF into A and a different one into B.
    index_documents([FILE_A], session_a["id"], doc_type="resume")
    index_documents([FILE_B], session_b["id"], doc_type="company")

    # 3. list_indexed_documents(A) shows only A's file.
    docs_a = list_indexed_documents(session_a["id"])
    check(
        "Session A's index shows only its own file",
        docs_a == ["Pushp_Goel_Resume.pdf"],
    )

    # 4. Retrieving in A returns only chunks tagged with A's session_id.
    results = get_retriever(session_a["id"]).invoke("What projects are listed?")
    check(
        "Every retrieved chunk in session A carries session A's session_id",
        len(results) > 0
        and all(doc.metadata.get("session_id") == session_a["id"] for doc in results),
    )

    # 5. Indexing a second file into A keeps the first file retrievable
    #    (the clear_index-on-every-run bug is fixed).
    index_documents([FILE_A2], session_a["id"], doc_type="notes")
    docs_a_after_second = list_indexed_documents(session_a["id"])
    check(
        "Session A keeps its first file after a second upload",
        "Pushp_Goel_Resume.pdf" in docs_a_after_second
        and "Pushp_Goel_Bonafide.pdf" in docs_a_after_second,
    )

    # 6. Clearing session A leaves session B untouched.
    clear_session_index(session_a["id"])
    docs_a_after_clear = list_indexed_documents(session_a["id"])
    docs_b_after_clear = list_indexed_documents(session_b["id"])
    check(
        "clear_session_index(A) empties A but leaves B's results intact",
        docs_a_after_clear == [] and docs_b_after_clear == ["CN.pdf"],
    )

    # Cleanup so repeated runs start from a clean slate.
    clear_session_index(session_b["id"])

    print("\nAll M0 acceptance checks passed.")


if __name__ == "__main__":
    main()
