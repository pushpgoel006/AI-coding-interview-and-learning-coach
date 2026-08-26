from langchain_core.documents import Document

from models.llm_provider import get_llm
from prompts.doc_grader import GRADER_PROMPT


def format_context(documents: list[Document]) -> str:
    return "\n\n".join(
        document.page_content
        for document in documents
    )


def grade_documents(
    question: str,
    documents: list[Document],
) -> str:

    context = format_context(documents)

    prompt = GRADER_PROMPT.format(
        question=question,
        context=context,
    )

    llm = get_llm()

    response = llm.invoke(prompt)

    return response.content.strip().lower()


def grade_document(question: str, document: Document) -> bool:
    """Grade a single chunk's relevance to the question."""
    prompt = GRADER_PROMPT.format(
        question=question,
        context=document.page_content,
    )

    llm = get_llm()

    response = llm.invoke(prompt)

    return response.content.strip().lower().startswith("yes")


def filter_relevant_documents(
    question: str,
    documents: list[Document],
) -> tuple[list[Document], str]:
    """Grade each chunk independently and keep only the relevant ones."""
    if not documents:
        return [], "0/0 relevant"

    kept = [document for document in documents if grade_document(question, document)]

    return kept, f"{len(kept)}/{len(documents)} relevant"