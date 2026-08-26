# M2 — Resume checker (implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report what changed so it can be reviewed before
> continuing. Do not implement several steps in one go. Do not refactor
> anything this brief does not name.
>
> **Prerequisite: M0 and M1 must be complete.** This brief assumes
> `session_id` scoping (M0) and per-chunk grading conventions (M1) already
> work, and reuses their patterns rather than reinventing them.

---

## 1. Goal

Score the resume already indexed in this prep session against the JD already
indexed in it, and turn that into something actionable:

1. An overall fit score.
2. A per-requirement verdict — **clearly demonstrated / partially demonstrated
   / not demonstrated** — each backed by the resume text it came from.
3. Concrete rewrite suggestions.

### Why this module

It is the highest-value single screen in the product, and the closest to
what the codebase can already do: `SourceAwareRetriever` and the M1 grading
pattern were built for exactly this kind of multi-document reasoning. The
difference from M1 is that this is not a Q&A turn — there is no user
question. The "question" is fixed ("how well does this resume match this
JD") and the two documents being reasoned over are always the resume and the
JD for this session.

**The rule that must never break:** every "demonstrated" verdict is only as
trustworthy as the evidence line under it. A tool that invents a
qualification is actively harmful — this is the same principle M1's prompt
rewrite protected, applied here to structured output instead of free text.

## 2. Non-goals

Do **not** build these in M2.

- Theory mock round, question generation or evaluation (M3)
- Follow-up round or conversation memory (M4)
- DSA round (M5)
- Dashboard or analytics (M6)
- Any change to `agents/evaluator.py`, `agents/question_generator.py`,
  `agents/followup_generator.py`, `graphs/interview_graph.py`, `main.py`
- Any change to `rag/grader.py`, `rag/generator.py`, or the M1 chat prompt —
  this module has its own prompt and its own grounding check, kept separate
  because resume verdicts are structured data, not free-text chat answers
- Re-running the check automatically on every document upload — it runs when
  the user asks for it

---

## 3. Four gotchas to get right

### 3.1 A session might have no resume, no JD, or both

Before calling the LLM, check that both `get_documents_by_doc_type` calls
returned something. If either is empty, skip the LLM entirely and return a
specific message naming which one is missing — "Upload a resume to this
session before running the check" / "Upload a job description first." This
is the same principle as M1's gotcha 3.4 (empty retrieval must never reach
the LLM), applied to two required inputs instead of one.

### 3.2 Chunks come back from the store in no particular order

`vector_store.get(where=...)` does not guarantee chunks are returned in
reading order. When reassembling a document's full text from its chunks,
sort by `metadata["page"]` (and, within a page, by whatever stable order they
came back in) before joining — otherwise the LLM sees the resume in a
shuffled order, which makes comparison worse and evidence lines harder to
verify.

### 3.3 LLM JSON output is not guaranteed to be clean JSON

Models frequently wrap JSON in a ```` ```json ... ``` ```` fence, or add a
sentence before it. Strip a leading/trailing code fence if present, then
`json.loads`. **Wrap the parse in a try/except** and return a clear error
dict (e.g. `{"error": "..."}`) instead of letting `json.JSONDecodeError`
crash the graph. This is the exact bug the M0 brief flagged in
`evaluate_answer` — do not repeat it here.

### 3.4 Grounding check only ever downgrades, never upgrades

The ground-check step re-examines each verdict the model claimed was
"clearly demonstrated" and confirms the evidence line actually appears in
the resume context. If it does not hold up, downgrade that verdict toward
"partially demonstrated" or "not demonstrated." Never do the reverse, and
never have the ground-check invent or rewrite an evidence quote — it only
demotes claims, it does not manufacture support for them.

---

## Step 1 — Data model

**File:** `database/models.py`

Add one new table.

```python
from sqlalchemy import JSON

class ResumeReview(Base):
    __tablename__ = "resume_reviews"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    session_id     = Column(String, ForeignKey("prep_sessions.id"))
    overall_score  = Column(Integer)          # 0-100
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    suggestions    = Column(Text, default="")
    created_at     = Column(DateTime, default=datetime.utcnow)
```

No relationship back-reference on `PrepSession` is required — this table is
read through its own service, not through session traversal.

**Done when:** `init_db.py` runs clean and `resume_reviews` exists alongside
the M0 tables.

---

## Step 2 — Retrieve by document type

**File:** `rag/retriever.py`

