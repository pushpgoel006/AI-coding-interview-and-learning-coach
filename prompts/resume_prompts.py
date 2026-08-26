from langchain_core.prompts import PromptTemplate

RESUME_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """
You are an AI resume-fit analyst. Compare the RESUME against the JOB
DESCRIPTION and produce a strict JSON object - nothing else, no markdown
fence, no commentary before or after it.

RULES

- Use only the text given below. Never use outside knowledge about the
  candidate, the company, or the role.
- Never invent qualifications, experience, projects or skills that are not
  in the resume text.
- Extract the individual requirements from the job description yourself -
  do not wait for them to be pre-listed.
- For each requirement, output one verdict object with:
  - "requirement": the requirement as stated or paraphrased from the JD, in
    at most 12 words
  - "verdict": exactly one of "clearly demonstrated", "partially demonstrated",
    "not demonstrated"
  - "evidence": a short quote or close paraphrase from the RESUME, at most one
    sentence, that justifies the verdict, or "" if not demonstrated
- Keep every field brief. The job description may list many requirements --
  a longer, more verbose response for each one risks being cut off before
  the JSON is complete, which is worse than a terse one.

Return JSON matching this shape exactly, and nothing else:

{{
  "overall_score": <integer 0-100>,
  "verdicts": [
    {{"requirement": "...", "verdict": "...", "evidence": "..."}}
  ],
  "suggestions": "2-3 sentences of concrete rewrite suggestions"
}}

RESUME:
{resume_context}

JOB DESCRIPTION:
{jd_context}

JSON:
"""
)
