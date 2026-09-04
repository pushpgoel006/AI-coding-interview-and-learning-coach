# M8 — Login & Multi-User Isolation, then Agentic RAG (full implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report exactly what changed, then wait to be told
> to continue. Do not implement several steps in one turn. Do not refactor
> anything this brief does not name. Do not skip ahead to Part B before every
> step of Part A is verified working.
>
> This file replaces `docs/M8_auth.md` and `docs/M9_agentic_rag.md`. Those two
> files now just point here — use this one.

---

## Tech stack this brief needs

Nothing here requires a new hosting service, a new account, or a new API key.
Everything is either already in this project or a plain Python library.

| Purpose | Library | Status in this project |
|---|---|---|
| Password hashing | `bcrypt` | Already in `requirements.txt`. Add it to `pyproject.toml` too (Step 0) so `uv` tracks it as a real dependency, not an incidental one. |
| User + session storage | SQLAlchemy models on the existing Neon Postgres database | No new database. One new table (`users`), one new column (`prep_sessions.owner_id`). |
| Login form | Plain Streamlit (`st.tabs`, `st.text_input`, `st.form`, `st.error`) | Already the UI framework. No new import for the form itself. |
| Gating the app on login | `st.session_state` | Already used for chat history and the active prep session. Same mechanism, one more key. |
| **Surviving a page refresh while logged in** | `extra-streamlit-components` (its `CookieManager`) | **New dependency.** `st.session_state` alone is wiped by a hard reload — a browser tab starting fresh has no memory of who was logged in. This writes one small cookie in the browser so login survives a reload. This is required in this brief, not optional. |
| Retry / decomposition prompts for agentic RAG | `models.llm_provider.get_llm()` (Groq, already wired) | No new library at all. |

Add to `pyproject.toml` dependencies: `bcrypt` and `extra-streamlit-components`.
Run `uv sync` (or the project's usual dependency install command) after Step 0.

---

# PART A — Login & multi-user isolation

## A.1 The problem, precisely

`services/session_service.list_sessions()` has no owner filter. Every visitor
to the deployed app sees the same dropdown of **every prep session anyone has
ever created** — every company name, and one click away, someone else's
resume, interview answers and scores.

This is a data isolation bug, not a UI polish issue. It exists because nothing
in the data model records *who* a `PrepSession` belongs to. Adding a login
screen without adding ownership would just put a password prompt in front of
the same leak. The real fix is one column — `PrepSession.owner_id` — and then
every read of a session, its documents, its interviews and its resume reviews
must be scoped to the logged-in user.

## A.2 Decisions already made

- Existing `prep_sessions`, `documents`, `interviews`, `followups` and
  `resume_reviews` rows in the Neon database belong to no one and will be
  **deleted**, not migrated. It is test data. Starting `owner_id` as
  `nullable=False` from day one is simpler than writing a backfill for data
  nobody needs to keep.
- Login method: **email + password**, hashed with `bcrypt`. No OAuth, no
  external identity provider.
- Login **must survive a hard browser refresh**. A demo where refreshing the
  page logs the user out looks broken, even though the underlying auth is
  sound — so the cookie-based persistence in Step 7 is part of the required
  build, not a follow-up.

## A.3 Non-goals

- Password reset / forgot-password flow — out of scope for now, note it as a
  known gap in the README
- Email verification
- Google or any OAuth sign-in
- Authenticating `main.py` (the FastAPI endpoints) — separate concern, note as
  a known limitation, do not build it here
- Roles or permissions beyond "owns a session" / "does not"

## A.4 Four gotchas to get right

### A.4.1 Never compare passwords, or fail open

Two mistakes are easy to make by accident:

```python
if user.password == password:            # WRONG — never store plain text
if bcrypt.checkpw(...) or user is None:   # WRONG — this logs in on any error
```

Always: hash on signup, `bcrypt.checkpw(entered.encode(), stored_hash)` on
login, and if the user is not found, run a dummy `bcrypt.checkpw` against a
throwaway hash anyway before returning failure. This avoids a timing
difference between "wrong password" and "no such user" that a real login
system should not leak.

### A.4.2 Ownership must be checked on every read, not just the list

Filtering `list_sessions()` by `owner_id` stops the dropdown leak, but if
`get_session(session_id)` doesn't also check ownership, a user who somehow
obtains another session's UUID could still load it directly. Every function
that fetches a single session must take `owner_id` and return `None` if it
does not match — not raise, not partially load, just return nothing.

### A.4.3 `CookieManager` needs a render round-trip before it works

`extra-streamlit-components`'s `CookieManager` is itself a Streamlit
component — on the very first run of a session, its `get_all()` call can
return an empty dict even if a cookie actually exists in the browser, because
the component hasn't finished its first round-trip yet. **Do not treat an
empty cookie read on the first render as "definitely logged out."** The
standard pattern:

```python
cookies = cookie_manager.get_all()
if cookies is None:
    st.stop()   # component not ready yet; Streamlit will rerun automatically
```

Skipping this check causes an intermittent bug where a genuinely logged-in
user occasionally sees the login page for one frame after a refresh.

### A.4.4 The cookie stores a user id, never a password

The cookie should contain only the user's `id` (a UUID, meaningless without
the database) and nothing else — never the password, never the password hash.
On every rerun, look up the user fresh from the database using that id; do not
trust any other field from the cookie.

