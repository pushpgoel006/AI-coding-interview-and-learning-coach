# M3 — Theory mock round (implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report what changed so it can be reviewed before
> continuing. Do not implement several steps in one go. Do not refactor
> anything this brief does not name.
>
> **Prerequisite: M0 and M1 must be complete.** M2 does not need to be
> finished first -- M3 does not depend on the resume checker.

---

## 1. Goal

The system asks a question grounded in this session's own documents, the
user answers, and gets a score with strengths, weaknesses, and an ideal
answer that is itself grounded in those documents rather than the model's
memory.

This is the project's most important upgrade. Today `generate_question(jd)`
takes a raw JD string and asks the model to invent a question from it --
nothing about the company material, the resume, or prior interview
experience the user uploaded ever enters the prompt. After M3, question
generation **retrieves** first, and the evaluator's `ideal_answer` is drawn
from retrieved context instead of general knowledge, the same principle M1
applied to chat answers and M2 applied to resume verdicts.

## 2. Non-goals

Do **not** build these in M3.

- The follow-up loop or conversation memory (M4). Do not touch
  `agents/followup_generator.py` or `prompts/followup_prompts.py`.
- DSA round (M5), dashboard (M6).
- Any change to `graphs/rag_graph.py`, `graphs/resume_graph.py`,
  `agents/resume_analyzer.py`, `rag/grader.py`, `rag/generator.py`,
  `prompts/rag_prompts.py`, `prompts/doc_grader.py`, `prompts/resume_prompts.py`.
- Any change to what `main.py`'s existing endpoints return for their
  existing inputs. `generate_question(jd)` and `evaluate_answer(question,
  answer)` keep their current signatures and success-case return shape --
  new capability is added through new functions and new, optional graph
  state, never by changing what these two already do.
- Streaming is not reworked. `stream_question` and `stream_evaluation` stay
  as they are; a grounded streaming variant is optional (Step 9).

---

## 3. Four gotchas to get right

### 3.1 Two unrelated things are both called "session_id"

`main.py`'s existing code generates a random uuid4 and stores it as
`Interview.id`, then calls that value "session_id" in its API responses.
This has **nothing to do** with the prep-session `session_id` column M0
added to `Interview` (a real foreign key to `prep_sessions`, currently
always `NULL` because nothing sets it yet). Do not let these merge in your
head:

- **`interview_id`** -- an `Interview` row's own primary key. This is what
  `main.py`'s old "session_id" actually is.
- **`session_id`** -- the prep session's id, the FK column from M0.

Every new function you write in this brief takes `session_id` meaning the
prep session. Never write a parameter called `session_id` that secretly
means an interview id.

### 3.2 `main.py` must keep working, and it never sets the new fields

`/start-interview` calls `interview_graph.invoke({"jd": ..., "answer":
...})` -- no `session_id` key at all. Every new node you add to this graph
must read new state with `state.get("session_id")`, never
`state["session_id"]`, and must fall back to exactly today's behaviour
(calling the untouched `generate_question(jd)` / `evaluate_answer`) when it
is absent. Verify this by re-running that exact call shape after every
change to the graph.

### 3.3 `evaluate_answer`'s unguarded `json.loads` is a real, pre-existing bug

Flagged all the way back in the M0 brief: `evaluate_answer` calls
`json.loads(response.content)` with no guard. Fix it now with a try/except
returning a clear error dict on failure -- the same pattern M2 used in
`analyze_resume`. Do not change its signature or its return shape on the
success path; `main.py`'s `/evaluate-answer` reads `result["score"]` and
must keep working.

### 3.4 One ideal answer needs one grounding check, not a loop

M2's grounding check re-verified many small verdicts one at a time. M3 has a
single `ideal_answer` per evaluation. Check it once: does the retrieved
context actually support it, or did the model quietly fall back to its own
memory? If unsupported, say so rather than silently presenting an ungrounded
answer as if it were sourced -- do not invent a citation for it either way.

---

## Step 1 — Data model

**File:** `database/models.py`

Add columns to the existing `Interview` class (`session_id` already exists
from M0 -- do not add it again):

