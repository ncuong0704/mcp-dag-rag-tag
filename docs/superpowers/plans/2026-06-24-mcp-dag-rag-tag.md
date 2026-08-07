# MCP DAG/RAG/TAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Xây dựng chatbot doanh nghiệp với 4 workflow N8N (DAG, RAG, TAG, Master Router) chạy trên Docker Windows, kết hợp PostgreSQL và Python FastAPI.

**Architecture:** N8N orchestration gọi Groq LLM; DAG query PostgreSQL qua SQL sinh tự động; RAG retrieve FAISS qua Python API; TAG gọi python_executor, web_search, sql_query. Master Router phân loại query tiếng Việt.

**Tech Stack:** Docker Compose, N8N, PostgreSQL 16, FastAPI, FAISS, Groq API, Hugging Face Inference API, PyMuPDF

**Spec:** `docs/superpowers/specs/2026-06-24-mcp-dag-rag-tag-design.md`

---

## File map

| File | Trách nhiệm |
|------|-------------|
| `docker-compose.yml` | 3 services: n8n, postgres, api |
| `.env.example` | Template API keys |
| `data/init.sql` | Schema + seed data tiếng Việt |
| `data/schema_registry.json` | Mô tả DB cho LLM |
| `data/documents/*.pdf` | 3 PDF RAG |
| `api/main.py` | FastAPI routes |
| `api/rag/ingest.py` | PDF chunk + embed + FAISS |
| `api/rag/retrieve.py` | Vector search |
| `api/tools/python_sandbox.py` | Safe Python executor |
| `api/tools/web_search.py` | DuckDuckGo search |
| `n8n/workflows/*.json` | 4 workflow export |
| `docs/bao-cao.md` | Báo cáo nộp bài |
| `docs/quiz-kiem-tra.md` | Quiz DAG/RAG/TAG |
| `README.md` | Hướng dẫn chạy |

---

### Task 1: Scaffold dự án và Docker Compose

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Tạo `.gitignore`**

```
.env
__pycache__/
*.pyc
.faiss_index/
n8n_data/
postgres_data/
.venv/
```

- [ ] **Step 2: Tạo `.env.example`**

```env
GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACE_API_KEY=your_hf_api_key_here
POSTGRES_USER=mcp_user
POSTGRES_PASSWORD=mcp_secret_2025
POSTGRES_DB=cong_ty_ban_le
N8N_HOST=localhost
N8N_PORT=5678
API_PORT=8000
```

- [ ] **Step 3: Tạo `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./data/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: ./api
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      GROQ_API_KEY: ${GROQ_API_KEY}
      HUGGINGFACE_API_KEY: ${HUGGINGFACE_API_KEY}
      HF_EMBED_MODEL: sentence-transformers/all-MiniLM-L6-v2
      FAISS_INDEX_PATH: /data/faiss_index
      DOCUMENTS_PATH: /data/documents
    volumes:
      - ./data/documents:/data/documents:ro
      - faiss_index:/data/faiss_index
    depends_on:
      postgres:
        condition: service_healthy

  n8n:
    image: n8nio/n8n
    ports:
      - "${N8N_PORT:-5678}:5678"
    environment:
      - N8N_HOST=${N8N_HOST}
      - WEBHOOK_URL=http://${N8N_HOST}:${N8N_PORT}/
      - GENERIC_TIMEZONE=Asia/Ho_Chi_Minh
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/workflows:/home/node/workflows:ro
      - ./data/schema_registry.json:/home/node/schema_registry.json:ro
    depends_on:
      - postgres
      - api

volumes:
  postgres_data:
  faiss_index:
  n8n_data:
```

- [ ] **Step 4: Copy `.env.example` → `.env` và điền API keys**

```powershell
Copy-Item .env.example .env
# Sửa .env: thêm GROQ_API_KEY và HUGGINGFACE_API_KEY thật
```

- [ ] **Step 5: Verify cấu trúc thư mục**

