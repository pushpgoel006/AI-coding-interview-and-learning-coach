from langchain_core.prompts import PromptTemplate


GRADER_PROMPT = PromptTemplate.from_template(
    """
You are an expert document relevance evaluator.

Your task is to determine whether the retrieved context is relevant
and useful for answering the user's question.

The question may:
- Ask for information directly contained in the document.
- Ask to compare information across documents.
- Contain requirements or criteria and ask whether a person or document
  satisfies them.
- Require reasoning or comparison using information from the retrieved context.

Rules:

- Answer ONLY "yes" or "no".
- Do not explain your answer.
- Answer "yes" if the context contains useful information that can help
  answer, compare, evaluate, or reason about the question.
- Answer "no" only if the context is unrelated or provides no useful
  information for answering the question.

Question:
{question}

Context:
{context}

Answer:
"""
)