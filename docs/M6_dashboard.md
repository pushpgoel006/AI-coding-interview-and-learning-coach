# M6 — Dashboard (implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report what changed so it can be reviewed before
> continuing. Do not implement several steps in one go. Do not refactor
> anything this brief does not name.
>
> **Prerequisite: M2, M3, M4 must be complete.** The dashboard has nothing
> to show without the data they produce. **M5 (DSA) is not required** --
> see gotcha 4 for how the dashboard handles that gap.

---

## 1. Goal

Turn a pile of resume checks, theory rounds, and follow-ups into a decision
about how to spend tomorrow. Without this, the other modules are five
disconnected tabs -- this is what closes the loop: it names your weakest
topic and gets you practicing it in two clicks.

## 2. Non-goals

Do **not** build these in M6.

- M5 (DSA round) itself. The dashboard's DSA section is a placeholder --
  see gotcha 4.
- Cross-session analytics (comparing *across* different companies/roles).
  Every metric here is scoped to the one active prep session, matching the
  per-session design principle M0 established. "You are weak on X across
  every company you've prepped for" is a real feature, but a different one,
  and not this brief.
- Any change to `services/session_service.py`, `services/resume_service.py`,
  or `services/interview_service.py`'s existing functions. M6 only adds a
  new `services/analytics.py` that reads from the same tables.
- Any change to `agents/resume_analyzer.py`, `agents/evaluator.py`,
  `agents/question_generator.py`, `agents/followup_generator.py`. M6 only
  adds a new `agents/recommender.py`.
- Forcing Streamlit to switch the visible tab programmatically. It can't
  (there is no public API for it). "Practice these" pre-fills the topic
  field for the next time the user opens that tab -- see gotcha 3.

---

## 3. Four gotchas to get right

### 3.1 Every aggregation must handle "no data yet" without crashing

A session with zero interviews, zero follow-ups, or no resume review yet is
the *normal* state for a brand-new session, not an edge case. Every function
in `analytics.py` must return `None` / `[]` / an empty-safe default rather
than dividing by zero or crashing on an empty query result. The UI must show
"Not enough data yet" rather than a stack trace.

### 3.2 A topic of `None` is not a weak topic

Interviews created without a topic (the user left the topic field blank)
have `topic = None`. Exclude these from `get_score_by_topic` and
`get_weakest_topics` entirely -- "you are weak on None" is not something a
"Practice these" button can act on.

### 3.3 Streamlit cannot jump the user to another tab

There is no supported way to make the "🎤 Theory Round" tab become the
active one from code running in the "📊 Dashboard" tab. "Practice these"
should: (1) pre-fill `st.session_state` for the interview page's topic
field with the chosen weak topic, (2) clear any in-progress thread
(`interview_pending_*`, `interview_thread_*`) so a stale thread doesn't
linger, (3) tell the user to switch tabs themselves. Do not attempt a
JavaScript workaround for this.

### 3.4 DSA data does not exist yet -- do not query for it

M5 was never built, so there is no `DsaAttempt` table. The dashboard's DSA
section must be a static "not available yet, build M5 to unlock this"
message -- never a query against a table that does not exist. When M5 is
eventually built, this section can be swapped for a real one without
touching anything else in this brief.

---

## Step 1 — Analytics service

**File:** `services/analytics.py` (new)

Pure aggregation functions, one session at a time. Every function is a
read-only query -- no writes, unlike the other `services/` modules.

```python
get_theory_average(session_id) -> float | None
get_theory_trend(session_id) -> list[dict]     # [{"date":..., "topic":..., "score":...}, ...] chronological
get_score_by_topic(session_id) -> list[dict]   # [{"topic":..., "average_score":...}, ...]
get_resume_fit_score(session_id) -> int | None # latest ResumeReview.overall_score, or None
get_weakest_topics(session_id, n=3) -> list[dict]  # lowest average_score first
get_readiness_score(session_id) -> int | None
```

Notes:

- "Theory" data combines **both** `Interview` rows (the original questions)
  and `Followup` rows (each one is also a scored answer) -- a follow-up
  inherits its parent interview's topic, so it belongs in the same
  aggregation, not a separate one.
- `get_readiness_score`: `round(0.6 * (theory_average / 10 * 100) + 0.4 *
  resume_fit_score)` when both exist. If only one exists, use it alone
  (scaled to 0-100). If neither exists, return `None` (gotcha 3.1). This
  60/40 weighting is a judgement call, not a spec -- state it plainly in
  the UI (e.g. a caption) so it is not mistaken for something precise.
- `get_weakest_topics` excludes `None`/blank topics (gotcha 3.2) and
  requires at least, say, 1 scored entry for a topic to appear at all.

