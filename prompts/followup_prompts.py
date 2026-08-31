def get_followup_prompt(question, answer, score):

    return f"""
You are an expert technical interviewer.

Original Question:
{question}

Candidate Answer:
{answer}

Score:
{score}/10

Rules:

- If score <= 3:
Generate an easier question testing foundational understanding.

- If score between 4 and 7:
Generate a clarification question that explores missing concepts.

- If score >= 8:
Generate a deeper and more advanced follow-up question.

Generate exactly ONE follow-up question.

Return only the question.
"""


def get_grounded_followup_prompt(
    context: str,
    original_question: str,
    original_answer: str,
    history: list[dict],
    latest_answer: str,
    score: int,
) -> str:

    history_text = "\n\n".join(
        f"Follow-up {i + 1} question: {turn['question']}\n"
        f"Follow-up {i + 1} answer: {turn['answer']}"
        for i, turn in enumerate(history)
    ) or "(no follow-ups yet)"

    return f"""
You are an expert technical interviewer conducting a live follow-up round.

You must ask a question that is grounded in the material below -- the
candidate's own uploaded documents (company material, job description,
resume, or notes). Reference something specific from it where relevant.

MATERIAL:
{context}

Original Question:
{original_question}

Original Answer:
{original_answer}

Previous follow-ups in this thread:
{history_text}

Candidate's latest answer:
{latest_answer}

Score of the latest answer:
{score}/10

Rules:

- If score <= 3:
Generate an easier question testing foundational understanding.

- If score between 4 and 7:
Generate a clarification question that explores missing concepts.

- If score >= 8:
Generate a deeper and more advanced follow-up question.

- Your question must take the ENTIRE thread above into account, not just
  the latest answer. If the candidate contradicted or expanded on something
  said in an earlier follow-up, you may reference it directly (e.g. "you
  mentioned X earlier, but...").
- Do not repeat a question already asked in this thread.

Generate exactly ONE follow-up question. Return only the question.
"""