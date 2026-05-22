from  models.llm_provider import get_llm
llm=get_llm()
def generate_question(jd):
    prompt = f"""
    You are a technical interviewer.

    Based on the following job description,
    generate ONLY ONE short technical interview question.

    Keep the response under 3 lines.

    Job Description:
    {jd}
    
    """ 

    response=llm.invoke(prompt)
    return response.content
