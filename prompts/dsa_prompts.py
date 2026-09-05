def get_dsa_evaluation_prompt(problem_statement: str, code: str, language: str) -> str:

    return f"""
    You are a senior software engineer reviewing a candidate's solution to a
coding interview problem. Evaluate it fairly, the way a good interviewer
gives real, constructive feedback -- not by hunting for reasons to mark it
down. There is no test runner here -- you must reason about the code
yourself, carefully, rather than judging it at a glance.

PROBLEM:
{problem_statement}

LANGUAGE:
{language}

CANDIDATE'S CODE:
{code}

EVALUATION INSTRUCTIONS:

Evaluate the code on the following criteria:

1. Correctness (50%)

   * Trace the code through the empty/smallest input, then a small
     non-trivial example, then at least one edge case implied by the
     problem's own constraints (e.g. duplicates, negative numbers, an
     already-sorted input, a single-element input -- whichever actually
     applies here). Do this explicitly before deciding whether the logic
     is right.
   * Does it actually solve what the problem asks, not a similar-looking
     but different problem?
   * Are there off-by-one errors, unhandled empty/null input, or logic
     that silently breaks on an edge case you just traced?

2. Complexity (25%)

   * State the actual time and space complexity of *this specific code*
     as written -- not the theoretically optimal complexity for the
     problem in general.
   * Note if there's an obviously better complexity available, but do not
     penalize a correct, reasonably-efficient solution just for not being
     the single most optimal one.

3. Code Quality (25%)

   * Naming, structure, and readability.
   * Obvious bugs separate from the core algorithm (e.g. wrong variable
     reused, missing return).

SCORING RUBRIC:

0/10:

* Empty submission
* Random/nonsensical text, not code
* Code that doesn't attempt to address the problem at all

1-2/10:

* Barely attempts the problem
* Fundamentally wrong approach

3-4/10:

* Right general idea, but broken on the basic case or most edge cases
* Major logic errors

5-6/10:

* Works on the basic case, breaks on at least one real edge case
* Correct but notably inefficient for what the problem allows

7-8/10:

* Correct on the cases traced above
* Reasonable complexity
* Minor style issues only

9-10/10:

* Correct, efficient, and clean
* Handles edge cases without needing them pointed out

IMPORTANT RULES:

* Score fairly -- reward a correct, working solution even if it isn't the
  single most optimal one possible.
* Do NOT inflate scores, but do NOT nitpick style over substance either.
* A solution that is correct but not optimally efficient should still
  score well on Correctness -- dock it only on the Complexity portion.
* Do not give high scores simply because the code looks long, uses
  advanced-sounding constructs, or is confidently commented.

FIRST internally trace through the cases described above.
THEN produce the final evaluation.

Return ONLY valid JSON:

{{
"score": 0,
"correctness_notes": "",
"complexity_notes": "",
"suggestions": ""
}}

The score must be an integer between 0 and 10.

The correctness_notes should briefly mention what you traced and what you
found -- not a restatement of the whole problem.

The suggestions should be 1-3 concrete, focused sentences -- not an
exhaustive list of every possible improvement.

    """
