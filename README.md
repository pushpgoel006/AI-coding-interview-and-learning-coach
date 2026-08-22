## AI Interview Intelligence Platform

The RAG interface has a thin Streamlit presentation layer and a backend-owned
indexing API. Start the Streamlit app from the project root:

```powershell
streamlit run app.py
```

`app.py` is only the Streamlit entry point. The UI components live in `ui/` and
call two backend boundaries:

- `rag.indexer.index_documents(paths)` runs the existing load → split → embed
  → Chroma pipeline.
- `graphs.rag_graph.rag_graph.invoke({"question": question})` answers chat
  questions through the existing retrieve → grade → generate graph.

The Chroma database and uploads directory are resolved from the project root,
so the application does not depend on the current working directory.
