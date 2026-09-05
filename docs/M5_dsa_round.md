# M5 — DSA round (implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report what changed so it can be reviewed before
> continuing. Do not implement several steps in one go. Do not refactor
> anything this brief does not name.
>
> **Prerequisite: M0 must be complete** (prep sessions, `get_db()`). M5 does
> not depend on M1-M4 or M8 in any code sense, but it reuses their
> conventions throughout (plain-dict services, defensive JSON parsing,
> session-scoped data, LangGraph as pure orchestrator).

---

## 1. Goal

A DSA round that works like the theory round, but for code: the candidate
picks a topic and difficulty, gets a **real LeetCode problem** for it,
writes a solution, and an LLM judges correctness, complexity, and edge
cases -- no code execution involved anywhere.

This was cut from the original build (M5 was explicitly marked "safe to
cut"). It's being added back now, deliberately scoped smaller than a real
judge: no sandbox, no test-case execution, no arbitrary-code-execution
surface. The LLM reads the problem and the code and reasons about it, the
same way `evaluate_grounded_answer` reasons about a theory answer.

## 2. Non-goals

Do **not** build these in M5.

- Real code execution, test-case running, or any sandbox/judge
  infrastructure. This is the one thing this brief deliberately avoids --
  running arbitrary user-submitted code is a real security surface on a
  public multi-user app, and this project has no infrastructure for it.
- A LeetCode account/login integration of any kind. This only reads public
  problem data, anonymously.
- An admin UI for curating problems, or any CRUD over the local fallback
  list beyond a plain Python/JSON file checked into the repo.
- Follow-up questions on a DSA submission (no `DsaFollowup` table). One
  submission, one evaluation, matching the theory round's base loop before
  M4 added follow-ups -- do not build a DSA equivalent of M4 here.
- Any change to `graphs/rag_graph.py`, `graphs/resume_graph.py`,
  `graphs/interview_graph.py`, or their agents/prompts.
- Streaming the evaluation. Keep it a single blocking call, like M2/M3's
  base evaluation before their optional streaming steps.

---

## 3. Five gotchas to get right

### 3.1 The LeetCode API is unofficial and *will* eventually fail

There is no public, supported LeetCode API. This brief uses the same
unofficial GraphQL endpoint (`https://leetcode.com/graphql`) every
community "LeetCode helper" tool uses to read public problem data. It can
rate-limit, block, or change shape without notice -- and a shared cloud IP
(Streamlit Community Cloud) is more likely to be throttled than a local
machine. **Every call to it must have a timeout (5-8s) and a local
fallback.** The feature must degrade to the local problem list, never
crash the page and never hang it.

### 3.2 Topic names must be LeetCode's real tag slugs, not invented ones

Filtering by topic only works if the tag slug matches LeetCode's own
vocabulary exactly (e.g. `array`, `hash-table`, `two-pointers`,
`dynamic-programming`, `binary-search`, `tree`, `graph`, `linked-list`,
`stack`, `greedy`, `backtracking`, `sorting`, `string`, `heap-priority-queue`,
`sliding-window`). The topic dropdown in the UI must only ever offer
values from this fixed, known-good list -- never free text -- both because
free text won't match the API's filter and because the local fallback list
(3.1) is keyed by the same slugs.

### 3.3 LLM-only judging can be fooled by code that merely *looks* right

Without execution, the model has no ground truth. The prompt must force it
to actually trace through the logic step by step (what does this code do
on an empty input? on the smallest edge case? what's the actual time
complexity of this specific loop structure?) **before** producing a score
-- the same "determine internally, then evaluate" pattern M3's evaluation
prompt already uses, not a first-glance verdict.

### 3.4 The problem statement is LeetCode's content, not ours

Store and display the problem with a visible "via LeetCode" attribution
and a link back to `https://leetcode.com/problems/<slug>/`. Never present a
fetched problem as if this app generated it.

### 3.5 `DsaAttempt` does not need an `owner_id` column

Same rule M8 established for `Document`, `Interview`, and `ResumeReview`:
ownership is enforced once, at session lookup (`get_session(session_id,
owner_id)`). `DsaAttempt` only needs `session_id` as a foreign key to
`prep_sessions`, exactly like those three tables. Do not add an `owner_id`
column here or thread one through this module's service functions.

---

## Step 1 — Data model

**File:** `database/models.py`

```python
class DsaAttempt(Base):
    __tablename__ = "dsa_attempts"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    session_id       = Column(String, ForeignKey("prep_sessions.id"))
    topic            = Column(String, nullable=True)
    difficulty       = Column(String, nullable=True)
    problem_slug     = Column(String, nullable=True)
    problem_title    = Column(String, nullable=True)
    code             = Column(Text)
    language         = Column(String, default="python")
    score            = Column(Integer)
    correctness_notes = Column(Text, default="")
    complexity_notes  = Column(Text, default="")
    suggestions       = Column(Text, default="")
    created_at       = Column(DateTime, default=datetime.utcnow)

    session = relationship("PrepSession")
```

**Done when:** `init_db.py` runs clean and `dsa_attempts` exists.

---

## Step 2 — Local fallback problem list

**File:** `rag/dsa_fallback_problems.py` (new)

A small, hand-picked dict keyed by the exact topic slugs from gotcha 3.2,
each mapping to a few real, well-known LeetCode problems at each
difficulty. Real slugs and titles only (e.g. `two-sum`, `valid-parentheses`,
`reverse-linked-list`) -- this is the safety net when the live API is
unavailable, so it must be usable completely offline: include the full
problem statement text for each entry (written by you, factually matching
the real problem), not just a title, since there is no network fallback
for the fallback.

Shape:

```python
FALLBACK_PROBLEMS = {
    "array": {
        "easy": [{"slug": "two-sum", "title": "Two Sum", "statement": "..."}],
        "medium": [...],
        "hard": [...],
    },
    ...
}
```

Cover at least the topics listed in gotcha 3.2, at least one problem per
difficulty per topic.

**Done when:** every topic/difficulty combination the UI will offer (Step
8) has at least one fallback entry -- write a quick check script, don't
just eyeball it.

---

## Step 3 — LeetCode client

**File:** `rag/leetcode_client.py` (new)

```python
def fetch_problem(topic: str, difficulty: str) -> dict:
    """Returns {"slug", "title", "statement", "source": "leetcode" | "fallback"}.
    Tries the live LeetCode GraphQL endpoint first; on any failure
    (timeout, non-200, malformed response, empty result set), falls back
    to rag.dsa_fallback_problems and marks source as "fallback"."""
```

- Use `requests` (already a dependency) with an explicit `timeout=8`.
- Query problems filtered by tag slug + difficulty, pick one at random
  from the matches, then fetch its statement content.
- Wrap the entire live-fetch path in a single broad
  `try/except Exception` -- any failure at all falls through to the local
  list (gotcha 3.1). Log the exception with `print()` (matching this
  project's existing style of plain print-based node tracing) but never
  raise it to the caller.
- The returned `statement` must be plain text or simple markdown the UI
  can render with `st.markdown` -- strip any HTML tags LeetCode's API
  returns.

**Done when:** calling it with a bad/unreachable topic still returns a
valid dict (from the fallback), and calling it with a real topic while
online returns `source: "leetcode"` with a non-empty statement.

---

## Step 4 — DSA evaluation prompt

**File:** `prompts/dsa_prompts.py` (new)

```python
def get_dsa_evaluation_prompt(problem_statement: str, code: str, language: str) -> str
```

Rubric, adapted from M3's evaluation prompt for code instead of prose:

- Correctness (50%): does the code actually solve the stated problem? Trace
  it through the empty case, the smallest non-trivial case, and one edge
  case from the problem's own constraints, explicitly, before scoring
  (gotcha 3.3).
- Complexity (25%): state the actual time and space complexity of this
  specific code, not the theoretically optimal complexity for the problem.
- Code quality (25%): naming, structure, obvious bugs (off-by-one,
  unhandled null/empty input) separate from whether the core algorithm is
  right.

Same scoring bands and "score fairly, don't hunt for reasons to mark it
down" framing this session already applied to `evaluation_prompt.py` --
do not reintroduce the old overly-strict tone.

Return JSON:

```python
{
  "score": 0,
  "correctness_notes": "",
  "complexity_notes": "",
  "suggestions": ""
}
```

**Done when:** the function returns a prompt string containing the
problem statement, the code, and the language.

---

## Step 5 — DSA evaluator

**File:** `agents/dsa_evaluator.py` (new)

```python
def evaluate_dsa_submission(problem_statement: str, code: str, language: str) -> dict
```

Same defensive-parsing shape this session already applied to
`resume_analyzer.py` / `evaluator.py`: search-anywhere fence stripping with
a brace-extraction fallback, and retry the LLM call itself (not just
re-parse) up to 3 times on a `JSONDecodeError` before returning
`{"error": "Could not parse the evaluation. Please try again."}`.

**Done when:** a clearly-correct solution and a clearly-wrong solution to
the same real problem produce meaningfully different scores, and a mocked
malformed-JSON response (first 2 calls) recovers on the 3rd, matching the
test pattern already used for `analyze_resume`.

---

## Step 6 — DSA service

**File:** `services/dsa_service.py` (new)

```python
def record_attempt(session_id, topic, difficulty, problem_slug, problem_title,
                    code, language, score, correctness_notes, complexity_notes,
                    suggestions) -> dict
def list_attempts(session_id) -> list[dict]
```

Same `get_db()` / plain-dict rules as every other service (gotcha 3.5: no
`owner_id` parameter here).

**Done when:** a scratch call records an attempt and reads it back.

---

## Step 7 — DSA graph

**File:** `graphs/dsa_graph.py` (new)

A small `StateGraph`, matching `interview_graph.py`'s shape:

- `fetch_problem_node`: calls `rag.leetcode_client.fetch_problem(topic,
  difficulty)`, stores `slug`/`title`/`statement`/`source` in state.
- `evaluate_node`: only runs when `state.get("code")` is present -- calls
  `evaluate_dsa_submission`, then `dsa_service.record_attempt(...)`.
- Route: if `code` is absent, stop after fetching the problem (this is the
  "New Problem" click); if present, fetch is skipped (problem already in
  state from the prior turn, same one-invoke-per-turn convention as the
  interview graph) and evaluation runs.

**Done when:** invoking with just `{"session_id", "topic", "difficulty"}`
returns a problem and does not touch the database; invoking with those
plus `"code"` and the prior state's `slug`/`title`/`statement` returns a
full evaluation and a persisted `DsaAttempt` row.

---

## Step 8 — DSA round UI

**File:** `ui/dsa_page.py` (new)

- Topic selectbox (the fixed slug list from gotcha 3.2 -- show a friendly
  label, e.g. "Dynamic Programming" for `dynamic-programming`, same
  label/value mapping pattern `ui/sidebar.py`'s `DOC_TYPE_LABELS` already
  established) and a difficulty selectbox (easy/medium/hard).
- "New Problem" button -> shows the statement, its difficulty/topic, a
  "View on LeetCode" link (gotcha 3.4), and if `source == "fallback"`, a
  small caption noting live fetch wasn't available.
- A code text area (`st.text_area`, monospace via `st.code` for read-only
  bits is fine, but the input itself is a plain text area -- no live
  syntax highlighting needed) and a language selectbox (python/javascript/
  java/cpp, free enough to cover common cases).
- "Submit Solution" -> invokes the graph's evaluate path, wrapped in
  try/except showing `st.error(...)` on failure.
- Shows score, correctness notes, complexity notes, suggestions.

Not wired into `ui/app.py`'s tabs as part of this step -- call it out
explicitly when you reach it, same as M2/M3's convention, so the wiring
can be reviewed on its own.

**Done when:** a full round -- new problem, submit code, see evaluation --
works in the browser.

---

## Step 9 — Wire into the app and dashboard

**Files:** `ui/app.py`, `services/analytics.py`, `ui/dashboard_page.py`

- Add a "DSA" tab in `ui/app.py`, alongside the existing four.
- `services/analytics.py`: add `get_dsa_average(session_id)` and
  `get_dsa_topic_scores(session_id)`, same shape as the existing theory
  equivalents (`get_theory_average`, `get_score_by_topic`).
- `ui/dashboard_page.py`: replace the "DSA -- Not built yet" metric and the
  "DSA Solve Rate -- Not available yet" placeholder section with real
  numbers, using the same colored-badge pattern (`_score_color`) already
  used for theory topics. Fold DSA into the readiness score's weighting
  only if that recalculation is explicitly requested -- otherwise leave
  `get_readiness_score`'s existing 60/40 theory/resume formula untouched
  and show the DSA average as its own, separate number.

**Done when:** the Dashboard tab shows real DSA numbers after at least one
attempt is recorded, and the app's four other tabs are unaffected.

---

## Acceptance test

**File:** `test_dsa_round.py` (project root, plain script, not pytest)

1. **Fallback never crashes** -- mock the live fetch to always raise, call
   `fetch_problem` for a couple of topic/difficulty pairs, assert a valid
   problem dict comes back every time with `source == "fallback"`.
2. **Evaluation differentiates** -- for one real fallback problem, evaluate
   an obviously-correct solution and an obviously-wrong one; assert the
   correct one scores meaningfully higher.
3. **Parse-retry recovers** -- mock the LLM to return malformed JSON twice
   then valid JSON; assert `evaluate_dsa_submission` returns the parsed
   result, not the error dict.
4. **Persistence** -- run the graph's full fetch-then-submit flow on a real
   session; assert `list_attempts(session_id)` contains the row with
   `score`, `correctness_notes`, `complexity_notes` populated.
5. **No-code path is read-only** -- invoking the graph with just topic and
   difficulty (no code) does not create a `DsaAttempt` row (mock
   `dsa_service.record_attempt` and assert it was never called).

Print a clear PASS / FAIL line per assertion.

**M5 is complete when this script passes and a full round -- pick topic and
difficulty, get a real LeetCode problem, submit code, see a fair evaluation
-- works in the browser, and the Dashboard shows real DSA numbers.**
