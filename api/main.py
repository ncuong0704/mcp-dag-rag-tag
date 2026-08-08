import os

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(title="MCP API", version="1.0.0")

N8N_URL = os.getenv("N8N_URL", "http://n8n:5678")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class ChatRequest(BaseModel):
    query: str


class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    hf_configured: bool
    faiss_ready: bool


class IngestResponse(BaseModel):
    chunks: int
    files: list[str] = Field(default_factory=list)


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1)


class PythonRequest(BaseModel):
    code: str


class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    from rag.retrieve import index_exists

    return HealthResponse(
        status="ok",
        groq_configured=bool(os.getenv("GROQ_API_KEY")),
        hf_configured=bool(os.getenv("HUGGINGFACE_API_KEY")),
        faiss_ready=index_exists(),
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest() -> IngestResponse:
    from rag.ingest import ingest_all

    result = await ingest_all()
    return IngestResponse(chunks=result["chunks"], files=result.get("files", []))


@app.post("/embed")
async def embed_endpoint(req: EmbedRequest) -> dict:
    from rag.embedder import embed_texts

    vectors = await embed_texts(req.texts)
    return {"embeddings": vectors, "count": len(vectors)}


@app.post("/retrieve")
async def retrieve_endpoint(req: RetrieveRequest) -> dict:
    from rag.retrieve import retrieve

    results = await retrieve(req.query, req.top_k)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="Chưa ingest tài liệu hoặc không tìm thấy kết quả phù hợp",
        )
    return {"results": results}


@app.post("/execute-python")
def execute_python_endpoint(req: PythonRequest) -> dict:
    from tools.python_sandbox import SandboxError, execute_python

    try:
        return execute_python(req.code)
    except SandboxError as exc:
        return {"success": False, "error": str(exc)}


@app.post("/web-search")
def web_search_endpoint(req: WebSearchRequest) -> dict:
    from tools.web_search import web_search

    return {"snippets": web_search(req.query, req.max_results)}


@app.get("/", response_class=HTMLResponse)
def chat_ui() -> FileResponse:
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/chat")
async def chat_endpoint(req: ChatRequest) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(f"{N8N_URL}/webhook/chat", json={"query": req.query})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Lỗi gọi N8N: {exc}") from exc
