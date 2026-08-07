# Demo MCP — lệnh nhanh

## 1. Thiết lập (chạy một lần)
```powershell
.\scripts\setup-demo.ps1
```

## 2. Trong N8N (http://localhost:5678)
- Import 4 file từ `n8n/workflows/`
- Credential Groq: Header Auth → `Authorization` = `Bearer <GROQ_API_KEY>`
- Credential Postgres: host `postgres`, db `cong_ty_ban_le`, user `mcp_user`, pass `mcp_secret_2025`
- **Activate** cả 4 workflow

## 3. Chạy demo
```powershell
$body = @{ query = "Doanh thu quý 1 năm 2025 là bao nhiêu?" } | ConvertTo-Json
$result = Invoke-RestMethod -Method POST `
  -Uri http://localhost:5678/webhook/dag `
  -ContentType "application/json" `
  -Body $body

$result | ConvertTo-Json -Depth 5
$result.summary
$result.markdown
```

Hoặc chạy cả 3 query:
```powershell
.\scripts\run-demo.ps1
```

## Kết quả mong đợi
- **DAG:** doanh thu Q1/2025 ≈ 485.000.000 VND
- **RAG:** thanh toán 50% trong 7 ngày, 50% trong 30 ngày
- **TAG:** trung bình 150 triệu