Add one function. This is not a similarity search — there is no query. It
fetches **every** chunk of a given type in a session, for reassembly into
full text.

```python
def get_documents_by_doc_type(session_id: str, doc_type: str) -> list[Document]:
    """Fetch every chunk of one doc_type in a session, in reading order."""
```

- Use `vector_store.get(where={"$and": [{"session_id": session_id}, {"doc_type": doc_type}]}, include=["metadatas", "documents"])`.
- Reconstruct `Document` objects from the returned `documents` and
  `metadatas` lists (they come back as parallel lists, not `Document`
  objects — `Chroma.get()` does not return LangChain `Document`s the way
  `similarity_search` does).
- Sort by `metadata.get("page", 0)` before returning (gotcha 3.2).
- No matching chunks returns `[]`, not an error.

**Done when:** given a session with one resume and one JD indexed, calling
this once with `doc_type="resume"` and once with `doc_type="jd"` returns only
that document's chunks, in page order.

---

## Step 3 — Resume review service

**File:** `services/resume_service.py` (new)

Same rule as `session_service.py`: the only module allowed to touch
`ResumeReview` rows, and every function returns plain dicts.

```python
save_review(session_id, overall_score, matched_skills, missing_skills, suggestions) -> dict
get_latest_review(session_id) -> dict | None
list_reviews(session_id) -> list[dict]
```

- `list_reviews` orders newest first.
- `get_latest_review` is `list_reviews(session_id)[0]` if any exist, else
  `None`.

**Done when:** a scratch call can save a review for a session and read it
back with both functions.

---

## Step 4 — Resume analysis prompt

**File:** `prompts/resume_prompts.py` (new)

Structured JSON output, one prompt. Keep the three-way verdict labels
identical to M1's, so the UI and any later cross-referencing stay
consistent.

```python
RESUME_ANALYSIS_PROMPT = PromptTemplate.from_template(
    """
You are an AI resume-fit analyst. Compare the RESUME against the JOB
DESCRIPTION and produce a strict JSON object — nothing else, no markdown
fence, no commentary before or after it.

RULES

- Use only the text given below. Never use outside knowledge about the
  candidate, the company, or the role.
- Never invent qualifications, experience, projects or skills that are not
  in the resume text.
- Extract the individual requirements from the job description yourself —
  do not wait for them to be pre-listed.
- For each requirement, output one verdict object with:
  - "requirement": the requirement as stated or paraphrased from the JD
  - "verdict": exactly one of "clearly demonstrated", "partially demonstrated",
    "not demonstrated"
  - "evidence": a short quote or close paraphrase from the RESUME that
    justifies the verdict, or "" if not demonstrated

Return JSON matching this shape exactly:

{{
  "overall_score": <integer 0-100>,
  "verdicts": [
    {{"requirement": "...", "verdict": "...", "evidence": "..."}}
  ],
  "matched_skills": ["..."],
  "missing_skills": ["..."],
  "suggestions": "short paragraph of concrete rewrite suggestions"
}}

RESUME:
{resume_context}

JOB DESCRIPTION:
{jd_context}

JSON:
"""
)
```

**Done when:** the module imports and the template formats with
`resume_context` and `jd_context`.

---

## Step 5 — Resume analyzer agent

**File:** `agents/resume_analyzer.py` (new)

Pure functions — no retrieval, no database access. This module only knows
how to turn two blocks of text into a parsed verdict.

```python
def format_context(documents: list[Document]) -> str
def analyze_resume(resume_context: str, jd_context: str) -> dict
```

- `analyze_resume` formats `RESUME_ANALYSIS_PROMPT`, calls the LLM, strips a
  leading/trailing ` ```json ` fence if present, then `json.loads` inside a
  try/except (gotcha 3.3). On failure return
  `{"error": "Could not parse the analysis. Please try again."}` — never let
  the exception propagate.
- On success, the returned dict is exactly the JSON shape from Step 4.

**Done when:** given a short resume and JD string pair, this returns a dict
with `overall_score`, `verdicts`, `matched_skills`, `missing_skills`,
`suggestions` — and a deliberately malformed LLM response (mock it) produces
the error dict instead of a crash.

---

## Step 6 — Grounding check

**File:** `agents/resume_analyzer.py` (same file, new function)

```python
def ground_check_verdicts(verdicts: list[dict], resume_context: str) -> list[dict]
```

- For every verdict where `verdict == "clearly demonstrated"`, ask the LLM a
  single yes/no question: does `resume_context` actually support this
  `evidence` line? Reuse the same normalisation as M1's grader
  (`.strip().lower().startswith("yes")`).
- If the check comes back "no", downgrade that verdict's `"verdict"` field to
  `"not demonstrated"` and clear its `"evidence"` to `""`. Never upgrade, never
  touch verdicts that were not "clearly demonstrated" to begin with (gotcha
  3.4).
- Return the full list, same order, same length.

**Done when:** feeding a hand-built verdict list containing one true claim
and one fabricated claim against a real resume context downgrades only the
fabricated one.

---

## Step 7 — Resume graph

**File:** `graphs/resume_graph.py` (new)

Same orchestrator-only rule as `rag_graph.py`. No business logic here —
every node calls into `rag/`, `agents/`, or `services/`.

```python
class ResumeGraphState(TypedDict):
    session_id: str
    resume_documents: list[Document]
    jd_documents: list[Document]
    analysis: dict
    review: dict   # the persisted, UI-ready result
