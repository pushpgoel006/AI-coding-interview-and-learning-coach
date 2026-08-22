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