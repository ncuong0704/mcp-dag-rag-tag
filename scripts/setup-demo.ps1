# Thiết lập và chạy demo MCP (DAG / RAG / TAG)
# Yêu cầu: Docker Desktop đang chạy, file .env đã có GROQ_API_KEY

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== 1. Kiểm tra Docker ===" -ForegroundColor Cyan
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker chưa chạy. Hãy mở Docker Desktop rồi chạy lại script này." -ForegroundColor Red
    exit 1
}

Write-Host "=== 2. Tạo PDF (nếu thiếu) ===" -ForegroundColor Cyan
if (-not (Test-Path "data\documents\hop-dong-mau.pdf")) {
    python scripts/generate_pdfs.py
}

Write-Host "=== 3. Khởi động Docker Compose ===" -ForegroundColor Cyan
docker compose up -d --build

Write-Host "=== 4. Chờ API sẵn sàng ===" -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod http://localhost:8000/health -TimeoutSec 3
        if ($health.status -eq "ok") { $ready = $true; break }
    } catch { Start-Sleep -Seconds 3 }
}
if (-not $ready) {
    Write-Host "API chưa sẵn sàng sau 90s. Kiểm tra: docker compose logs api" -ForegroundColor Yellow
} else {
    Write-Host "API OK. faiss_ready=$($health.faiss_ready)" -ForegroundColor Green
}

Write-Host "=== 5. Ingest tài liệu RAG ===" -ForegroundColor Cyan
try {
    $ingest = Invoke-RestMethod -Method POST -Uri http://localhost:8000/ingest -TimeoutSec 120
    Write-Host "Đã index $($ingest.chunks) chunks từ: $($ingest.files -join ', ')" -ForegroundColor Green
} catch {
    Write-Host "Ingest lỗi: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Bước tiếp theo (thủ công trong N8N) ===" -ForegroundColor Cyan
Write-Host "1. Mở http://localhost:5678"
Write-Host "2. Import 4 workflow từ n8n/workflows/"
Write-Host "3. Gán credential Groq (Header Auth) và Postgres (host=postgres)"
Write-Host "4. Activate cả 4 workflow (DAG, RAG, TAG trước Master Router)"
Write-Host "5. Chạy: .\scripts\run-demo.ps1"
Write-Host ""
