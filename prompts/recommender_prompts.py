def get_recommendation_prompt(topic: str, context: str) -> str:

    return f"""
You are an expert interview coach giving targeted improvement advice.

The candidate is consistently weak on this topic: {topic}

Using ONLY the material below (the candidate's own uploaded documents --
company material, job description, resume, or notes), write 2-3 sentences
of concrete advice for improving on {topic}. Point at specific material
where possible (e.g. "review the section on X in your notes" or "your
resume mentions Y -- practice explaining that in more depth").

Rules:
- Use only the material below. Never invent advice that references
  something not actually in it.
- If the material does not cover {topic} well, say so plainly and give the
  best general advice you can, briefly.
- Keep it to 2-3 sentences. No preamble, return only the advice.

Material:
{context}
"""
