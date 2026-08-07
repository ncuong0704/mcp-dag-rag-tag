# N8N Workflows — MCP DAG / RAG / TAG

Bộ 4 workflow orchestration cho chatbot doanh nghiệp: truy vấn SQL (DAG), hỏi đáp tài liệu (RAG), gọi tool (TAG), và router tổng (Master).

## Danh sách file

| File | Webhook | Mô tả |
|------|---------|-------|
| `wf-dag-sql.json` | `POST /webhook/dag` | Sinh SQL SELECT → PostgreSQL → bảng Markdown |
| `wf-rag-docs.json` | `POST /webhook/rag` | Retrieve FAISS qua API → Groq trả lời từ context |
| `wf-tag-tools.json` | `POST /webhook/tag` | Groq function calling → Python / Web / DAG |
| `wf-master-router.json` | `POST /webhook/chat` | Phân loại DAG/RAG/TAG/HYBRID → gọi workflow con |

## Yêu cầu môi trường

- Docker Compose đã chạy: `postgres`, `api`, `n8n`
- Host nội bộ Docker:
  - PostgreSQL: `postgres:5432`
  - Python API: `http://api:8000`
  - N8N (gọi webhook nội bộ): `http://n8n:5678`
- File schema mount sẵn: `/home/node/schema_registry.json` (từ `./data/schema_registry.json`)

Thêm biến môi trường cho container N8N trong `.env` / `docker-compose.yml`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

## Import workflow

1. Mở N8N UI: `http://localhost:5678`
2. **Workflows** → **Import from File**
3. Import lần lượt 4 file JSON (thứ tự đề xuất):
   1. `wf-dag-sql.json`
   2. `wf-rag-docs.json`
   3. `wf-tag-tools.json`
   4. `wf-master-router.json`
4. Sau khi import, mở từng workflow và **gán credential** (xem bên dưới)
5. **Activate** (bật) cả 4 workflow — webhook chỉ hoạt động khi workflow đang active

> **Lưu ý:** Workflow con (`dag`, `rag`, `tag`) phải được activate **trước** khi test `wf-master-router` hoặc `wf-tag-tools` (vì chúng gọi webhook nội bộ).

## Thiết lập Credentials

### 1. Groq API (Header Auth)

Dùng cho mọi node HTTP Request gọi Groq.

1. **Credentials** → **Add credential** → **Header Auth**
2. Tên: `Groq API`
3. Cấu hình:
   - **Name:** `Authorization`
   - **Value:** `Bearer gsk_xxxxxxxx` (thay bằng API key Groq thật)
4. Lưu credential
5. Mở từng workflow, chọn các node Groq (`Groq Generate SQL`, `Groq Answer`, `Groq Select Tool`, …) → chọn credential **Groq API**

Placeholder trong JSON export: `GROQ_API_CREDENTIAL_ID` — N8N sẽ yêu cầu map sang credential thật khi import.

**Cách thay thế (tùy chọn):** Nếu đã truyền `GROQ_API_KEY` vào env container N8N, có thể sửa node HTTP Request dùng header expression:

```
={{ 'Bearer ' + $env.GROQ_API_KEY }}
```

### 2. Postgres MCP (PostgreSQL)

Dùng cho node **Postgres Execute** trong `wf-dag-sql.json`.

1. **Credentials** → **Add credential** → **Postgres**
2. Tên: `Postgres MCP`
3. Cấu hình:

| Trường | Giá trị |
|--------|---------|
| Host | `postgres` |
| Database | `cong_ty_ban_le` |
| User | `mcp_user` |
| Password | `mcp_secret_2025` (theo `.env`) |
| Port | `5432` |
| SSL | Disable |

4. Gán credential cho node **Postgres Execute**

Placeholder trong JSON: `POSTGRES_CREDENTIAL_ID`

## Kiểm tra nhanh

```bash
# Health API + ingest RAG (chạy một lần)
curl -X POST http://localhost:8000/ingest

# DAG — doanh thu
curl -X POST http://localhost:5678/webhook/dag \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Doanh thu quý 1 năm 2025 là bao nơu?\"}"

# RAG — chính sách
curl -X POST http://localhost:5678/webhook/rag \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Điều khoản hợp đồng về thanh toán là gì?\"}"

# TAG — tính toán
curl -X POST http://localhost:5678/webhook/tag \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Tính trung bình cộng: 120, 150, 180 triệu\"}"

# Master Router
curl -X POST http://localhost:5678/webhook/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Top 5 sản phẩm bán chạy nhất?\"}"
```

## Luồng xử lý tóm tắt

```
POST /webhook/chat
  → Groq phân loại
  → Switch
      DAG  → POST http://n8n:5678/webhook/dag
      RAG  → POST http://n8n:5678/webhook/rag
      TAG  → POST http://n8n:5678/webhook/tag
      HYBRID → gọi song song RAG + DAG
  → Respond JSON
```

## Xử lý sự cố

| Lỗi | Nguyên nhân | Cách xử lý |
|-----|-------------|------------|
| 404 webhook | Workflow chưa activate | Bật workflow trong N8N |
| 401 Groq | Credential chưa gán / key sai | Kiểm tra Header Auth |
| Postgres connection refused | Sai host | Dùng `postgres`, không dùng `localhost` trong Docker |
| RAG 404 | Chưa ingest | `POST /ingest` trên API |
| DAG webhook fail từ TAG | `wf-dag-sql` chưa active | Activate workflow DAG trước |