```powershell
New-Item -ItemType Directory -Force -Path data/documents, n8n/workflows, api/rag, api/tools
```

---

### Task 2: PostgreSQL schema và seed data

**Files:**
- Create: `data/init.sql`

- [ ] **Step 1: Viết `data/init.sql`**

Tạo 5 bảng + seed ~100 đơn hàng năm 2025 với doanh thu phân bổ Q1–Q4. Đảm bảo có khách hàng ở Hà Nội, TP.HCM; sản phẩm đủ để có top 5 bán chạy.

Cấu trúc cốt lõi:

```sql
CREATE TABLE san_pham (
  ma_sp SERIAL PRIMARY KEY,
  ten_sp VARCHAR(200) NOT NULL,
  danh_muc VARCHAR(100),
  gia_ban NUMERIC(12,2)
);

CREATE TABLE khach_hang (
  ma_kh SERIAL PRIMARY KEY,
  ten_kh VARCHAR(200) NOT NULL,
  thanh_pho VARCHAR(100),
  loai_kh VARCHAR(50)
);

CREATE TABLE nhan_vien (
  ma_nv SERIAL PRIMARY KEY,
  ten_nv VARCHAR(200),
  phong_ban VARCHAR(100)
);

CREATE TABLE don_hang (
  ma_dh SERIAL PRIMARY KEY,
  ma_kh INT REFERENCES khach_hang(ma_kh),
  ma_nv INT REFERENCES nhan_vien(ma_nv),
  ngay_dat DATE NOT NULL,
  trang_thai VARCHAR(50) DEFAULT 'Đã giao'
);

CREATE TABLE chi_tiet_don_hang (
  id SERIAL PRIMARY KEY,
  ma_dh INT REFERENCES don_hang(ma_dh),
  ma_sp INT REFERENCES san_pham(ma_sp),
  so_luong INT NOT NULL,
  don_gia NUMERIC(12,2) NOT NULL
);
```

Seed: INSERT 20 sản phẩm, 30 khách hàng (10 Hà Nội), 5 nhân viên, 120 đơn hàng từ 2025-01-01 đến 2025-12-31.

- [ ] **Step 2: Verify seed — doanh thu Q1 có số cố định**

```powershell
docker compose up -d postgres
docker compose exec postgres psql -U mcp_user -d cong_ty_ban_le -c "
SELECT SUM(ct.so_luong * ct.don_gia) AS doanh_thu_q1
FROM chi_tiet_don_hang ct
JOIN don_hang dh ON ct.ma_dh = dh.ma_dh
WHERE dh.ngay_dat BETWEEN '2025-01-01' AND '2025-03-31';
"
```

Expected: một số cố định (ghi vào README để test DAG).

---

### Task 3: Schema registry cho DAG

**Files:**
- Create: `data/schema_registry.json`

- [ ] **Step 1: Tạo `data/schema_registry.json`**