---

## Step 0 — Add dependencies

**File:** `pyproject.toml`

Add `bcrypt` and `extra-streamlit-components` to `dependencies`. Run the
project's install command. Confirm both import cleanly:

```python
import bcrypt
import extra_streamlit_components as stx
```

**Done when:** both imports succeed with no error.

---

## Step 1 — User model

**File:** `database/models.py`

```python
class User(Base):
    __tablename__ = "users"

    id            = Column(String, primary_key=True)   # uuid4 string
    email         = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    display_name  = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("PrepSession", back_populates="owner")
```

On `PrepSession`, add:

```python
owner_id = Column(String, ForeignKey("users.id"), nullable=False)
owner    = relationship("User", back_populates="sessions")
```

**Done when:** the models import cleanly. Do not run `init_db.py` yet — the
data wipe in Step 2 must happen first.

---

## Step 2 — Wipe orphaned data

Existing rows have no owner and will not fit the new `nullable=False`
constraint.

```python
# scratch script, run once, then discard
from database.db import engine, Base
from database.models import PrepSession, Document, Interview, Followup, ResumeReview

for model in [ResumeReview, Followup, Interview, Document, PrepSession]:
    model.__table__.drop(engine, checkfirst=True)

Base.metadata.create_all(bind=engine)
```

Order matters — child tables drop before the parent (`PrepSession`) they
foreign-key to.

Also delete the local vector store so no orphaned vectors from deleted
sessions linger on disk: `rm -rf chroma_db/`.

**Done when:** `init_db.py` runs clean and `prep_sessions`, `documents`,
`interviews`, `followups`, `resume_reviews`, and the new `users` table all
exist, empty.

---

## Step 3 — Auth service

**File:** `services/auth_service.py` (new)

Same rule as every other service in this project: **return plain dicts, never
ORM objects** — the existing services already follow this pattern, match it.

```python
import bcrypt

def register_user(email: str, password: str, display_name: str) -> dict:
    """Raises ValueError if the email is already registered, or if the
    email/password fail basic validation."""

def verify_login(email: str, password: str) -> dict | None:
    """Returns the user dict on success, None on failure. Always performs
    a bcrypt comparison even for an unknown email (gotcha A.4.1)."""

def get_user(user_id: str) -> dict | None:
    ...
```

Validate before hashing: email is non-empty and contains `@`; password is at
least 8 characters. Raise `ValueError` with a message the UI can show
directly — never leak a stack trace.

```python
password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
```

**Done when:** a scratch script can register a user, fail to register the same
email twice, log in with the right password, and fail to log in with the
wrong one.

---

## Step 4 — Scope the session service by owner

**File:** `services/session_service.py`

Every function that touches a `PrepSession` gains an `owner_id` parameter and
a matching filter.

