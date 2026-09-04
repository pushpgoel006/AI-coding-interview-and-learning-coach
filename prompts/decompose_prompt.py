from langchain_core.prompts import PromptTemplate

DECOMPOSE_PROMPT = PromptTemplate.from_template(
    """
Look at the question below. If it asks about MULTIPLE distinct requirements,
skills, or topics that should each be checked separately against a document,
break it into separate short sub-questions - one per requirement or topic.

If the question is already a single, focused question, return it unchanged as
the only item.

Return each sub-question on its own line, with no numbering, no bullets, and
no extra commentary. Return at most 5 sub-questions.

Question:
{question}

Sub-questions:
"""
)