```json
{
  "database": "cong_ty_ban_le",
  "description": "Hệ thống quản lý bán hàng doanh nghiệp Việt Nam",
  "tables": {
    "san_pham": {
      "description": "Danh mục sản phẩm",
      "columns": {
        "ma_sp": "Mã sản phẩm (INTEGER, PK)",
        "ten_sp": "Tên sản phẩm",
        "danh_muc": "Danh mục: Điện tử, Thực phẩm, Gia dụng...",
        "gia_ban": "Giá bán (NUMERIC)"
      }
    },
    "khach_hang": {
      "description": "Thông tin khách hàng",
      "columns": {
        "ma_kh": "Mã khách hàng (INTEGER, PK)",
        "ten_kh": "Tên khách hàng",
        "thanh_pho": "Thành phố: Hà Nội, TP.HCM, Đà Nẵng...",
        "loai_kh": "Loại: Cá nhân, Doanh nghiệp"
      }
    },
    "don_hang": {
      "description": "Đơn hàng",
      "columns": {
        "ma_dh": "Mã đơn hàng (INTEGER, PK)",
        "ma_kh": "FK → khach_hang.ma_kh",
        "ma_nv": "FK → nhan_vien.ma_nv",
        "ngay_dat": "Ngày đặt (DATE)",
        "trang_thai": "Đã giao | Đang xử lý | Hủy"
      }
    },
    "chi_tiet_don_hang": {
      "description": "Chi tiết từng dòng trong đơn hàng",
      "columns": {
        "ma_dh": "FK → don_hang.ma_dh",
        "ma_sp": "FK → san_pham.ma_sp",
        "so_luong": "Số lượng",
        "don_gia": "Đơn giá tại thời điểm bán"
      }
    },
    "nhan_vien": {
      "description": "Nhân viên bán hàng",
      "columns": {
        "ma_nv": "Mã nhân viên (INTEGER, PK)",
        "ten_nv": "Tên nhân viên",
        "phong_ban": "Phòng ban"
      }
    }
  },
  "notes": [
    "Doanh thu = SUM(chi_tiet_don_hang.so_luong * chi_tiet_don_hang.don_gia)",
    "Quý 1 = tháng 1-3, Quý 2 = 4-6, Quý 3 = 7-9, Quý 4 = 10-12",
    "Chỉ dùng SELECT, không JOIN thừa bảng"
  ]
}
```

---

### Task 4: Python API — scaffold và health check

**Files:**
- Create: `api/Dockerfile`
- Create: `api/requirements.txt`
- Create: `api/main.py`

- [ ] **Step 1: Tạo `api/requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
httpx==0.28.1
faiss-cpu==1.9.0.post1
numpy==2.2.1
pymupdf==1.25.2
pydantic==2.10.4
duckduckgo-search==7.2.1
```

- [ ] **Step 2: Tạo `api/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Tạo `api/main.py` skeleton**

```python
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="MCP API", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    groq_configured: bool
    hf_configured: bool
    faiss_ready: bool

@app.get("/health", response_model=HealthResponse)
def health():
    from rag.retrieve import index_exists
    return HealthResponse(
        status="ok",
        groq_configured=bool(os.getenv("GROQ_API_KEY")),
        hf_configured=bool(os.getenv("HUGGINGFACE_API_KEY")),
        faiss_ready=index_exists(),
    )
```

- [ ] **Step 4: Build và test health**

```powershell
docker compose build api
docker compose up -d api
curl http://localhost:8000/health
```

Expected: `{"status":"ok","groq_configured":true,"hf_configured":true,"faiss_ready":false}`

---

### Task 5: Python API — RAG (embed, ingest, retrieve)

**Files:**
- Create: `api/rag/embedder.py`
- Create: `api/rag/ingest.py`
- Create: `api/rag/retrieve.py`
- Modify: `api/main.py`

- [ ] **Step 1: Tạo `api/rag/embedder.py`**

```python
import os
import httpx

HF_MODEL = os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
HF_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL}"

async def embed_texts(texts: list[str]) -> list[list[float]]:
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        raise RuntimeError("HUGGINGFACE_API_KEY chưa cấu hình")
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(HF_URL, headers=headers, json={"inputs": texts})
        resp.raise_for_status()
        data = resp.json()
    # HF trả về nested list; lấy mean pooling nếu cần
    vectors = []
    for item in data:
        if isinstance(item[0], list):
            import numpy as np
            vectors.append(np.mean(item, axis=0).tolist())
        else:
            vectors.append(item)
    return vectors
```

- [ ] **Step 2: Tạo `api/rag/ingest.py`**

Chunk PDF bằng PyMuPDF, chunk size ~500 ký tự overlap 64, lưu FAISS + metadata JSON cạnh index.

```python
import json, os
import fitz  # pymupdf
import faiss
import numpy as np
from pathlib import Path
from rag.embedder import embed_texts
import asyncio

INDEX_DIR = Path(os.getenv("FAISS_INDEX_PATH", "/data/faiss_index"))
DOCS_DIR = Path(os.getenv("DOCUMENTS_PATH", "/data/documents"))