```python
topic         = Column(String, nullable=True)
ideal_answer  = Column(Text, default="")
strengths     = Column(Text, default="")
weaknesses    = Column(Text, default="")
created_at    = Column(DateTime, default=datetime.utcnow)
```

Leave `Followup` untouched -- that is M4.

**Done when:** `init_db.py` runs clean and the new columns exist on
`interviews`.

---

## Step 2 — Grounded question prompt

**File:** `prompts/question_prompts.py`

Add a new function; keep `get_question_prompt(jd)` exactly as it is.

```python
def get_grounded_question_prompt(context: str, topic: str | None, difficulty: str) -> str
```

Ask for exactly one interview question that visibly draws on the given
context (mention a technology, a project, or a requirement that actually
appears in it), at the requested difficulty, on the given topic if one was
provided.

**Done when:** the function returns a prompt string containing the passed
context, topic, and difficulty.

---

## Step 3 — Grounded question generation

**File:** `agents/question_generator.py`

Add a new function; keep `generate_question(jd)` and `stream_question(jd,
session_id)` (gotcha 3.1: that `session_id` param is really an interview id)
exactly as they are.

```python
def generate_grounded_question(session_id: str, topic: str | None = None, difficulty: str = "medium") -> dict
```

- Retrieve with `get_retriever(session_id).invoke(topic or "interview
  question")`.
- Build context with the same `format_context` shape used elsewhere (a
  small local helper is fine, matching the existing per-module convention).
- Call `get_grounded_question_prompt`, invoke the LLM.
- Build `sources` with `rag.citations.build_sources(documents)`.
- Return `{"question": ..., "topic": topic, "sources": [...]}`.
- If retrieval returns no documents, return a specific message asking the
  user to upload material first, and do not call the LLM (same empty-input
  guard as M1 gotcha 3.4 / M2 gotcha 3.1).

**Done when:** given a session with indexed documents, the returned question
text or its sources demonstrably trace back to something in those
documents.

---

## Step 4 — Grounded evaluation prompt

**File:** `prompts/evaluation_prompt.py`

Add a new function; keep `get_evaluation_prompt(question, answer)` exactly
as it is.

```python
def get_grounded_evaluation_prompt(question: str, answer: str, context: str) -> str
```

Same scoring rubric as the existing prompt, plus: the `ideal_answer` must be
built from `context`, not general knowledge, and should reference specific
material from it where possible.

**Done when:** the function returns a prompt string containing the
question, answer, and context.

---

## Step 5 — Evaluator: fix the crash, add the grounded path

**File:** `agents/evaluator.py`

1. Fix `evaluate_answer` (gotcha 3.3): wrap `json.loads` in try/except,
   return `{"error": "Could not parse the evaluation. Please try again."}`
   on failure. Signature and success-case shape unchanged.
2. Add, alongside it:

```python
def evaluate_grounded_answer(session_id: str, question: str, answer: str) -> dict
def ground_check_ideal_answer(ideal_answer: str, context: str) -> bool
```

- `evaluate_grounded_answer` retrieves context the same way Step 3 does,
  calls `get_grounded_evaluation_prompt`, parses defensively (same fence
  -stripping helper pattern as M2's analyzer -- a small local copy is fine,
  this file has no dependency on `agents/resume_analyzer.py`), and returns
  `{"score", "strengths", "weaknesses", "ideal_answer", "sources", "grounded": bool}`.
- `ground_check_ideal_answer` asks one yes/no question (gotcha 3.4),
  normalised the M1/M2 way (`.strip().lower().startswith("yes")`). Its
  result becomes the `"grounded"` field above -- do not drop the
  `ideal_answer` when ungrounded, flag it instead.

**Done when:** a deliberately malformed mocked LLM response returns the
error dict from `evaluate_answer` without raising, and a real grounded call
returns the full shape above with `sources` non-empty.

---

## Step 6 — Interview service

**File:** `services/interview_service.py` (new)

Same convention as `session_service.py` / `resume_service.py`: the only
module allowed to write the *new* grounded fields on `Interview` rows.
`main.py`'s existing raw `SessionLocal()` usage is pre-existing and stays as
it is -- this rule is for new code only, matching the precedent already set
for `database/db.py`'s `get_db()` in M0.

