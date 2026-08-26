# M0 — Prep Sessions (implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report what changed so it can be reviewed before
> continuing. Do not implement several steps in one go. Do not refactor
> anything this brief does not name.

---

## 1. Goal

Every document, question, answer and score in this application must belong to a
**prep session** — one company + role the user is preparing for.

Today everything is global: one Chroma collection, one uploads folder, one
`interviews` table with no owner. That makes the future dashboard meaningless
(an average across two unrelated companies carries no information) and lets
retrieval serve company A's material while the user is preparing for company B.

After M0:

- The user picks or creates a session before doing anything else.
- Documents are indexed **into** that session.
- Retrieval is filtered to that session.
- Interview rows are linked to that session.

## 2. Non-goals

Do **not** build any of these in M0. They belong to later modules.

- Source citations in chat (M1)
- Resume analysis (M2)
- Grounded question generation, evaluator changes (M3)
- Conversation memory (M4)
- Dashboard, analytics (M6)
- Any change to `main.py`, `agents/`, `graphs/interview_graph.py`
- OCR, authentication, deployment

`main.py` must keep working. Adding a nullable `session_id` column to
`Interview` is backwards compatible — existing endpoints will simply leave it
`NULL`. Verify this, do not "fix" it.

## 3. Before starting: clear the old data

Existing vectors have no `session_id` in their metadata, so once filtering is
in place they match nothing and just consume space. Existing DB rows cannot
take a foreign key cleanly in SQLite.

Delete both:

```
rm -rf chroma_db/
rm -f interviews.db
```

`uploads/` is **kept** — the PDFs there get re-indexed into a real session
later. Confirm `.gitignore` covers `chroma_db/` and `interviews.db`.

## 4. Three gotchas to get right

These are the parts most likely to produce confusing bugs. Read before coding.

### 4.1 Detached SQLAlchemy objects

The existing code pattern is `db = SessionLocal()` … `db.close()`. If a
function returns an ORM object **after** closing the session, reading any
attribute later raises `DetachedInstanceError`.

**Rule for `services/session_service.py`: never return ORM objects.** Convert to
plain `dict` before the session closes. This also keeps the UI layer free of
ORM knowledge, which matches the project's separation rules.

### 4.2 Chroma needs `$and` for multiple filter conditions

A `where` filter with two keys is **not** valid. This is wrong:

```python
filter={"session_id": sid, "source": src}      # WRONG
```

This is correct:

```python
filter={"$and": [{"session_id": sid}, {"source": src}]}
```

A single condition stays flat: `filter={"session_id": sid}`.

### 4.3 Deleting a session's vectors

`langchain_chroma`'s `delete()` takes **ids**, not a `where` filter. To delete
one session's vectors, fetch the matching ids first, then delete them:

```python
found = vector_store.get(where={"session_id": session_id})
ids = found.get("ids", [])
if ids:
    vector_store.delete(ids=ids)
```

Never call `delete_collection()` for a per-session clear — that destroys every
session's data.

---

## Step 1 — Database models

**File:** `database/models.py`

Add two new tables and one column.

```python
class PrepSession(Base):
    __tablename__ = "prep_sessions"

    id           = Column(String, primary_key=True)      # uuid4 string
    company_name = Column(String, nullable=False)
    role         = Column(String, nullable=False)
    jd_text      = Column(Text, default="")
    status       = Column(String, default="active")      # active | archived
    created_at   = Column(DateTime, default=datetime.utcnow)

    documents  = relationship("Document", back_populates="session",
                              cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="session")


class Document(Base):
    __tablename__ = "documents"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    session_id  = Column(String, ForeignKey("prep_sessions.id"))
    file_name   = Column(String)
    file_path   = Column(String)
    doc_type    = Column(String)     # company | jd | resume | notes | experience
    chunk_count = Column(Integer, default=0)
    indexed_at  = Column(DateTime, default=datetime.utcnow)

    session = relationship("PrepSession", back_populates="documents")
```

On the existing `Interview` class add:

```python
session_id = Column(String, ForeignKey("prep_sessions.id"), nullable=True)
session    = relationship("PrepSession", back_populates="interviews")
```

Leave `Followup` untouched. Do not add `topic` / `ideal_answer` / `strengths` /
`weaknesses` — those are M3.

**Also:** confirm `database/init_db.py` still creates all tables (it calls
`Base.metadata.create_all`, so importing the new models is enough). Run it once
and confirm `prep_sessions` and `documents` exist.

**Done when:** `init_db.py` runs clean and creates a fresh `interviews.db` with
four tables.

---

## Step 2 — A safe DB session helper

**File:** `database/db.py`

Add a context manager so no code path can leak an open session:

```python
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

Do **not** rewrite existing callers in `main.py` to use it. New code only.

**Done when:** the helper exists and is importable.

---

## Step 3 — Session service

**File:** `services/session_service.py` (new package — add `services/__init__.py`)

This is the only module allowed to touch `PrepSession` and `Document` rows.
Every function returns plain dicts (see gotcha 4.1).

```python
create_session(company_name, role, jd_text="") -> dict
list_sessions(include_archived=False)          -> list[dict]
get_session(session_id)                        -> dict | None
archive_session(session_id)                    -> None

