# M7 — Deployment (implementation brief)

> **How to use this file.** Unlike M0-M6, several steps here are things
> **you** do outside this codebase (create an account, copy a connection
> string) before the matching code step can be written or tested. Steps are
> marked accordingly. Still one step at a time -- stop after each, report,
> wait for "continue."
>
> **Prerequisite:** M0-M4 complete (M6 is not required for deployment
> itself, though it's nearly done). **M5 (DSA) is not required** -- it was
> never built and stays out of scope here too.

---

## 1. Goal

The app runs somewhere that isn't your laptop, and its data survives a
restart. Two things move to the cloud; one stays local:

| Concern | Local now | Deployed | Decision |
|---|---|---|---|
| Vector store | Local Chroma folder | **Chroma Cloud** | Same client library already in the code -- smallest, lowest-risk swap |
| Database | `interviews.db` (SQLite file) | **Neon** (hosted Postgres) | Plain Postgres, nothing extra -- SQLAlchemy just needs a new connection string |
| Embeddings | Local MiniLM | **Stays local** | Switching would change the vector dimension and force re-indexing all 3 real sessions' documents -- not worth it right now |

## 2. Non-goals

- M5 (DSA round) -- still not built, still not required.
- Switching embeddings to a hosted API -- explicitly decided against, to
  avoid re-indexing real data.
- Any change to the AI logic in `agents/`, `graphs/`, `prompts/`,
  `rag/generator.py`, `rag/grader.py`, `rag/citations.py`. This brief only
  touches *where data lives*, never *what the app does with it*.
- Any change to `main.py`'s endpoints or behavior beyond how it reads
  secrets/connection strings. It keeps working exactly as it does today,
  same as every other module respected it.
- Rewriting `services/`, `ui/` business logic. Nothing here should need to
  change beyond config/connection plumbing.

---

## 3. Four gotchas to get right

### 3.1 Local dev must keep working with zero cloud accounts

Everything in this brief is **additive and gated**. If no cloud env vars
are set, the app must behave exactly as it does today: local SQLite,
local Chroma folder. This is the same principle every prior module
followed for `main.py` -- old behavior is a fallback, never removed.

### 3.2 Secrets never get committed, and never get logged

`.env` stays gitignored (already true). Streamlit Community Cloud's own
secrets file (`secrets.toml`, or entered via its dashboard) is never
written into this repo either. When wiring up connection strings, never
`print()` or log a raw secret value, even for debugging -- a stray print
statement is how these end up in a terminal scrollback or, worse, a
screenshot.

### 3.3 `main.py` cannot read `st.secrets` -- it isn't a Streamlit process

`st.secrets` only exists inside a running Streamlit app. `main.py` (FastAPI)
and every `test_*.py` script need secrets a different way -- `os.getenv` /
`.env`, exactly as today. Whatever reads the database URL / Chroma
credentials needs to work in **both** contexts. Do not write something that
only works inside Streamlit.

### 3.4 Postgres needs a driver dependency that isn't installed yet

SQLAlchemy talks to Postgres through a driver library (`psycopg`), which
this project has never needed until now. Forgetting to add it produces a
confusing `NoSuchModuleError` at connection time, not at install time.

---

## Step 1 — Create the Neon project *(you do this)*

Go to neon.tech, create a free project, and get its connection string
(`postgresql://...`). Put it in your local `.env` as `DATABASE_URL=...` --
never paste it into a file that gets committed. Tell me once you have it
(you don't need to paste the actual string into chat if you'd rather not --
just confirm it's in `.env` and I'll reference the variable name, never the
value).

**Done when:** you have a working Neon connection string sitting in your
local `.env`.

---

## Step 2 — Make the database connection configurable

**File:** `database/db.py`

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./interviews.db")
```

Add `psycopg[binary]` (or `psycopg2-binary`) to `pyproject.toml`'s
dependencies -- this is the actual Postgres driver, separate from
`sqlalchemy` itself (gotcha 3.4).

**Done when:** with no `DATABASE_URL` set, the app behaves exactly as
today (gotcha 3.1). With `DATABASE_URL` pointing at Neon, `init_db.py`
creates all 5 tables in the Neon database instead.

---

## Step 3 — Create the Chroma Cloud database *(you do this)*

Go to trychroma.com's cloud offering, create a database, and get its
`tenant`, `database` name, and `api_key`. Add these to your local `.env` as
`CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE`.

**Done when:** you have these three values in your local `.env`.

---

## Step 4 — Make the vector store configurable

**File:** `rag/vector_store.py` (and wherever else a `Chroma(...)` client
gets constructed, e.g. `rag/retriever.py`'s `load_vector_store`)

If `CHROMA_API_KEY` is set, connect via `chromadb.CloudClient(tenant=...,
database=..., api_key=...)` and pass it as `Chroma(client=..., ...)`.
Otherwise, keep today's local `PersistentClient`-backed path unchanged
(gotcha 3.1).

**Done when:** with no Chroma Cloud env vars set, indexing/retrieval work
exactly as today, against the local `chroma_db/` folder. With them set,
the same code indexes into and retrieves from Chroma Cloud instead.

---

## Step 5 — Secrets that work in both Streamlit and plain Python

**File:** `models/llm_provider.py` already does `load_dotenv()` +
`os.getenv`. Add a small helper (a new tiny module, e.g.
`config/secrets.py`) that:

- If `st` is importable **and** running inside an active Streamlit session
  **and** the key exists in `st.secrets`, use that.
- Otherwise, fall back to `os.getenv` (which already covers `.env` via
  `load_dotenv()`).

Use this helper everywhere a secret is read (`DATABASE_URL`, `CHROMA_*`,
`GROQ_API_KEY`) so the same code path works for `ui/app.py` (Streamlit),
`main.py` (FastAPI), and every `test_*.py` script (gotcha 3.3).

**Done when:** the same secret-reading call returns the right value whether
it's sourced from `.env` or from Streamlit secrets.

---

## Step 6 — Cache expensive resources

**File:** `rag/embeddings.py` (already has `@lru_cache` from M0 Step 9 --
this step is about the Streamlit-specific caching layer, not a duplicate).

Wrap the vector store getter (`load_vector_store` in `rag/retriever.py`) in
`@st.cache_resource` so a Streamlit rerun doesn't reconnect to Chroma Cloud
or re-open a Postgres connection pool on every interaction.

**Done when:** repeated Streamlit interactions in one session reuse the
same cached vector store connection (verify via a debug log line that only
prints on first connection, not every rerun).

---

## Step 7 — `requirements.txt` for Streamlit Community Cloud

**File:** `requirements.txt` (new, alongside `pyproject.toml` -- both exist,
per the master spec; Streamlit Community Cloud reads `requirements.txt`
most reliably)

Generate it from the current `pyproject.toml` dependencies (including the
new `psycopg` driver from Step 2).

**Done when:** a fresh virtual environment created from just
`requirements.txt` can run `streamlit run app.py` successfully.

---

## Step 8 — Deploy *(you do this, with me guiding)*

On share.streamlit.io: connect your GitHub repo (already pushed), point it
at `app.py`, and enter `DATABASE_URL`, `CHROMA_API_KEY`, `CHROMA_TENANT`,
`CHROMA_DATABASE`, `GROQ_API_KEY` in its secrets manager (never in a
committed file -- gotcha 3.2).

**Done when:** the app is live at a public `*.streamlit.app` URL.

---

## Step 9 — Post-deploy smoke test

Against the **live deployed app**: create a prep session, upload a PDF,
process it, ask a chat question, run a resume check, run a theory round.
Then, separately, confirm **local** `streamlit run app.py` (with no cloud
env vars set) still works exactly as before (gotcha 3.1 -- this is the
regression check for this entire module).

**M7 is complete when the live app works end-to-end against real cloud
infrastructure, and local development still works with zero cloud accounts
configured.**
