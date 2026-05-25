def get_evaluation_prompt(question, answer):

    return f"""
    You are a technical interviewer evaluating a candidate.

    Question:
    {question}

    Candidate Answer:
    {answer}

    Return ONLY valid JSON in this format:

    {{
        "score": number,
        "strengths": "text",
        "weaknesses": "text",
        "ideal_answer": "text"
    }}

    Do not add any extra explanation.
    """