record_document(session_id, file_name, file_path, doc_type, chunk_count) -> dict
list_documents(session_id)                     -> list[dict]
delete_session_documents(session_id)           -> None   # DB rows only
```

Notes:

- `create_session` generates the id with `str(uuid.uuid4())`.
- `list_sessions` orders newest first.
- `record_document` should **update in place** if a document with the same
  `session_id` + `file_name` already exists, rather than inserting a duplicate.
  Re-uploading the same file is normal user behaviour.
- `delete_session_documents` removes DB rows only. Vector deletion lives in
  the indexer (Step 5), so each layer keeps its own responsibility.

**Done when:** a scratch script can create two sessions, list them, add a
document row to one, and read it back.

---

## Step 4 — Retriever scoping

**File:** `rag/retriever.py`

`SourceAwareRetriever` gains a required `session_id`.

- `__init__(self, vector_store, session_id, k=4)`
- `_sources()` must list sources **within this session only**:
  `self.vector_store.get(where={"session_id": self.session_id}, include=["metadatas"])`
- `invoke()`:
  - single source → `similarity_search(query, k=self.k, filter={"session_id": sid})`
  - multiple sources → per-source search using the `$and` form from gotcha 4.2
- `get_retriever(session_id, k=4)` — `session_id` first and required, so no
  caller can accidentally query globally.

Keep the existing "split k across sources" behaviour exactly as it is. That
logic is correct and is not being changed.

**Done when:** `get_retriever("nonexistent-id").invoke("anything")` returns an
empty list rather than another session's chunks.

---

## Step 5 — Indexer scoping

**File:** `rag/indexer.py`

Signature becomes:

```python
index_documents(file_paths, session_id, doc_type="company") -> int
```

Changes:

1. Stamp `session_id` and `doc_type` into every document's metadata, alongside
   the existing `source` and `file_name`.
2. **Remove the `clear_index()` call.** This is the bug where processing a
   second batch destroyed the first. A session must be able to accumulate a
   resume *and* a JD *and* notes — that is the whole point of the product.
3. Add `clear_session_index(session_id)` using the id-fetch-then-delete pattern
   from gotcha 4.3.
4. `list_indexed_documents(session_id)` — filter by session.
5. Keep `clear_index()` (full wipe) but make it clearly a developer/debug
   utility, not something the UI calls.

**Done when:** indexing file A then file B into the same session leaves both
retrievable, and `clear_session_index` on session 1 leaves session 2 intact.

---

## Step 6 — RAG graph

**File:** `graphs/rag_graph.py`

- `GraphState` gains `session_id: str`.
- `retriever_node` calls `get_retriever(state["session_id"])`.

Nothing else changes. No new nodes, no new business logic — the graph stays an
orchestrator.

**Done when:** `rag_graph.invoke({"question": q, "session_id": sid})` works and
respects the session.

---

## Step 7 — Session selector UI

**File:** `ui/session_selector.py` (new)

At the **top of the sidebar**, above documents:

- A `st.selectbox` of existing sessions, labelled `f"{company_name} — {role}"`.
- An expander "➕ New prep session" containing company name, role, an optional
  JD textarea, and a Create button.
- Store the choice in `st.session_state.active_session_id`.
- Return the active session dict, or `None` if none exists.

Creating a session should select it immediately and `st.rerun()`.

**Done when:** the selector renders, creates sessions, and the selection
survives a rerun.

---

## Step 8 — Wire the UI together

**Files:** `ui/app.py`, `ui/sidebar.py`, `ui/chat.py`

`ui/app.py`

- Render the session selector first.
- If there is no active session, show an informative message
  ("Create a prep session to get started") and `return` — do not render chat or
  the uploader.
- Pass `session_id` and the chosen `doc_type` into `index_documents`.
- Call `record_document` after a successful index.
- Pass `session_id` into `render_chat`.

`ui/sidebar.py`

- Add a `st.selectbox` for document type: company / jd / resume / notes /
  experience. This is required — M2 and M3 depend on knowing which file is the
  resume and which is the JD.
- Add the **📚 Indexed Documents** section the spec asks for, listing this
  session's documents with their type. Use `list_documents(session_id)`.
- The Clear button now calls `clear_session_index` + `delete_session_documents`
  and its label should say it clears *this session*.

`ui/chat.py`

- Accept `session_id` and pass it into `rag_graph.invoke`.
- Key chat history per session: `st.session_state.messages[session_id]`, so
  switching sessions switches conversations instead of mixing them.

**Done when:** the full loop works in the browser — create session, upload with
a type, process, see it listed, ask a question, get an answer from that
session's documents only.

---

## Step 9 (optional) — Cache the embedding model

**File:** `rag/embeddings.py`

`get_embedding_model()` currently reloads MiniLM on every call, and
`get_retriever()` is called on every single graph invocation. Wrapping it in
`functools.lru_cache` makes testing noticeably faster.

```python
from functools import lru_cache

@lru_cache(maxsize=1)
def get_embedding_model():
    ...
```

Two lines, no behaviour change. Do this only after Steps 1–8 are verified.

---

## Acceptance test

**File:** `test_sessions.py` (project root, matching the existing test file
style — plain scripts, not pytest)

The script must:

1. Create session A ("Amazon", "SDE Intern") and session B ("TCS", "Analyst").
2. Index one PDF from `uploads/` into A and a *different* one into B.
3. Assert `list_indexed_documents(A)` shows only A's file.
4. Retrieve with a query in A and assert **every** returned chunk has
   `metadata["session_id"] == A`.
5. Index a second file into A and assert the first file is still retrievable
   (proves the `clear_index` bug is fixed).
6. Call `clear_session_index(A)` and assert B still returns results.

Print a clear PASS / FAIL line for each assertion.

**M0 is complete when this script passes and the browser loop in Step 8 works.**
