# M1 — Document Q&A upgrade (implementation brief)

> **How to use this file.** Implement it **one step at a time, in order**.
> After each step, stop and report what changed so it can be reviewed before
> continuing. Do not implement several steps in one go. Do not refactor
> anything this brief does not name.
>
> **Prerequisite: M0 must be complete and its acceptance test passing.**
> Every step here assumes `session_id` already flows through the retriever,
> the indexer and the graph.

---

## 1. Goal

Turn the working chat into something a user can *trust and reason with*.

Three things change:

1. **Every answer shows where it came from** — file name and page.
2. **Comparison and capability questions get real answers** instead of a blanket
   "I couldn't find that information."
3. **Relevance is judged per chunk, not all-or-nothing** — one irrelevant chunk
   can no longer sink an otherwise good retrieval.

### Why each one matters

**Citations.** This is a preparation tool. A wrong answer, delivered
confidently, costs the user an interview. "Which file and page did this come
from" is the difference between a demo and something a person will rely on. It
is also the cheapest credibility feature in the whole project.

**The refusal rule.** `RAG_PROMPT` currently says: if the answer is not present
in the context, reply *exactly* `"I couldn't find that information in the
uploaded documents."` For the project's own headline test case — pasting a list
of Data Analyst requirements and asking "is this candidate capable?" — none of
those requirements appear in the resume, so the prompt actively pushes the model
toward refusing. The resume does not need to contain the requirements. It only
needs to contain evidence about the candidate.

**Per-chunk grading.** Today `grade_documents()` joins every retrieved chunk
into one blob and asks the LLM one yes/no question about the whole batch. If
three chunks are useful and one is noise, a strict grader can answer "no" and
the user gets Not Found — a failure this project has already hit once. Grading
each chunk separately and keeping the ones that pass is the standard corrective
-RAG pattern, and it has a second benefit: **citations become honest**, because
you cite only the chunks that actually survived grading and reached the
generator.

## 2. Non-goals

Do **not** build these in M1.

- Query rewriting or query decomposition (later phases)
- Intent classification / routing to different prompts per question type —
  one improved prompt handles all cases in M1
- Grounding / hallucination checking of the final answer (M2 and M3)
- Resume analysis (M2), question generation or evaluation (M3)
- Conversation memory (M4)
- Any change to `agents/`, `main.py`, `graphs/interview_graph.py`
- Parallelising the grader calls — correctness first, speed later

---

## 3. Four gotchas to get right

### 3.1 PyMuPDF page numbers are zero-indexed

`document.metadata["page"]` is `0` for the first page. Displaying it raw shows
"Page 0", which looks broken. **Add 1 when displaying, never when storing.**

### 3.2 Cite what was used, not what was retrieved

After per-chunk grading, some chunks are discarded. Citations must be built
from the **kept** chunks only. Citing a discarded chunk is worse than no
citation — it points the user at a passage the answer never used.

### 3.3 The grader's output is not guaranteed to be clean

`response.content` may come back as `"Yes."`, `"yes\n"`, or with surrounding
whitespace. Normalise before comparing:

```python
verdict = response.content.strip().lower().startswith("yes")
```

Do not use `== "yes"`.

### 3.4 An empty retrieval must never reach the LLM

If the session has no indexed documents, the retriever returns `[]`. Today that
still runs a grader call and a generator call on an empty context, wasting two
API calls and producing confusing output. Guard it in the graph (Step 4) and
give the user a specific message: the problem is "you have not uploaded
anything to this session", not "I could not find that".

---

## Step 1 — Citation builder

**File:** `rag/citations.py` (new)

One small module, one job: turn a list of `Document` objects into a clean,
deduplicated list of sources the UI can render without knowing anything about
LangChain.

```python
build_sources(documents: list[Document]) -> list[dict]
```

Each returned dict:

```python
{"file_name": "Pushp_Goel_Resume.pdf", "page": 1, "doc_type": "resume"}
```

Requirements:

- Deduplicate on `(file_name, page)` — several chunks from the same page
  produce **one** entry.
- `page` is `metadata["page"] + 1` (gotcha 3.1).
- Fall back to `Path(metadata["source"]).name` if `file_name` is missing, and
  to `"unknown"` if both are.
- Sort by `file_name`, then `page`.
- An empty input returns an empty list — never `None`.

This lives in `rag/` and not in `ui/` because it is document logic, not
presentation. The UI receives plain dicts.

**Done when:** passing a handful of `Document` objects returns a sorted,
deduplicated list with 1-based page numbers.