def chunk_text(text: str, size: int = 500, overlap: int = 64) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]

async def ingest_all() -> dict:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    all_chunks, metadata = [], []
    for pdf_path in DOCS_DIR.glob("*.pdf"):
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            for i, chunk in enumerate(chunk_text(text)):
                all_chunks.append(chunk)
                metadata.append({"file": pdf_path.name, "page": page_num, "chunk_id": i})
    if not all_chunks:
        return {"chunks": 0}
    vectors = await embed_texts(all_chunks)
    dim = len(vectors[0])
    index = faiss.IndexFlatIP(dim)
    matrix = np.array(vectors, dtype="float32")
    faiss.normalize_L2(matrix)
    index.add(matrix)
    faiss.write_index(index, str(INDEX_DIR / "index.faiss"))
    (INDEX_DIR / "metadata.json").write_text(json.dumps({"chunks": all_chunks, "metadata": metadata}, ensure_ascii=False), encoding="utf-8")
    return {"chunks": len(all_chunks), "files": list({m["file"] for m in metadata})}
```

- [ ] **Step 3: Tạo `api/rag/retrieve.py`**

```python
import json, os
import faiss
import numpy as np
from pathlib import Path
from rag.embedder import embed_texts
import asyncio

INDEX_DIR = Path(os.getenv("FAISS_INDEX_PATH", "/data/faiss_index"))

def index_exists() -> bool:
    return (INDEX_DIR / "index.faiss").exists() and (INDEX_DIR / "metadata.json").exists()

