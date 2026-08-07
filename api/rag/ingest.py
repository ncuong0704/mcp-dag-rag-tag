import json

import faiss
import fitz
import numpy as np

from rag.embedder import embed_texts
from rag.paths import get_documents_dir, get_index_dir


def chunk_text(text: str, size: int = 500, overlap: int = 64) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks


async def ingest_all() -> dict:
    index_dir = get_index_dir()
    docs_dir = get_documents_dir()
    index_dir.mkdir(parents=True, exist_ok=True)

    all_chunks: list[str] = []
    metadata: list[dict] = []

    for pdf_path in sorted(docs_dir.glob("*.pdf")):
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            for chunk_id, chunk in enumerate(chunk_text(text)):
                all_chunks.append(chunk)
                metadata.append(
                    {"file": pdf_path.name, "page": page_num, "chunk_id": chunk_id}
                )
        doc.close()

    if not all_chunks:
        return {"chunks": 0, "files": []}

    vectors = await embed_texts(all_chunks)
    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)

    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    faiss.write_index(index, str(index_dir / "index.faiss"))

    payload = {"chunks": all_chunks, "metadata": metadata}
    (index_dir / "metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "chunks": len(all_chunks),
        "files": sorted({m["file"] for m in metadata}),
    }
