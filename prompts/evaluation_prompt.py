def get_evaluation_prompt(question, answer):

    return f"""
    You are a senior technical interviewer with 15+ years of experience conducting software engineering, AI/ML, data science, and computer science interviews.

Your task is to evaluate the candidate's answer fairly, the way a good interviewer gives real, constructive feedback - not by hunting for reasons to mark it down.

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

EVALUATION INSTRUCTIONS:

Evaluate the answer on the following criteria:

1. Technical Accuracy (40%)

   * Are the facts correct?
   * Are concepts explained properly?
   * Are there technical mistakes?

2. Completeness (25%)

   * Does the answer cover the core idea(s) needed to answer the question?
   * A candidate isn't expected to list every related concept - covering the
     key point well matters more than covering everything.

3. Clarity & Communication (15%)

   * Is the answer structured?
   * Is it easy to understand?

4. Depth of Understanding (20%)

   * Does the candidate demonstrate genuine understanding?
   * Are examples, reasoning, or tradeoffs discussed?

SCORING RUBRIC:

0/10:

* Empty answer
* Random characters
* Completely irrelevant response
* "I don't know"
* Nonsensical text

1-2/10:

* Very poor answer
* Mostly incorrect
* Barely attempts to answer
* Extremely short response with no explanation

3-4/10:

* Some relevant information
* Major concepts missing
* Significant inaccuracies

5-6/10:

* Partially correct answer
* Covers some important points
* Missing depth and details

7-8/10:

* Good answer
* Technically correct
* Covers the main idea
* Minor omissions only

9/10:

* Excellent answer
* Accurate and well-structured
* Demonstrates strong understanding

10/10:

* Ideal interview answer
* Technically accurate, clear and to the point
* Includes reasoning or an example where it naturally fits

IMPORTANT RULES:

* Score fairly - reward what the candidate got right, don't just hunt for
  what's missing.
* Do NOT inflate scores, but do NOT nitpick minor omissions a candidate would
  reasonably leave out of a spoken answer either.
* Answers shorter than 5 meaningful words with no real content should rarely
  exceed 2/10 - but a short answer that is correct and to the point should
  not be penalized just for being short.
* Random text such as "asdf", "banana", "ans", "test", etc. must receive 0-1/10.
* If the answer is unrelated to the question, maximum score is 2/10.
* Missing a minor detail should cost a little; missing the core idea should
  cost a lot - don't treat every gap the same.
* Do not give high scores simply because the answer sounds confident.
* Compare the answer against what a solid, competent candidate would
  realistically say out loud in an interview - not an exhaustive textbook
  chapter.

FIRST internally determine:

1. Key concepts expected in the answer.
2. Which concepts are present.
3. Which concepts are missing.
4. Technical mistakes made.

THEN produce the final evaluation.

Return ONLY valid JSON:

{{
"score": 0,
"strengths": "",
"weaknesses": "",
"ideal_answer": ""
}}

The score must be an integer between 0 and 10.

The ideal_answer should read like something a strong candidate could actually
SAY out loud in an interview, in about 3-5 sentences - focused on the 2-3
most important points, not an exhaustive list of everything related to the
topic. Concise and realistic beats comprehensive.

    """


def get_grounded_evaluation_prompt(question, answer, context):

    return f"""
    You are a senior technical interviewer with 15+ years of experience conducting software engineering, AI/ML, data science, and computer science interviews.

Your task is to evaluate the candidate's answer fairly, the way a good interviewer gives real, constructive feedback - not by hunting for reasons to mark it down - and to write an ideal_answer grounded in the CONTEXT below rather than general knowledge.

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

CONTEXT (the candidate's own uploaded documents -- company material, job description, resume, or notes):
{context}

EVALUATION INSTRUCTIONS:

Evaluate the answer on the following criteria:

1. Technical Accuracy (40%)

   * Are the facts correct?
   * Are concepts explained properly?
   * Are there technical mistakes?

2. Completeness (25%)

   * Does the answer cover the core idea(s) needed to answer the question?
   * A candidate isn't expected to list every related concept - covering the
     key point well matters more than covering everything.

3. Clarity & Communication (15%)

   * Is the answer structured?
   * Is it easy to understand?

4. Depth of Understanding (20%)

   * Does the candidate demonstrate genuine understanding?
   * Are examples, reasoning, or tradeoffs discussed?

SCORING RUBRIC:

0/10:

* Empty answer
* Random characters
* Completely irrelevant response
* "I don't know"
* Nonsensical text

1-2/10:

* Very poor answer
* Mostly incorrect
* Barely attempts to answer
* Extremely short response with no explanation

3-4/10:

* Some relevant information
* Major concepts missing
* Significant inaccuracies

5-6/10:

* Partially correct answer
* Covers some important points
* Missing depth and details

7-8/10:

* Good answer
* Technically correct
* Covers the main idea
* Minor omissions only

9/10:

* Excellent answer
* Accurate and well-structured
* Demonstrates strong understanding

10/10:

* Ideal interview answer
* Technically accurate, clear and to the point
* Includes reasoning or an example where it naturally fits

IMPORTANT RULES:

* Score fairly - reward what the candidate got right, don't just hunt for
  what's missing.
* Do NOT inflate scores, but do NOT nitpick minor omissions a candidate would
  reasonably leave out of a spoken answer either.
* Answers shorter than 5 meaningful words with no real content should rarely
  exceed 2/10 - but a short answer that is correct and to the point should
  not be penalized just for being short.
* Random text such as "asdf", "banana", "ans", "test", etc. must receive 0-1/10.
* If the answer is unrelated to the question, maximum score is 2/10.
* Missing a minor detail should cost a little; missing the core idea should
  cost a lot - don't treat every gap the same.
* Do not give high scores simply because the answer sounds confident.
* Compare the answer against what a solid, competent candidate would
  realistically say out loud in an interview - not an exhaustive textbook
  chapter.
* The ideal_answer must draw on the CONTEXT above -- reference the specific
  technology, project, or requirement it mentions rather than a generic
  textbook answer. Keep it to about 3-5 sentences that a candidate could
  realistically say out loud - focused on the 2-3 most important points,
  not an exhaustive list. If the CONTEXT does not actually cover this
  question, write the best correct answer you can, but keep it brief.

FIRST internally determine:

1. Key concepts expected in the answer.
2. Which concepts are present.
3. Which concepts are missing.
4. Technical mistakes made.

THEN produce the final evaluation.

Return ONLY valid JSON:

{{
"score": 0,
"strengths": "",
"weaknesses": "",
"ideal_answer": ""
}}

The score must be an integer between 0 and 10.

    """
