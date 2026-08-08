
<p align="center">
  <a href="https://www.youtube.com/watch?v=7MIa2zYui7w">
    <img src="https://img.youtube.com/vi/7MIa2zYui7w/maxresdefault.jpg" alt="Xem demo trên YouTube" width="600">
  </a>
</p>

<p align="center">
  <strong>📺 <a href="https://www.youtube.com/watch?v=7MIa2zYui7w">Xem video demo trên YouTube</a></strong>
</p>

# MCP Final Project — Chatbot Doanh Nghiệp (DAG / RAG / TAG)

Dự án cuối khóa **Model Context Protocol (MCP)** xây dựng chatbot doanh nghiệp tổng hợp, kết hợp ba biến thể:

- **DAG** (Data-Augmented Generation) — truy vấn dữ liệu bán hàng qua SQL
- **RAG** (Retrieval-Augmented Generation) — hỏi đáp tài liệu nội bộ
- **TAG** (Tool-Augmented Generation) — gọi công cụ Python, tìm kiếm web, SQL

Hệ thống chạy trên **Docker Compose** với **N8N** (orchestration), **PostgreSQL** (dữ liệu), **FastAPI** (RAG + tools) và **Groq LLM**.

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản / Ghi chú |
|------------|---------------------|
| **Docker Desktop for Windows** | Bật WSL 2 backend (khuyến nghị) |
| **Python 3.10+** | Chỉ cần khi chạy script tạo PDF |
| Tài khoản **Groq** | API key miễn phí tại [console.groq.com](https://console.groq.com) |
| Tài khoản **Hugging Face** | API key cho embedding tại [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |

---

## Cài đặt nhanh

### Bước 1 — Cấu hình biến môi trường

Sao chép file mẫu và điền API key:

```powershell
copy .env.example .env
```

Mở `.env` và thay các giá trị placeholder:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxxxxx
POSTGRES_USER=mcp_user
POSTGRES_PASSWORD=mcp_secret_2025
POSTGRES_DB=cong_ty_ban_le
N8N_HOST=localhost
N8N_PORT=5678
API_PORT=8000
```

### Bước 2 — Khởi động Docker Compose

Tại thư mục gốc dự án:

```powershell
docker compose up -d --build
```

Chờ đến khi cả 3 service `postgres`, `api`, `n8n` đều healthy/running:

```powershell
docker compose ps
```

### Bước 3 — Tạo PDF tài liệu RAG (nếu thiếu)

Thư mục `data/documents/` cần 3 file PDF. Nếu chưa có, chạy:

```powershell
pip install pymupdf
python scripts/generate_pdfs.py
```

Script tạo:

- `hop-dong-mau.pdf` — điều khoản thanh toán, bảo hành
- `faq-noi-bo.pdf` — nghỉ phép, quy trình đặt hàng
- `chinh-sach-ban-hang.pdf` — chiết khấu, đổi trả

### Bước 4 — Ingest tài liệu vào FAISS

Chạy **một lần** sau khi API đã sẵn sàng:

```powershell
# PowerShell: curl là alias của Invoke-WebRequest — dùng một trong hai cách sau
Invoke-RestMethod -Method POST -Uri http://localhost:8000/ingest
# hoặc: curl.exe -X POST http://localhost:8000/ingest
```

Kết quả mong đợi: JSON chứa số `chunks` đã index và danh sách `files`.

Kiểm tra health:

```powershell
Invoke-RestMethod http://localhost:8000/health
# hoặc: curl.exe http://localhost:8000/health
```

Trường `faiss_ready` phải là `true`.

### Bước 5 — Import workflow N8N

1. Mở N8N UI: **http://localhost:5678**
2. Vào **Workflows** → **Import from File**
3. Import lần lượt 4 file trong `n8n/workflows/`:
   1. `wf-dag-sql.json`
   2. `wf-rag-docs.json`
   3. `wf-tag-tools.json`
   4. `wf-master-router.json`

### Bước 6 — Thiết lập Credentials

#### Groq API (Header Auth)

1. **Credentials** → **Add credential** → **Header Auth**
2. Tên gợi ý: `Groq API`
3. Cấu hình:
   - **Name:** `Authorization`
   - **Value:** `Bearer gsk_xxxxxxxx` (thay bằng Groq API key thật)
4. Gán credential cho tất cả node HTTP Request gọi Groq trong 4 workflow

#### Postgres MCP (PostgreSQL)

1. **Credentials** → **Add credential** → **Postgres**
2. Tên gợi ý: `Postgres MCP`
3. Cấu hình:

| Trường | Giá trị |
|--------|---------|
| Host | `postgres` |
| Database | `cong_ty_ban_le` |
| User | `mcp_user` |
| Password | `mcp_secret_2025` |
| Port | `5432` |
| SSL | Disable |

4. Gán credential cho node **Postgres Execute** trong `wf-dag-sql.json`

> **Lưu ý:** Trong Docker network, host PostgreSQL là `postgres`, **không** dùng `localhost`.

### Bước 7 — Kích hoạt workflow

**Activate** (bật) cả 4 workflow. Webhook chỉ hoạt động khi workflow đang active.

Thứ tự quan trọng: activate `wf-dag-sql`, `wf-rag-docs`, `wf-tag-tools` **trước** `wf-master-router` (router gọi webhook nội bộ của 3 workflow con).

---

## Kiểm tra hệ thống

### Webhook DAG — truy vấn SQL

```powershell
$body = @{ query = "Doanh thu quý 1 năm 2025 là bao nhiêu?" } | ConvertTo-Json
Invoke-RestMethod -Method POST `
  -Uri http://localhost:5678/webhook/dag `
  -ContentType "application/json" `
  -Body $body
```

**Kết quả mong đợi:** Doanh thu quý 1/2025 ≈ **525.186.000 VND** (tổng `so_luong × don_gia` các đơn tháng 1–3/2025, SQL do Groq tự sinh — đã kiểm thử thật).

Nếu gặp lỗi `The requested webhook "POST dag" is not registered`, hãy mở N8N và **Activate** workflow `wf-dag-sql` trước khi gọi production webhook.

### Webhook RAG — hỏi đáp tài liệu

```powershell
$body = @{ query = "Điều khoản hợp đồng về thanh toán là gì?" } | ConvertTo-Json
Invoke-RestMethod -Method POST `
  -Uri http://localhost:5678/webhook/rag `
  -ContentType "application/json" `
  -Body $body
```

**Kết quả mong đợi:** Trả lời về thanh toán 50% trong 7 ngày, 50% còn lại trong 30 ngày sau nghiệm thu; kèm trích dẫn nguồn `hop-dong-mau.pdf`.

### Webhook TAG — gọi công cụ

```powershell
$body = @{ query = "Tính trung bình cộng: 120, 150, 180 triệu" } | ConvertTo-Json
Invoke-RestMethod -Method POST `
  -Uri http://localhost:5678/webhook/tag `
  -ContentType "application/json" `
  -Body $body
```

**Kết quả mong đợi:** Groq chọn `python_executor`, kết quả trung bình **150 triệu VND**.

### Webhook Master Router — phân loại tự động

```powershell
$body = @{ query = "Top 5 sản phẩm bán chạy nhất?" } | ConvertTo-Json
Invoke-RestMethod -Method POST `
  -Uri http://localhost:5678/webhook/chat `
  -ContentType "application/json" `
  -Body $body
```

**Kết quả mong đợi:** Router phân loại `DAG`, trả về bảng Markdown top 5 sản phẩm theo tổng số lượng bán.

---

## Cấu trúc dự án

```
├── docker-compose.yml      # Postgres + API + N8N
├── .env.example            # Template biến môi trường
├── api/                    # FastAPI: RAG ingest/retrieve, Python sandbox, web search
├── data/
│   ├── init.sql            # Schema + seed data PostgreSQL
│   ├── schema_registry.json
│   └── documents/          # PDF cho RAG
├── n8n/workflows/          # 4 workflow JSON export
├── scripts/generate_pdfs.py  # Tạo PDF mẫu
└── docs/
    ├── bao-cao.md          # Báo cáo đầy đủ
    └── quiz-kiem-tra.md    # Quiz kiểm tra
```

---

## Xử lý sự cố

| Triệu chứng | Nguyên nhân | Cách xử lý |
|-------------|-------------|------------|
| Webhook 404 | Workflow chưa activate | Bật workflow trong N8N |
| Groq 401 | Credential sai / chưa gán | Kiểm tra Header Auth Bearer |
| Postgres connection refused | Sai host | Dùng `postgres` trong credential N8N |
| RAG 404 / không có kết quả | Chưa ingest | `POST http://localhost:8000/ingest` |
| `docker pull` 401 Unauthorized | Credential Docker Hub **hết hạn/sai** trong credsStore | Chạy `docker logout` rồi `docker compose up -d --build` (pull ẩn danh). Hoặc `docker login` lại với tài khoản mới |
| FAISS lỗi ghi file trên Windows | Đường dẫn có ký tự Unicode | Để trống `FAISS_INDEX_PATH` — hệ thống dùng `%TEMP%\mcp_faiss_index` |
| Embedding HF timeout | Mạng chặn huggingface.co | Đặt `EMBED_PROVIDER=local` (mặc định trong docker-compose) |
| `faiss_ready: false` | Chưa ingest | `POST http://localhost:8000/ingest` sau khi có PDF |
| Bind for 0.0.0.0:5432 failed | Cổng 5432 đã bị container/process khác chiếm (vd. `rag_postgres`) | Dự án dùng `POSTGRES_HOST_PORT=5433` — truy cập từ máy host qua port **5433**. Trong Docker/N8N vẫn dùng host `postgres`, port **5432** |

---

## Tài liệu tham khảo

- [Báo cáo đầy đủ](docs/bao-cao.md) — lý thuyết, kiến trúc, demo, tối ưu hóa
- [Quiz kiểm tra](docs/quiz-kiem-tra.md) — 10 câu hỏi trắc nghiệm DAG/RAG/TAG
- [Hướng dẫn workflow N8N](n8n/workflows/README.md) — chi tiết import và credential