async def retrieve(query: str, top_k: int = 5) -> list[dict]:
    if not index_exists():
        return []
    index = faiss.read_index(str(INDEX_DIR / "index.faiss"))
    meta = json.loads((INDEX_DIR / "metadata.json").read_text(encoding="utf-8"))
    qvec = np.array(await embed_texts([query]), dtype="float32")
    faiss.normalize_L2(qvec)
    scores, indices = index.search(qvec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        results.append({
            "text": meta["chunks"][idx],
            "file": meta["metadata"][idx]["file"],
            "page": meta["metadata"][idx]["page"],
            "score": float(score),
        })
    return results
```

- [ ] **Step 4: Thêm routes vào `api/main.py`**

```python
class IngestResponse(BaseModel):
    chunks: int
    files: list[str] = []

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/ingest", response_model=IngestResponse)
async def ingest():
    from rag.ingest import ingest_all
    result = await ingest_all()
    return IngestResponse(chunks=result["chunks"], files=result.get("files", []))

@app.post("/retrieve")
async def retrieve_endpoint(req: RetrieveRequest):
    from rag.retrieve import retrieve
    results = await retrieve(req.query, req.top_k)
    if not results:
        raise HTTPException(404, "Chưa ingest tài liệu hoặc không tìm thấy")
    return {"results": results}
```

- [ ] **Step 5: Test ingest sau khi có PDF (Task 7)**

```powershell
curl -X POST http://localhost:8000/ingest
curl -X POST http://localhost:8000/retrieve -H "Content-Type: application/json" -d "{\"query\":\"thanh toán\",\"top_k\":3}"
```

---

### Task 6: Python API — TAG tools

**Files:**
- Create: `api/tools/python_sandbox.py`
- Create: `api/tools/web_search.py`
- Modify: `api/main.py`

- [ ] **Step 1: Tạo `api/tools/python_sandbox.py`**

```python
import ast
import signal
from contextlib import contextmanager

FORBIDDEN_NAMES = {"os", "subprocess", "sys", "open", "eval", "exec", "__import__"}
ALLOWED_IMPORTS = {"math", "statistics", "json", "datetime"}

class TimeoutError_(Exception):
    pass

@contextmanager
def time_limit(seconds: int):
    def handler(signum, frame):
        raise TimeoutError_("Timeout")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def validate_code(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    raise ValueError(f"Import không cho phép: {alias.name}")
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] not in ALLOWED_IMPORTS:
                raise ValueError(f"Import không cho phép: {node.module}")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ValueError(f"Biến/hàm không cho phép: {node.id}")

def execute_python(code: str, timeout: int = 10) -> dict:
    validate_code(code)
    local_vars = {}
    try:
        with time_limit(timeout):
            exec(compile(code, "<sandbox>", "exec"), {"__builtins__": {}}, local_vars)
        result = local_vars.get("result", local_vars.get("ket_qua", None))
        return {"success": True, "result": result, "stdout": str(result)}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

> **Windows note:** `signal.SIGALRM` không có trên Windows. Khi chạy trong Docker (Linux container) thì OK. Nếu test local Windows, dùng `threading` timeout thay thế.

- [ ] **Step 2: Tạo `api/tools/web_search.py`**

```python
from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = 5) -> list[dict]:
    with DDGS() as ddgs:
        results = list(ddgs.text(query, region="vi-vn", max_results=max_results))
    return [{"title": r.get("title"), "snippet": r.get("body"), "url": r.get("href")} for r in results]
```

- [ ] **Step 3: Thêm routes**

```python
class PythonRequest(BaseModel):
    code: str

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5

@app.post("/execute-python")
def execute_python_endpoint(req: PythonRequest):
    from tools.python_sandbox import execute_python
    return execute_python(req.code)

@app.post("/web-search")
def web_search_endpoint(req: WebSearchRequest):
    from tools.web_search import web_search
    return {"snippets": web_search(req.query, req.max_results)}
```

- [ ] **Step 4: Test tools**

```powershell
curl -X POST http://localhost:8000/execute-python -H "Content-Type: application/json" -d "{\"code\":\"result = (120+150+180)/3\"}"
curl -X POST http://localhost:8000/web-search -H "Content-Type: application/json" -d "{\"query\":\"tỷ giá USD VND\"}"
```

---

### Task 7: Tạo PDF tài liệu mẫu

**Files:**
- Create: `scripts/generate_pdfs.py`
- Create: `data/documents/hop-dong-mau.pdf`
- Create: `data/documents/faq-noi-bo.pdf`
- Create: `data/documents/chinh-sach-ban-hang.pdf`

- [ ] **Step 1: Script tạo PDF bằng reportlab hoặc fpdf2**

```python
# scripts/generate_pdfs.py
from fpdf import FPDF
from pathlib import Path

OUT = Path("data/documents")
OUT.mkdir(parents=True, exist_ok=True)

def write_pdf(filename, title, sections: list[tuple[str, str]]):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", "api/fonts/DejaVuSans.ttf", uni=True)  # font Unicode
    pdf.set_font("DejaVu", size=14)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font("DejaVu", size=11)
    for heading, body in sections:
        pdf.cell(0, 8, heading, ln=True)
        pdf.multi_cell(0, 6, body)
        pdf.ln(2)
    pdf.output(str(OUT / filename))

write_pdf("hop-dong-mau.pdf", "HỢP ĐỒNG CUNG CẤP DỊCH VỤ", [
    ("Điều 5: Thanh toán", "Bên B thanh toán 50% giá trị hợp đồng trong vòng 7 ngày kể từ ngày ký. 50% còn lại thanh toán trong vòng 30 ngày sau nghiệm thu."),
    ("Điều 6: Bảo hành", "Thời gian bảo hành là 12 tháng kể từ ngày bàn giao."),
])
write_pdf("faq-noi-bo.pdf", "FAQ NỘI BỘ", [
    ("Nghỉ phép", "Nhân viên chính thức được 12 ngày phép năm. Ngày phép tăng thêm 1 ngày sau mỗi 5 năm thâm niên."),
    ("Đặt hàng", "Đơn hàng trên 20 triệu cần phê duyệt trưởng phòng."),
])
write_pdf("chinh-sach-ban-hang.pdf", "CHÍNH SÁCH BÁN HÀNG", [
    ("Chiết khấu", "Đơn hàng từ 50 triệu: chiết khấu 5%. Đơn hàng từ 80 triệu: chiết khấu 8%. Đơn hàng từ 100 triệu: chiết khấu 10%."),
    ("Đổi trả", "Sản phẩm lỗi được đổi trong 30 ngày."),
])
```

- [ ] **Step 2: Chạy script và ingest**

```powershell
pip install fpdf2
python scripts/generate_pdfs.py
docker compose restart api
curl -X POST http://localhost:8000/ingest
```

---

### Task 8: Workflow N8N — DAG (`wf-dag-sql`)

**Files:**
- Create: `n8n/workflows/wf-dag-sql.json` (export sau khi build trên UI)

- [ ] **Step 1: Khởi động N8N**

```powershell
docker compose up -d
# Mở http://localhost:5678 — tạo tài khoản admin lần đầu
```

- [ ] **Step 2: Cấu hình credentials trong N8N**

- **Groq API:** HTTP Header Auth hoặc OpenAI-compatible credential trỏ `https://api.groq.com/openai/v1`
- **PostgreSQL:** host `postgres`, port 5432, user/pass từ `.env`

- [ ] **Step 3: Build workflow trên N8N UI**

Nodes theo thứ tự:

1. **Webhook** — POST `/dag`, response mode `lastNode`
2. **Set** — `query` = `{{ $json.body.query }}`
3. **Read/Write File** hoặc **Code** — load `schema_registry.json`
4. **HTTP Request (Groq)** — chat completions:

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {"role": "system", "content": "Bạn là SQL generator. Chỉ trả về 1 câu SELECT PostgreSQL. Schema: {{ $json.schema }}"},
    {"role": "user", "content": "{{ $json.query }}"}
  ],
  "temperature": 0
}
```

5. **Code** — validate SQL (regex chặn DROP/DELETE/UPDATE/INSERT)
6. **Postgres** — Execute Query
7. **IF** — lỗi → loop Groq sửa (tối đa 2 lần)
8. **Code** — format Markdown table
9. **Respond to Webhook**

- [ ] **Step 4: Test DAG**

```powershell
curl -X POST http://localhost:5678/webhook/dag -H "Content-Type: application/json" -d "{\"query\":\"Doanh thu quý 1 năm 2025 là bao nhiêu?\"}"
```

- [ ] **Step 5: Export workflow** → `n8n/workflows/wf-dag-sql.json`

---

### Task 9: Workflow N8N — RAG (`wf-rag-docs`)

- [ ] **Step 1: Build workflow**

1. **Webhook** — POST `/rag`
2. **HTTP Request** — POST `http://api:8000/retrieve` body `{"query":"...", "top_k":5}`
3. **Code** — ghép context từ results
4. **HTTP Request (Groq)** — system prompt:

