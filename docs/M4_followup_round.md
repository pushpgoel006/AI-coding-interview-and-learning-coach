# M4 — Follow-up round with memory (implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report what changed so it can be reviewed before
> continuing. Do not implement several steps in one go. Do not refactor
> anything this brief does not name.
>
> **Prerequisite: M3 must be complete.** This brief extends
> `graphs/interview_graph.py` and `ui/interview_page.py` again, on top of
> what M3 built.

---

## 1. Goal

After the candidate answers, the system digs deeper -- and by the third
follow-up, it still remembers what was said in the first and second. This is
the difference between a quiz (one question, one score, done) and something
that feels like an interview.

## 2. The two memories -- keep them separate

- **Conversation memory (short-term).** The running list of
  question/answer turns *within one thread* (the original question plus its
  follow-ups). Lives only in the graph state, one thread at a time. Enables
  "you said X earlier, but what about Y?"
- **Performance memory (long-term).** Scores and topics saved to the
  `Interview` / `Followup` tables, across every session that has ever
  existed. Already exists as of M3 (`interview_service.record_interview`);
  M4 extends it to also save each follow-up. Enables a *future* dashboard
  (M6) to say "you are consistently weak on SQL joins" -- M4 does not build
  that dashboard, it only makes sure the data is there for it.

Do not let these merge. Conversation memory is a Python list that exists for
the lifetime of one thread. Performance memory is rows in SQLite that
outlive every thread forever.

## 3. Non-goals

Do **not** build these in M4.

- DSA round (M5), dashboard / cross-session analytics (M6). "You are weak on
  X across all your sessions" is M6's job -- M4 only needs the `Followup`
  rows to exist with the right data in them.
- Any change to `main.py`, including its existing (and already incomplete --
  `/evaluate-followup` never actually evaluates anything) follow-up
  endpoints. Not our problem to fix; it is off-limits like every other
  module.
- Any change to `agents/resume_analyzer.py`, `graphs/resume_graph.py`, or
  the non-follow-up parts of `agents/question_generator.py` /
  `agents/evaluator.py` that M3 already built.
- A real LangGraph checkpointer / `interrupt()` mechanism for pausing a
  single `invoke()` mid-run to wait for human input. Nothing in this project
  uses that anywhere (every existing graph call, including M3's, runs start
  -to-finish synchronously). See gotcha 4.1 for the pattern this brief uses
  instead.

---

## 4. Three gotchas to get right

### 4.1 A graph call cannot pause and wait for an answer

There is no way for a single `interview_graph.invoke()` call to ask a
question, block, and resume once a human eventually types an answer --
that requires a checkpointer, which nothing in this codebase has ever used.

The pattern this brief uses instead, matching how `main.py`'s REST API
already works across separate calls: **one invoke = one evaluated turn,
plus (if the depth limit allows) the next question to ask.** The caller
(the UI, or a test) carries the running `messages` list forward and calls
`invoke()` again once the human has actually answered. This is exactly how
M3's UI already drives `generate_grounded_question` /
`evaluate_grounded_answer` directly rather than through one `invoke()` call
-- M4 extends the same idea to a multi-turn thread instead of a single turn.

### 4.2 Two different ids must not collide, again