```python
def create_session(owner_id: str, company_name: str, role: str, jd_text: str = "") -> dict:
    # stamp owner_id on the new PrepSession

def list_sessions(owner_id: str, include_archived: bool = False) -> list[dict]:
    # filter PrepSession.owner_id == owner_id

def get_session(session_id: str, owner_id: str) -> dict | None:
    # filter BOTH session_id AND owner_id (gotcha A.4.2)
    # a mismatch returns None, exactly like "not found"

def archive_session(session_id: str, owner_id: str) -> None:
    # same ownership filter before archiving
```

`record_document`, `list_documents` and `delete_session_documents` do **not**
need an `owner_id` parameter — by the time the UI has a `session_id`, it has
already come from an owner-checked `get_session`. The boundary is enforced
once, at session lookup.

**Done when:** calling `get_session(real_id, wrong_owner_id)` returns `None`.

---

## Step 5 — Login UI (without persistence yet)

**File:** `ui/auth_page.py` (new)

One function, `render_auth_page() -> dict | None`, returning the logged-in
user dict or `None`.

- Two tabs via `st.tabs`: **Log in** and **Sign up**.
- Log in: email, password, submit. On success, store the user dict in
  `st.session_state.current_user` and `st.rerun()`. On failure, `st.error`
  with a generic "Invalid email or password" — never reveal whether the email
  existed.
- Sign up: email, display name, password, confirm password. Check the two
  passwords match client-side before calling `register_user`. Surface
  `ValueError` messages from the service directly.

**Done when:** the page renders standalone and both flows work against the
Step 3 auth service, using only `st.session_state` (no cookie yet — that is
Step 7).

---

## Step 6 — Gate the app

**File:** `ui/app.py`

At the very top of `main()`, before anything else renders:

```python
if "current_user" not in st.session_state:
    render_auth_page()
    return
```

Every call to `list_sessions`, `create_session`, and `get_session` in
`ui/session_selector.py` and `ui/app.py` now passes
`st.session_state.current_user["id"]` as `owner_id`.

Add a logout affordance in the sidebar — for now, clears
`st.session_state.current_user` and calls `st.rerun()`. Step 8 extends this to
also clear the cookie. Show the logged-in user's display name next to it
("Signed in as Pushp — Log out").

**Done when:** the app is unusable without logging in, and after logging in,
`list_sessions` only ever shows the current user's own sessions. (A hard
refresh will still log the user out at this point — that's expected, Step 7
fixes it.)

---

## Step 7 — Persist login across a refresh with a cookie

**File:** `ui/auth_page.py` (extend), `ui/app.py` (extend)

This is the step that makes login behave like a real login instead of
something that resets on F5.

Create one shared `CookieManager` instance, used everywhere the app checks or
sets the login cookie:

```python
import extra_streamlit_components as stx

def get_cookie_manager():
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager()
    return st.session_state.cookie_manager
```

On successful login or signup (in `ui/auth_page.py`):

```python
cookie_manager = get_cookie_manager()
cookie_manager.set("user_id", user["id"], key="set_login_cookie")
```

At the top of `ui/app.py`'s `main()`, **before** the `current_user` check from
Step 6, restore the session from the cookie if it exists:

```python
cookie_manager = get_cookie_manager()
cookies = cookie_manager.get_all()

if cookies is None:
    st.stop()   # component not ready yet (gotcha A.4.3)

if "current_user" not in st.session_state:
    cookie_user_id = cookies.get("user_id")
    if cookie_user_id:
        user = get_user(cookie_user_id)
        if user:
            st.session_state.current_user = user

if "current_user" not in st.session_state:
    render_auth_page()
    return
```

Only store `user["id"]` in the cookie (gotcha A.4.4) — never the password or
password hash. Every rerun re-fetches the current user dict fresh from the
database using that id, so a change to the user's `display_name` or a
deactivated account (if that concept is ever added) takes effect immediately.

---

## Step 8 — Logout clears the cookie too

**File:** wherever the Step 6 logout button lives

```python
if st.button("Log out"):
    cookie_manager = get_cookie_manager()
    cookie_manager.delete("user_id", key="delete_login_cookie")
    del st.session_state["current_user"]
    st.rerun()
```

Without this, logging out only clears server-side state — the browser still
holds the cookie, and the next reload silently logs the same user back in.

