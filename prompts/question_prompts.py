def get_question_prompt(jd):

    return f"""
    You are a technical interviewer.

    Based on the following job description,
    generate ONLY ONE short technical interview question.

    Keep the response under 3 lines.

    Job Description:
    {jd}
    """


def get_grounded_question_prompt(context: str, topic: str | None, difficulty: str) -> str:

    topic_line = (
        f"Focus specifically on the topic: {topic}."
        if topic
        else "Choose any relevant topic from the material below."
    )

    return f"""
    You are a technical interviewer preparing a candidate for a real interview.

    You must ask a question that is grounded in the material below -- the
    candidate's own uploaded documents (company material, job description,
    resume, or notes). Reference something specific from it: a technology,
    a project, a stated requirement, or a responsibility.

    {topic_line}

    Difficulty: {difficulty}.

    Generate ONLY ONE interview question. Keep it under 3 lines. Do not
    explain your reasoning -- return only the question.

    Material:
    {context}
    """