Gotcha 3.1 from the M3 brief (do not confuse the prep session's `session_id`
with an interview's own id) gets a third id to keep straight in M4:
**`interview_id`** -- the parent `Interview` row's primary key, which every
`Followup` row must point at via its `interview_id` foreign key. A follow-up
belongs to one interview thread, not directly to a prep session.

### 4.3 The depth limit is on follow-ups, not on total turns

"Up to 3 follow-ups" means `followup_number` reaches 1, 2, 3 and then stops
-- it does not mean 3 total turns including the original question. Off-by-
one here silently gives either 2 or 4 follow-ups instead of 3. Check
`followup_number >= max_followups` (default `max_followups = 3`) before
deciding whether to generate another one.

---

## Step 1 — Data model

**File:** `database/models.py`

Add to the existing `Followup` class (this is the exact item the master
requirement sheet deferred until M4):

```python
topic      = Column(String, nullable=True)
created_at = Column(DateTime, default=datetime.utcnow)
```

`question`, `answer`, `score`, `followup_number`, `interview_id` already
exist -- do not touch them.

**Done when:** `init_db.py`'s table-creation step is unaffected by adding
these two columns to an *existing* table (same `ALTER TABLE`-style approach
as M3 Step 1 -- `create_all()` will not add columns to a table that already
exists).

---

## Step 2 — Grounded, history-aware follow-up prompt

**File:** `prompts/followup_prompts.py`

Add a new function; keep `get_followup_prompt(question, answer, score)`
exactly as it is.

```python
def get_grounded_followup_prompt(
    context: str,
    original_question: str,
    original_answer: str,
    history: list[dict],
    latest_answer: str,
    score: int,
) -> str
```

- Keep the existing score-based difficulty branching (`<=3` easier, `4-7`
  clarifying, `>=8` deeper) -- that logic is good and unrelated to grounding.
- `history` is the list of prior follow-up turns in this thread (each a
  `{"question": ..., "answer": ...}` pair). Render it plainly in the prompt
  so the model can reference something said two turns ago, not just the
  latest one.
- The question must still be grounded in `context`, the same principle as
  M3's question prompt.

**Done when:** the function returns a prompt string containing the context,
the original Q&A, every turn in `history`, and the latest answer.

---

## Step 3 — Grounded follow-up generation

**File:** `agents/followup_generator.py`

Add a new function; keep `generate_followup(question, answer, score)`
exactly as it is (`main.py` calls it positionally).

```python
def generate_grounded_followup(
    session_id: str,
    original_question: str,
    original_answer: str,
    history: list[dict],
    latest_answer: str,
    score: int,
) -> dict
```

- Retrieve the same way M3's `generate_grounded_question` does.
- Call `get_grounded_followup_prompt`, invoke the LLM.
- Return `{"question": ..., "sources": [...]}`.
- No documents indexed -> same empty-guard message pattern as M3, no LLM
  call.

Evaluating a follow-up's answer needs **no new function** -- reuse M3's
`evaluate_grounded_answer(session_id, question, answer)` unchanged. A
follow-up answer is scored exactly the same way a first answer is.

**Done when:** given a short thread history, the returned question visibly
references something from an earlier turn, not just the original answer.

---

## Step 4 — Follow-up persistence

**File:** `services/interview_service.py`

Add to this existing file (it already owns `Interview`; `Followup` is its
child table, the same relationship `session_service.py` already has with
`PrepSession` + `Document`).

```python
record_followup(interview_id, followup_number, topic, question, answer, score) -> dict
list_followups(interview_id) -> list[dict]
```

One insert per follow-up, all fields set at once (score is already known by
the time you call this, unlike `main.py`'s two-phase create-then-update
flow) -- matches `record_interview`'s one-shot pattern.

**Done when:** a scratch call records two follow-ups against one interview
and reads them back in order.

---

## Step 5 — Extend the interview graph with the follow-up loop

**File:** `graphs/interview_graph.py`

`InterviewState` gains: `messages: list[dict]`, `followup_number: int`
(defaults to 0 -- 0 means "no follow-up yet, this is the original
question"), `max_followups: int` (default 3), `next_question: str | None`,
`interview_id: str`, `sources`.

**New nodes**

- `followup_node` -- runs after `store` (original question path) or after
  `store_followup` (a follow-up path). If `followup_number >=
  max_followups` (gotcha 4.3), sets `next_question = None`. Otherwise calls
  `generate_grounded_followup` with the accumulated `messages` as `history`,
  and sets `next_question` plus appends the new question to `messages`.
- `store_followup` -- when `state.get("followup_number", 0) > 0` (i.e. this
  invocation is evaluating a follow-up answer, not the original one), calls
  `record_followup(...)` (gotcha 4.2: uses `interview_id`, never
  `session_id`) instead of `record_interview`.

**Changed routing**

- `evaluation_node` must know whether it is evaluating the *original*
  question or a *follow-up* -- branch on `state.get("followup_number", 0)`.
- After evaluating: `followup_number == 0` -> `store` (existing, M3) ->
  `followup_node` -> END. `followup_number > 0` -> `store_followup` (new) ->
  `followup_node` -> END.
- The legacy (no `session_id`) path is completely unaffected -- it never
  reaches any of these new nodes, exactly as M3 already arranged.

**Done when:** calling `invoke()` with the previous call's returned state
(plus a new `answer` for the `next_question` it returned) produces the next
evaluated follow-up turn and, if under the depth limit, another
`next_question`; at the depth limit, `next_question` comes back `None` and
no further follow-up is offered.

---

## Step 6 — Follow-up UI

**File:** `ui/interview_page.py`

After the original evaluation renders (M3's existing behaviour, untouched):

- If the graph's `next_question` came back non-empty, show it as
  "Follow-up #N" with its own answer box and submit button, exactly
  mirroring the original question's UI.
- Submitting a follow-up answer calls the graph again carrying `messages`,
  `interview_id`, and `followup_number` forward from
  `st.session_state` -- render its evaluation the same way, then show the
  *next* follow-up if one comes back, up to the depth limit.
- Render the whole thread top-to-bottom (original Q&A + every follow-up so
  far), not just the latest turn, so the candidate can see the full
  conversation.

**Done when:** a full thread -- original question, up to 3 follow-ups, each
scored -- works in the browser, and a later follow-up's question visibly
references something answered in an earlier one.

---

## Acceptance test

**File:** `test_followup_round.py` (project root, plain script like the
existing `test_*.py` files, not pytest)

Setup: create one prep session, index `uploads/Pushp_Goel_Resume.pdf` as
`doc_type="resume"` and a JD as `doc_type="jd"`.

Then assert:

1. **Thread runs to the depth limit** -- drive the graph through the
   original question and 3 follow-ups (feeding a plausible answer at each
   step). By the 3rd follow-up's response, `next_question` is `None` --
   no 4th follow-up is ever offered.
2. **A later follow-up references earlier history** -- assert the 2nd or
   3rd follow-up's question text has a non-trivial word overlap with the
   *first* follow-up's answer (not just the original answer) -- proving
   `history` is actually being used, not just the original Q&A.
3. **Persistence** -- after the thread, `list_followups(interview_id)`
   returns 3 rows, `followup_number` 1/2/3 in order, each with a non-`None`
   `score`.
4. **Legacy path still unaffected** -- `interview_graph.invoke({"jd": "...",
   "answer": "..."})` (no `session_id`) still returns exactly
   `{"jd", "answer", "question", "evaluation"}`, same regression check as
   M3.

Print a clear PASS / FAIL line per assertion.

**M4 is complete when this script passes and a real 3-follow-up thread works
in the browser, with the last follow-up demonstrably aware of what was said
in the first.**