**Done when:** against a session with a mix of interviews and follow-ups
across a few topics, each function returns correct, sensibly-shaped data,
and every function returns a safe empty value against a brand-new session
with nothing in it yet.

---

## Step 2 — Recommendation prompt

**File:** `prompts/recommender_prompts.py` (new)

Matches the convention every other agent module in this project follows
(`question_prompts.py`, `evaluation_prompt.py`, `followup_prompts.py`,
`resume_prompts.py` each have their own prompt file).

```python
def get_recommendation_prompt(topic: str, context: str) -> str
```

Ask for 2-3 sentences of concrete advice for improving on `topic`, pointing
at specific material in `context` where possible (e.g. "review the section
on X in your notes"). Same "use only the context, never invent" rule as
every grounded prompt in this project.

**Done when:** the function returns a prompt string containing the topic
and the context.

---

## Step 3 — Recommender agent

**File:** `agents/recommender.py` (new)

```python
def generate_recommendation(session_id: str, topic: str) -> dict
```

- Retrieve with `get_retriever(session_id).invoke(topic)`, same pattern as
  every other grounded agent function in this project.
- No documents indexed -> same empty-guard message pattern as M3/M4, no
  LLM call.
- Return `{"advice": ..., "sources": [...]}` (sources via
  `rag.citations.build_sources`).

**Done when:** given a session with real documents and a real weak topic,
returns advice that references something specific from the material.

---

## Step 4 — Dashboard UI

**File:** `ui/dashboard_page.py` (new)

- **Readiness score** -- `st.metric`, or "Not enough data yet" if `None`
  (gotcha 3.1). A caption noting it is a simple 60% theory / 40% resume
  blend.
- **Average theory score + trend** -- `st.metric` for the average,
  `st.line_chart` for the trend (or an info message if there is no theory
  data yet).
- **Score by topic** -- `st.bar_chart`, the single most useful visual per
  the master spec. Empty state if no topics yet.
- **Resume fit score** -- `st.metric`, or a prompt to run the resume check
  if `None`.
- **DSA** -- the static placeholder from gotcha 3.4.
- **Weakest 3 topics** -- listed with their average score, each with its
  own "🎯 Practice this" button. Clicking one:
  1. Sets `st.session_state[f"interview_topic_{session_id}"] = topic`.
  2. Clears `st.session_state[f"interview_pending_{session_id}"]` and
     `st.session_state[f"interview_thread_{session_id}"]` if present.
  3. Shows `st.success("Topic set -- switch to the Theory Round tab.")`
     (gotcha 3.3 -- this is the honest limit of what the code can do).

**Done when:** on a session with real theory-round history, the dashboard
shows a correct weak-topic ranking, and clicking "Practice this" actually
pre-fills that topic when you switch to the Theory Round tab and click
"New Question."

---

## Step 5 — Wire it in

**File:** `ui/app.py`

Add a fourth tab, `"📊 Dashboard"`, alongside the existing three. This is
the one place in this brief that touches a file another module owns --
call it out explicitly when you reach it, same as M2 and M3 both did for
their own UI wiring.

**Done when:** all four tabs render on a real session with no errors.

---

## Acceptance test

**File:** `test_dashboard.py` (project root, plain script like the existing
`test_*.py` files, not pytest)

Setup: create one prep session, index `uploads/Pushp_Goel_Resume.pdf` as
`doc_type="resume"`. Use `services/interview_service.record_interview` and
`record_followup` directly (no need to run the full graph / call the LLM
repeatedly) to seed a handful of interviews across at least two different
topics with clearly different score levels, so there is an obvious weakest
topic. Also seed one `ResumeReview` via `services/resume_service.save_review`.

Then assert:

1. **Brand-new empty session is safe** -- every `analytics.py` function
   called against a session with nothing in it returns its documented empty
   value, not an exception.
2. **Theory average is correct** -- matches a hand-computed average of the
   seeded scores.
3. **Score by topic is correct** -- the topic you seeded with lower scores
   comes back with a lower `average_score` than the one you seeded with
   higher scores.
4. **Weakest topics excludes blanks** -- seed one interview with
   `topic=None`; assert it never appears in `get_weakest_topics`'s result.
5. **Readiness score blends both signals** -- with both theory data and a
   resume review present, the readiness score is between the lower and
   higher of the two individual scores (a sanity check on the blend, not an
   exact-value check, since the weighting is a judgement call per gotcha's
   note in Step 1).
6. **Recommendation is grounded** -- `generate_recommendation` on the
   real weak topic returns non-empty `advice` and non-empty `sources`.

Print a clear PASS / FAIL line per assertion.

**M6 is complete when this script passes and, in the browser, the dashboard
correctly identifies a weak topic from real practice history and "Practice
this" successfully seeds that topic into the Theory Round tab.**
