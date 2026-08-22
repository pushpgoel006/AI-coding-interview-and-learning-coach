"""Filesystem and Chroma configuration shared by RAG modules."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOADS_DIR = PROJECT_ROOT / "uploads"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
# Keep the existing LangChain default collection so pre-existing indexes remain
# available after adopting the packaged Streamlit entry point.
CHROMA_COLLECTION = "langchain"