---

## Step 2 — Rewrite the RAG prompt

**File:** `prompts/rag_prompts.py`

Replace `RAG_PROMPT` with the version below. This is the single most important
change in M1 — read it before pasting it, because the reasoning behind each
rule matters more than the text.

```python
RAG_PROMPT = PromptTemplate.from_template(
    """
You are an AI Interview Intelligence Assistant.

You answer using ONLY the provided context. The context comes from documents
the user uploaded - their resume, job descriptions, company material, or notes.

HOW TO ANSWER

The question may be one of several kinds:

1. A direct factual question.
   Example: "What programming languages does the candidate know?"
   Answer it from the context.

2. A comparison across documents.
   Example: "Which technologies in the job description also appear in the
   resume?"
   Compare what the context shows from each document.

3. A capability or evaluation question, where the criteria are stated in the
   QUESTION itself.
   Example: "Here are the job requirements ... is this candidate capable?"
   The context does NOT need to contain the requirements - they are already in
   the question. Work through the requirements one at a time and judge each
   against the evidence in the context. Label each one:

     - Clearly demonstrated  - the context contains direct evidence
     - Partially demonstrated - related evidence, but not a direct match
     - Not demonstrated       - no supporting evidence in the context

   Then give a short overall assessment.

RULES

- Use only the context. Never use outside knowledge to add facts about the
  candidate, the company, or the documents.
- Never invent qualifications, experience, projects or skills that are not in
  the context.
- Partial information is still an answer. If the context answers part of the
  question, answer that part and say plainly which part is not covered.
- Name the evidence you are relying on, so the user can check it.
- Only if the context is entirely unrelated to the question, reply with exactly
  this sentence and nothing else:
  "I couldn't find that information in the uploaded documents."

Context:
{context}

Question:
{question}

Answer:
"""
)
```

**What changed and why**

| Old rule | New rule | Reason |
|---|---|---|
| Refuse if the answer is not present | Refuse only if the context is *unrelated* | Capability questions have their criteria in the question, not the documents |
| No guidance on question types | Three named question types | The model needs to know a comparison is a legitimate answer shape |
| "Keep the answer concise" | "Name the evidence you rely on" | Makes the answer checkable, and pairs with citations |
| — | Explicit three-way labelling | The project's headline test case requires demonstrated / partial / not demonstrated |

**What did not change:** the prohibition on outside knowledge and on invented
qualifications. Loosening the refusal rule must not loosen those. A tool that
invents experience for a candidate is actively harmful.

**Done when:** the module imports and the template still formats with
`context` and `question`.

---

## Step 3 — Per-chunk grading

**File:** `rag/grader.py`

Add a new function alongside the existing one. **Do not delete
`grade_documents()`** — leave it in place so nothing that imports it breaks.

```python
grade_document(question: str, document: Document) -> bool
```

- Formats `GRADER_PROMPT` with the question and this **single** chunk's
  `page_content`.
- Returns a bool using the normalisation from gotcha 3.3.

```python
filter_relevant_documents(question, documents) -> tuple[list[Document], str]
```

- Calls `grade_document` for each chunk.
- Returns `(kept_documents, summary)` where `summary` is a short human-readable
  string for the debug trace, e.g. `"3/4 relevant"`.
- An empty input returns `([], "0/0 relevant")` **without calling the LLM**.

`prompts/doc_grader.py` needs **no change**. The existing prompt already asks
"is this context useful for answering, comparing, evaluating or reasoning about
the question" — which is exactly the right question to ask of a single chunk.

**Cost note.** This turns 1 LLM call into `k` calls per question (4 by default).
On Groq these are small and fast, so it is acceptable. Parallelising them is a
later optimisation, deliberately out of scope here.

**Done when:** given a question and a mixed list of chunks, only the relevant
ones come back, and the summary string reports the right counts.

---

## Step 4 — Graph changes

**File:** `graphs/rag_graph.py`

The graph stays an orchestrator. No business logic moves into it.

**State** gains two fields:

```python
class GraphState(TypedDict):
    question: str
    session_id: str
    documents: list[Document]           # everything retrieved
    relevant_documents: list[Document]  # what survived grading
    grade: str                          # summary string, for the debug trace
    sources: list[dict]                 # built from relevant_documents
    answer: str
```

Keeping `documents` and `relevant_documents` separate is deliberate. In the
backpack analogy: `retrieve` puts everything in, `grader` puts the filtered set
in beside it. You can then see both in the debug trace, which makes it obvious
whether a bad answer was a retrieval problem or a grading problem.