```

**Nodes**

- `retrieve_node` — calls `get_documents_by_doc_type` twice (resume, jd). If
  either list is empty, route straight to a `missing_documents_node` that
  sets a specific message naming which one is missing (gotcha 3.1) and skips
  everything else.
- `analyze_node` — builds context strings with `format_context`, calls
  `analyze_resume`. If the result contains `"error"`, route to an
  `analysis_failed_node` that surfaces that message — do not call
  `ground_check_verdicts` on a failed parse.
- `ground_check_node` — calls `ground_check_verdicts` on `analysis["verdicts"]`.
- `store_node` — calls `save_review(...)` with the (possibly downgraded)
  verdicts folded into `matched_skills`/`missing_skills` as appropriate, and
  sets `state["review"]` to the full persisted dict plus the verdict list, so
  the UI never has to reopen the database.

**Done when:** all three terminal paths work — missing documents, failed
parse, and a normal successful review — and a normal run's `review` is both
returned in state and present in `list_reviews(session_id)`.

---

## Step 8 — Resume page UI

**File:** `ui/resume_page.py` (new)

- A "🧾 Resume Check" button that invokes `resume_graph`.
- Wrap the invoke in try/except exactly like M1's chat (gotcha: every LLM
  call can fail) — show `st.error(...)` on failure, never a stack trace.
- On success: a score gauge or `st.metric` for `overall_score`, then three
  columns — **Clearly demonstrated / Partially demonstrated / Not
  demonstrated** — each listing its requirements with their evidence line
  underneath (source citation rule from the cross-cutting requirements,
  applied to this screen).
- A suggestions section rendering `suggestions` as plain text.
- If a previous review exists for this session (`get_latest_review`), show it
  on page load instead of a blank screen, with the button re-running the
  check on demand.

This file is **not wired into `ui/app.py` routing** as part of this brief —
wiring a resume tab into the app's navigation is a one-line addition once
this page works standalone; call it out explicitly when you reach it so it
can be reviewed like every other step.

**Done when:** running the check in the browser on a session with a resume
and a JD produces the three-column verdict table with evidence lines, and
reloading the page shows the same result without re-running the LLM.

---

## Acceptance test

**File:** `test_resume_review.py` (project root, plain script like the
existing `test_*.py` files, not pytest)

Setup: create one prep session, index `uploads/Pushp_Goel_Resume.pdf` as
`doc_type="resume"` and `uploads/IBM_AI_ML_Engineer_Requirements.pdf` as
`doc_type="jd"`.

Then assert:

1. **Missing documents guard** — invoke the graph on a brand-new session with
   nothing indexed. The result names a missing document and the analyzer/LLM
   is never called (mock `analyze_resume` and assert it was not called).
2. **Normal run produces valid shape** — `overall_score` is an int in
   `0..100`; every verdict's `"verdict"` is one of the three allowed labels;
   `matched_skills` and `missing_skills` are lists.
3. **Evidence is honest** — for every verdict marked "clearly demonstrated",
   its `evidence` string is a non-empty substring-or-close match of the
   reassembled resume context.
4. **Grounding check runs** — patch `ground_check_verdicts` and assert the
   graph called it exactly once with the analyzer's raw verdict list.
5. **Persistence** — after the run, `get_latest_review(session_id)` returns a
   dict whose `overall_score` matches `result["review"]["overall_score"]`.

Print a clear PASS / FAIL line per assertion.

**M2 is complete when this script passes and the three-column verdict view
works in the browser on a real resume + JD pair.**
