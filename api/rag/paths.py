import os
import platform
import tempfile
from pathlib import Path


def get_index_dir() -> Path:
    configured = os.getenv("FAISS_INDEX_PATH", "").strip()
    if configured:
        return Path(configured)
    if platform.system() == "Windows":
        return Path(tempfile.gettempdir()) / "mcp_faiss_index"
    return Path("/data/faiss_index")


def get_documents_dir() -> Path:
    configured = os.getenv("DOCUMENTS_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent.parent.parent / "data" / "documents"