**Done when:** logging in, then hitting a hard refresh (not just clicking
around the app), keeps the user logged in. Logging out, then refreshing,
shows the login page.

---

## Acceptance test for Part A

**File:** `test_auth.py` (project root, plain script like the existing test
files, not pytest)

The cookie round-trip (Steps 7–8) is browser behavior and cannot be exercised
by a headless script — verify that part manually in the browser as described
above. Everything else is testable directly:

1. Register user A and user B with different emails.
2. Assert registering A's email again raises `ValueError`.
3. Assert `verify_login` with A's correct password returns a dict, and with
   the wrong password returns `None`.
4. A creates two sessions, B creates one.
5. Assert `list_sessions(A["id"])` returns exactly A's two sessions — never
   B's.
6. Assert `get_session(one_of_bs_session_ids, owner_id=A["id"])` returns
   `None`.
7. Assert `get_session(one_of_as_session_ids, owner_id=A["id"])` returns the
   session.

Print a clear PASS / FAIL line per assertion.

**Part A is complete when this script passes, two different accounts each see
only their own prep sessions in the browser, and a hard refresh no longer logs
either account out.**

---

# PART B — Agentic RAG upgrade

> **Prerequisite: M1 (per-chunk grading, `no_documents` / `not_found` /
> `generate` routing, `build_sources`) must already be in `graphs/rag_graph.py`.**
> Re-read that file before starting. Part B does not depend on Part A being
> finished — it can be built independently — but do not start it until Part A
> is at least code-complete, to avoid two half-finished features in flight at
> once.

## B.1 What "agentic" means here, concretely

Plain RAG is a straight line: retrieve once, grade once, generate once. If the
first retrieval is weak, the whole answer is weak — there is no way for the
system to notice and try again.

Agentic RAG means the graph can **make a decision and loop**, instead of
always walking the same fixed path. This brief adds exactly two decision
points to the existing graph. It is the same `StateGraph`, with one more
conditional edge and a counter — not a new framework.

1. **Self-correcting retrieval.** If grading throws away everything retrieved,
   instead of jumping straight to `not_found`, rewrite the query once and try
   retrieval again. This directly targets a failure already seen in this
   project: the grader saying "no" because of a phrasing mismatch, not because
   the information is truly missing.

2. **Query decomposition.** If a question bundles several distinct asks
   together — the project's own six-requirement "is this candidate capable"
   test case — split it into sub-questions, retrieve and grade for each one
   separately, then answer from the combined evidence. One global top-k search
   cannot cover six unrelated requirements at once; six focused searches can.

Both are additions to the **existing** `rag_graph`. `agents/`,
`graphs/interview_graph.py` and `graphs/resume_graph.py` are not touched here.

## B.2 Non-goals

- Rewriting the interview or resume graphs
- A general-purpose "agent" that can call arbitrary tools
- Parallel retrieval for decomposed sub-questions — sequential first,
  correctness over speed
- Any change to the login/session work in Part A — this brief assumes
  `session_id` already flows through `get_retriever` exactly as it does today

## B.3 Two gotchas to get right

### B.3.1 A retry loop needs a hard stop

Without a counter, a graph edge that loops back to `retrieve` on failure can
in principle loop forever. **Every loop-back edge here must check a counter in
state and cap retries at 2.** "Still no relevant documents after 2 retries" is
an answerable outcome (`not_found`), not a bug to chase further.

### B.3.2 Decomposition must not enlarge the model's inputs unboundedly

If a question decomposes into 6 sub-questions and each retrieves separately,
that is 6x the retrieval and grading calls of before. Cap the number of
sub-questions at 5, and validate the LLM's output — if it returns something
that isn't a clean list of short questions, fall back to treating the original
question as a single one rather than crashing.

---

## Step 1 — Query rewriter (for the retry loop)

**File:** `prompts/query_rewrite_prompt.py` (new)

```python
from langchain_core.prompts import PromptTemplate

QUERY_REWRITE_PROMPT = PromptTemplate.from_template(
    """
The following question did not retrieve useful results from a document
search. Rewrite it as a single, different search query that is more likely to
find relevant passages - use different wording, synonyms, or a more specific
or more general phrasing than the original.

Return ONLY the rewritten query. No explanation, no quotes.

Original question:
{question}

Rewritten query:
"""
)
```