```
Chỉ trả lời dựa trên CONTEXT. Nếu không có thông tin, nói "Không tìm thấy trong tài liệu nội bộ".
Trích dẫn nguồn [file, trang].
CONTEXT:
{{ $json.context }}
```

5. **Respond to Webhook**

- [ ] **Step 2: Test**

```powershell
curl -X POST http://localhost:5678/webhook/rag -H "Content-Type: application/json" -d "{\"query\":\"Điều khoản hợp đồng về thanh toán là gì?\"}"
```

- [ ] **Step 3: Export** → `n8n/workflows/wf-rag-docs.json`

---

### Task 10: Workflow N8N — TAG (`wf-tag-tools`)

- [ ] **Step 1: Build workflow**

1. **Webhook** — POST `/tag`
2. **HTTP Request (Groq)** — function calling với 3 tools: `python_executor`, `web_search`, `sql_query`
3. **Switch** theo tool được chọn
   - `python_executor` → POST `http://api:8000/execute-python`
   - `web_search` → POST `http://api:8000/web-search`
   - `sql_query` → **Execute Workflow** wf-dag-sql
4. **HTTP Request (Groq)** — tổng hợp kết quả tiếng Việt
5. **Respond to Webhook**

Tool schemas cho Groq:

```json
[
  {"name": "python_executor", "description": "Chạy Python tính toán", "parameters": {"type":"object","properties":{"code":{"type":"string"}},"required":["code"]}},
  {"name": "web_search", "description": "Tìm kiếm web", "parameters": {"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}},
  {"name": "sql_query", "description": "Truy vấn database", "parameters": {"type":"object","properties":{"question":{"type":"string"}},"required":["question"]}}
]
```

