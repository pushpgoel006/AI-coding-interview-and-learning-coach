from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOADS_DIR = PROJECT_ROOT / "uploads"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
CHROMA_COLLECTION = "langchain"
