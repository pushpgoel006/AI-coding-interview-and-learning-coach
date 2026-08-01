from langchain_core.documents import Document

from models.llm_provider import get_llm
from prompts.rag_prompts import RAG_PROMPT

#helps to merge the used chunks
def format_context(documents: list[Document]) -> str:
    

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    return context

#helps generate answer
def generate_answer(
    question: str,
    documents: list[Document],
) -> str:
    

    context = format_context(documents)

    prompt = RAG_PROMPT.format(
        context=context,
        question=question,
    )

    llm = get_llm()

    response = llm.invoke(prompt)

    return response.content