import json

import faiss
import numpy as np

from rag.embedder import embed_texts
from rag.paths import get_index_dir


def index_exists() -> bool:
    index_dir = get_index_dir()
    return (index_dir / "index.faiss").exists() and (index_dir / "metadata.json").exists()


async def retrieve(query: str, top_k: int = 5) -> list[dict]:
    if not index_exists():
        return []

    index_dir = get_index_dir()
    index = faiss.read_index(str(index_dir / "index.faiss"))
    meta = json.loads((index_dir / "metadata.json").read_text(encoding="utf-8"))

    query_vec = np.array(await embed_texts([query]), dtype="float32")
    faiss.normalize_L2(query_vec)

    scores, indices = index.search(query_vec, top_k)
    results: list[dict] = []

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        results.append(
            {
                "text": meta["chunks"][idx],
                "file": meta["metadata"][idx]["file"],
                "page": meta["metadata"][idx]["page"],
                "score": float(score),
            }
        )

    return results