**Node changes**

- `retriever_node` — unchanged from M0 apart from also printing the count.
- `grader_node` — calls `filter_relevant_documents`, sets `relevant_documents`
  and `grade`. Prints the summary.
- `generate_node` — generates from `state["relevant_documents"]`, and sets
  `state["sources"] = build_sources(state["relevant_documents"])`.
- `not_found_node` — sets `state["sources"] = []` explicitly.

**Add a new node:** `no_documents_node`, which sets:

```
"No documents have been indexed in this prep session yet.
 Upload a PDF in the sidebar and press Process Documents."
```

and `sources = []`. This is gotcha 3.4 — a different problem deserves a
different message.

**Routing**

Add a conditional edge straight after `retrieve`:

```
retrieve
  ├── documents empty      -> no_documents  -> END
  └── otherwise            -> grader
```

and change the existing route after `grader` to test the filtered list rather
than a yes/no string:

```
grader
  ├── relevant_documents non-empty -> generate  -> END
  └── empty                        -> not_found -> END
```

Routing on the list rather than on a parsed string removes a whole class of
"the grader said 'Yes.' with a full stop" bugs.

**Done when:** all four terminal paths work — no documents, nothing relevant,
relevant, and normal answer — and the debug trace shows retrieved and kept
counts.

---

## Step 5 — Chat UI

**File:** `ui/chat.py`

**Sources display.** After rendering the answer, if `result["sources"]` is
non-empty, render a collapsed expander:

```
📎 Sources (2)
   Pushp_Goel_Resume.pdf · page 1 · resume
   Job_Description.pdf   · page 2 · jd
```

Use `st.expander(..., expanded=False)`. It must not push the answer down or
compete with it visually — it is supporting evidence, not the headline.

**Store sources in history.** `st.session_state.messages[session_id]` entries
become:

```python
{"role": "assistant", "content": answer, "sources": [...]}
```

so the expander still renders after a rerun. Use `message.get("sources", [])`
when replaying history — older entries will not have the key.

**Error handling.** Wrap the `rag_graph.invoke` call:

```python
try:
    result = rag_graph.invoke({...})
except Exception as error:
    st.error(f"Something went wrong answering that: {error}")
    return
```

Every LLM call can fail — rate limits, a dropped connection, a bad API key. The
user sees a clean message, never a Streamlit stack trace.

**Done when:** answers show a working sources expander, sources survive a
rerun, and killing the network produces a clean error instead of a traceback.

---

## Step 6 (optional) — Stream the answer

**File:** `ui/chat.py`, `rag/generator.py`

`llm.stream()` already works elsewhere in this project (`stream_question`).
Adding `st.write_stream` to the chat makes the wait feel much shorter.

This complicates the graph, because a compiled graph returns a final state
rather than a token stream. The simplest approach that does not fight LangGraph:
keep the graph for retrieve + grade, then stream the generation step directly in
the UI from the filtered documents.

**Only attempt this after Steps 1–5 are verified working.** It is polish, not
function, and it is fine to skip.

---

## Acceptance test

**File:** `test_citations.py` (project root, plain script like the existing
`test_*.py` files, not pytest)

Setup: create one prep session, index `uploads/Pushp_Goel_Resume.pdf` as
`doc_type="resume"` and a job description as `doc_type="jd"`.

Then assert:

1. **Factual question** — "What programming languages does Pushp know?"
   Answer is non-empty, is not the refusal sentence, and `sources` contains at
   least one entry whose `file_name` is the resume.

2. **Page numbers are 1-based** — no source in any result has `page == 0`.

3. **Capability question** — paste the six Data Analyst requirements from the
   project brief and ask "Is Pushp capable of this?"
   The answer must **not** be the refusal sentence, and must contain at least
   one of the labels `demonstrated` / `Partially` / `Not demonstrated`.
   *This is the test M1 exists to make pass.*

4. **Unrelated question** — "What is the capital of France?"
   The answer **is** the refusal sentence, and `sources` is empty.
   This proves the loosened prompt did not become a hallucination licence.

5. **Empty session** — a brand new session with nothing indexed.
   The answer is the "No documents have been indexed" message, and the debug
   trace shows the grader and generator were never called.

6. **Citations are honest** — every `file_name` in `sources` appears in
   `list_indexed_documents(session_id)` for that session.

Print a clear PASS / FAIL line per assertion.

**M1 is complete when this script passes and the sources expander works in the
browser.**
