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