- [ ] **Step 2: Test 3 query TAG**
- [ ] **Step 3: Export** → `n8n/workflows/wf-tag-tools.json`

---

### Task 11: Workflow N8N — Master Router (`wf-master-router`)

- [ ] **Step 1: Build workflow**

1. **Webhook** — POST `/chat`
2. **HTTP Request (Groq)** — classifier:

```
Phân loại query thành 1 trong: DAG, RAG, TAG, HYBRID.
DAG: câu hỏi về số liệu, doanh thu, khách hàng, sản phẩm
RAG: câu hỏi về chính sách, hợp đồng, quy trình nội bộ
TAG: tính toán, tra cứu web, công thức
HYBRID: cần cả tài liệu và số liệu/tính toán
Chỉ trả về 1 từ: DAG|RAG|TAG|HYBRID
```

3. **Switch** → Execute Workflow tương ứng
4. **HYBRID branch:** gọi RAG → TAG (python) tuần tự
5. **Respond to Webhook**

- [ ] **Step 2: Test query phức hợp**
- [ ] **Step 3: Export** → `n8n/workflows/wf-master-router.json`

---

### Task 12: Báo cáo và quiz

**Files:**
- Create: `docs/bao-cao.md`
- Create: `docs/quiz-kiem-tra.md`
- Create: `README.md`

- [ ] **Step 1: Viết `docs/bao-cao.md`**

Cấu trúc:
1. Giới thiệu MCP và so sánh DAG/RAG/TAG (bảng)
2. Sơ đồ kiến trúc (mermaid)
3. Mô tả 4 workflow + screenshot N8N
4. Demo 3+ query (input/output/độ chính xác)
5. 2 cải tiến: Hybrid Router + SQL guardrail
6. Kết luận

- [ ] **Step 2: Viết `docs/quiz-kiem-tra.md`**

10 câu hỏi trắc nghiệm về DAG/RAG/TAG + đáp án.

- [ ] **Step 3: Viết `README.md`**

Hướng dẫn: cài Docker Desktop, copy `.env`, `docker compose up -d`, import workflow, `curl /ingest`, test webhook.

---

### Task 13: Kiểm tra end-to-end

- [ ] **Step 1: Health check tất cả services**

```powershell
docker compose ps
curl http://localhost:8000/health
curl http://localhost:5678/healthz
```

- [ ] **Step 2: Chạy 3 query rubric qua Master Router**

```powershell
# DAG
curl -X POST http://localhost:5678/webhook/chat -d "{\"query\":\"Doanh thu quý 1 năm 2025 là bao nhiêu?\"}"
# RAG
curl -X POST http://localhost:5678/webhook/chat -d "{\"query\":\"Điều khoản thanh toán trong hợp đồng?\"}"
# TAG
curl -X POST http://localhost:5678/webhook/chat -d "{\"query\":\"Tính trung bình 120, 150, 180 triệu\"}"
```

- [ ] **Step 3: Ghi kết quả vào `docs/bao-cao.md`**

---

## Plan self-review

| Spec requirement | Task |
|------------------|------|
| DAG workflow | Task 8 |
| RAG workflow | Task 9 |
| TAG workflow | Task 10 |
| Master Router | Task 11 |
| 3 query >80% | Task 13 |
| Tiếng Việt | All prompts |
| 2 cải tiến | Task 11 (HYBRID) + Task 8 (SQL guardrail) |
| Báo cáo + quiz | Task 12 |
| Docker N8N self-host | Task 1 |
| Groq + HF API | Task 4–6 |

Không có placeholder TBD trong plan.