```python
record_interview(session_id, topic, question, answer, score, strengths, weaknesses, ideal_answer) -> dict
list_interviews(session_id) -> list[dict]
get_interview(interview_id) -> dict | None
```

Every function returns plain dicts (same DetachedInstanceError rule as
always).

**Done when:** a scratch call records an interview and reads it back both
ways.

---

## Step 7 — Extend the interview graph

**File:** `graphs/interview_graph.py`

`InterviewState` gains optional fields: `session_id`, `topic`, `difficulty`,
`sources`, `strengths`, `weaknesses`, `ideal_answer`, `grounded`. All reads
of these use `.get(...)`, never `[...]` (gotcha 3.2).

- `question_node`: if `state.get("session_id")`, call
  `generate_grounded_question`; otherwise call the untouched
  `generate_question(state["jd"])` exactly as today.
- `evaluation_node`: if `state.get("session_id")`, call
  `evaluate_grounded_answer` then `ground_check_ideal_answer`; otherwise
  call the untouched `evaluate_answer` exactly as today.
- Add a `store_node` that calls `interview_service.record_interview(...)`
  **only on the grounded path** (there is no `session_id` to store against
  otherwise), then routes to `END`.

**Done when:** `interview_graph.invoke({"jd": "...", "answer": "..."})` (no
`session_id`) produces output identical in shape to before this step, and
`interview_graph.invoke({"session_id": sid, "topic": "...", "answer":
"..."})` produces a grounded question, a grounded evaluation, and a
persisted `Interview` row.

---

## Step 8 — Theory round UI

**File:** `ui/interview_page.py` (new)

- A question card showing the generated question and a collapsed sources
  expander (same pattern as M1/M2).
- An answer text area and a "Submit Answer" button.
- On submit: invoke the graph's grounded path, wrapped in try/except
  showing `st.error(...)` on failure (never a stack trace).
- Show the score, strengths, weaknesses, the ideal answer with its own
  sources expander, and -- if `grounded` came back `False` -- a visible
  note that the ideal answer could not be confirmed against the uploaded
  material.
- A "New Question" control to request another one (optionally by topic /
  difficulty).

Not wired into `ui/app.py`'s tabs as part of this brief -- call it out
explicitly when you reach it, same as M2's Step 8, so the wiring can be
reviewed on its own.

**Done when:** a full round -- question, answer, evaluation -- works in the
browser on a session with real indexed documents, and the question visibly
references something specific from them.

---

## Step 9 (optional) — Streamed grounded evaluation

**File:** `ui/interview_page.py`, `agents/evaluator.py`

Stream the grounded evaluation's generation the way `stream_evaluation`
already streams the ungrounded one. Purely a UX improvement; skip unless
asked for.

---

## Acceptance test

**File:** `test_theory_round.py` (project root, plain script like the
existing `test_*.py` files, not pytest)

Setup: create one prep session, index `uploads/Pushp_Goel_Resume.pdf` as
`doc_type="resume"` and a JD as `doc_type="jd"`.

Then assert:

1. **Grounded question generation** -- `generate_grounded_question(session_id)`
   returns a non-empty question and non-empty `sources`.
2. **Grounded evaluation shape** -- answering it and calling
   `evaluate_grounded_answer` returns `score` (int, 0-10), non-empty
   `strengths`/`weaknesses`/`ideal_answer`, non-empty `sources`, and a
   boolean `grounded`.
3. **Persistence** -- after running the graph's grounded path,
   `list_interviews(session_id)` contains a row with the `topic`,
   `ideal_answer`, `strengths`, `weaknesses` actually populated (not blank --
   this is the exact bug the M0 brief flagged: these fields exist today but
   are discarded).
4. **Legacy path is unchanged** -- `interview_graph.invoke({"jd": "...",
   "answer": "..."})` (no `session_id`) still returns exactly the old shape
   (`question`, `answer`, `evaluation` keys only) and does not touch
   `interview_service` at all (mock it and assert it was never called).
5. **The crash is fixed** -- mock the LLM to return malformed JSON and
   assert `evaluate_answer` returns an error dict instead of raising.

Print a clear PASS / FAIL line per assertion.

**M3 is complete when this script passes and a full question -> answer ->
evaluation round works in the browser, grounded in a real session's
documents.**