**File:** `rag/query_rewriter.py` (new)

```python
from models.llm_provider import get_llm
from prompts.query_rewrite_prompt import QUERY_REWRITE_PROMPT


def rewrite_query(question: str) -> str:
    prompt = QUERY_REWRITE_PROMPT.format(question=question)
    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content.strip()
```

**Done when:** calling it with a question returns a different, non-empty
string.

---

## Step 2 — Question decomposer

**File:** `prompts/decompose_prompt.py` (new)

```python
from langchain_core.prompts import PromptTemplate

DECOMPOSE_PROMPT = PromptTemplate.from_template(
    """
Look at the question below. If it asks about MULTIPLE distinct requirements,
skills, or topics that should each be checked separately against a document,
break it into separate short sub-questions - one per requirement or topic.

If the question is already a single, focused question, return it unchanged as
the only item.

Return each sub-question on its own line, with no numbering, no bullets, and
no extra commentary. Return at most 5 sub-questions.

Question:
{question}

Sub-questions:
"""
)
```

**File:** `rag/query_decomposer.py` (new)

```python
from models.llm_provider import get_llm
from prompts.decompose_prompt import DECOMPOSE_PROMPT


def decompose_question(question: str) -> list[str]:
    """Returns 1-5 sub-questions. Falls back to [question] on any
    parsing failure - decomposition failing must never break the graph."""
    prompt = DECOMPOSE_PROMPT.format(question=question)
    llm = get_llm()
    response = llm.invoke(prompt)

    lines = [line.strip() for line in response.content.strip().split("\n")]
    lines = [line for line in lines if line]

    if not lines or len(lines) > 5:
        return [question]

    return lines
```

**Done when:** a single-topic question returns a one-item list containing
(approximately) itself, and the six-requirement test question returns
multiple items.

---

## Step 3 — Extend `GraphState`

**File:** `graphs/rag_graph.py`

Add three fields to the existing `GraphState`:

```python
class GraphState(TypedDict):
    question: str
    session_id: str
    documents: list[Document]
    relevant_documents: list[Document]
    grade: str
    sources: list[dict]
    answer: str
    retry_count: int          # new - defaults to 0, capped at 2 (gotcha B.3.1)
    sub_questions: list[str]  # new - [] means "not decomposed"
```

`retriever_node` must initialise `retry_count` using
`state.get("retry_count", 0)` rather than assuming the caller set it.

**Done when:** the graph still compiles with the added fields.

---

## Step 4 — Add the retry loop

**File:** `graphs/rag_graph.py`

```python
from rag.query_rewriter import rewrite_query


def rewrite_and_retry_node(state: GraphState):
    print(">>> REWRITE NODE (retry", state.get("retry_count", 0) + 1, ")")

    new_question = rewrite_query(state["question"])

    print("Rewritten query:", new_question)

    state["question"] = new_question
    state["retry_count"] = state.get("retry_count", 0) + 1

    return state
```

This overwrites `state["question"]` with the rewritten version for the retry.
Answering using the rewritten question is acceptable for this pass — the goal
is recovering useful context, not preserving exact phrasing.

Change `route_after_grader`:

```python
def route_after_grader(state: GraphState):
    if state["relevant_documents"]:
        return "generate"

    if state.get("retry_count", 0) < 2:
        return "retry"

    return "not_found"
```

Wire the loop:

```python
graph.add_node("retry", rewrite_and_retry_node)

graph.add_conditional_edges(
    "grader",
    route_after_grader,
    {
        "generate": "generate",
        "retry": "retry",
        "not_found": "not_found",
    },
)

graph.add_edge("retry", "retrieve")
```

**Done when:** a query worded oddly enough to fail grading on the first try
succeeds on the second, visible in the printed trace as
`RETRIEVER NODE -> GRADER NODE (fail) -> REWRITE NODE -> RETRIEVER NODE ->
GRADER NODE (pass) -> GENERATE NODE`.

