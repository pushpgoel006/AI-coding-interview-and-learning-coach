def get_question_prompt(jd):

    return f"""
    You are a technical interviewer.

    Based on the following job description,
    generate ONLY ONE short technical interview question.

    Keep the response under 3 lines.

    Job Description:
    {jd}
    """