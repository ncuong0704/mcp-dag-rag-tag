import asyncio
import os
from functools import lru_cache

import httpx
import numpy as np

HF_MODEL = os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
LOCAL_MODEL_NAME = os.getenv("LOCAL_EMBED_MODEL", HF_MODEL)


@lru_cache(maxsize=1)
def _get_local_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(LOCAL_MODEL_NAME)


def _embed_local(texts: list[str]) -> list[list[float]]:
    model = _get_local_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


def _pool_embedding(item) -> list[float]:
    if isinstance(item[0], list):
        return np.mean(item, axis=0).tolist()
    return item


async def _embed_hf(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY chưa cấu hình")

    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            HF_URL,
            headers=headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
        )
        response.raise_for_status()
        data = response.json()

    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(data["error"])

    if len(texts) == 1 and isinstance(data, list) and data and isinstance(data[0], (int, float)):
        return [data]

    return [_pool_embedding(item) for item in data]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    provider = os.getenv("EMBED_PROVIDER", "local").lower()
    if provider == "huggingface":
        try:
            return await _embed_hf(texts)
        except Exception:
            pass

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _embed_local, texts)