---

## Step 5 — Add decomposition for multi-part questions

**File:** `graphs/rag_graph.py`

This runs before `retrieve`, as a new entry step.

```python
from rag.query_decomposer import decompose_question


def decompose_node(state: GraphState):
    print(">>> DECOMPOSE NODE")

    sub_questions = decompose_question(state["question"])

    print("Sub-questions:", len(sub_questions))

    state["sub_questions"] = sub_questions

    return state
```

If `len(sub_questions) == 1`, the rest of the graph behaves exactly as before.

If there is more than one, add a wrapper node that loops over them:

```python
from rag.retriever import get_retriever
from rag.grader import filter_relevant_documents


def multi_retrieve_node(state: GraphState):
    print(">>> MULTI-RETRIEVE NODE")

    all_relevant = []
    for sub_q in state["sub_questions"]:
        retriever = get_retriever(state["session_id"])
        docs = retriever.invoke(sub_q)
        relevant, _ = filter_relevant_documents(sub_q, docs)
        all_relevant.extend(relevant)

    # de-duplicate by (file_name, page) so a chunk retrieved for two
    # sub-questions isn't cited or included twice
    seen = set()
    deduped = []
    for doc in all_relevant:
        key = (doc.metadata.get("file_name"), doc.metadata.get("page"))
        if key not in seen:
            seen.add(key)
            deduped.append(doc)

    state["relevant_documents"] = deduped
    state["documents"] = deduped

    return state


def route_after_decompose(state: GraphState):
    if len(state["sub_questions"]) > 1:
        return "multi_retrieve"
    return "retrieve"
```

Wire it: `START -> decompose -> (retrieve | multi_retrieve)`. The single-path
branch (`retrieve`) continues into `grader` exactly as before, including the
Step 4 retry loop. The `multi_retrieve` branch already produces graded,
deduplicated `relevant_documents`, so it routes straight into the existing
`route_after_grader` logic (`generate` if non-empty, `not_found` otherwise) —
reuse that conditional edge rather than duplicating the routing rule.

**Done when:** the six-requirement Data Analyst test question visibly produces
multiple sub-questions in the trace, each retrieves separately, and the final
answer draws on evidence gathered from more than one targeted search.

---

## Step 6 (optional polish) — Surface the reasoning in the UI

**File:** `ui/chat.py`

If `state["sub_questions"]` has more than one entry, show them in a small
`st.caption` or expander above the answer: "Broken into: ...". This is a good
demo moment — it makes the agentic behavior visible. Only do this after Steps
1–5 are verified working.

---

## Acceptance test for Part B

**File:** `test_agentic_rag.py` (project root, plain script)

Using a session with the resume and a job description indexed (reuse the
fixture pattern from `test_citations.py`):

1. **Retry recovers a bad query.** Ask a question phrased unusually enough
   that the first retrieval is likely to fail grading (or, to make this
   deterministic, temporarily monkeypatch `filter_relevant_documents` to
   return empty on the first call only). Assert the final answer is not the
   refusal sentence, and `retry_count >= 1` in the resulting state.

2. **Retry gives up after 2 tries.** Ask about something genuinely absurd and
   not in any indexed document. Assert the final answer **is** the refusal
   sentence, and `retry_count == 2` — not more.

3. **Decomposition triggers on the six-requirement test question.** Run the
   project's own Data Analyst capability question. Assert
   `len(result["sub_questions"]) > 1`.

4. **Decomposition does not trigger on a simple question.** Ask "what
   programming languages does the candidate know?" Assert
   `len(result["sub_questions"]) == 1`.

5. **Decomposed answers still cite sources.** For the multi-part question,
   assert `result["sources"]` is non-empty.

Print a clear PASS / FAIL line per assertion.

**Part B is complete when this script passes and the printed trace for the
six-requirement question visibly shows decomposition and per-sub-question
retrieval happening.**

---

# Overall done condition

M8 is complete when **both** Part A's acceptance test passes and Part B's
acceptance test passes, and, in the browser: two different accounts each see
only their own prep sessions, login survives a hard refresh, and the
six-requirement capability question visibly triggers decomposition in the
printed trace.
