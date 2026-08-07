# Demo 3 query rubric: DAG, RAG, TAG qua webhook N8N
$ErrorActionPreference = "Continue"
$base = "http://localhost:5678/webhook"

$demos = @(
    @{
        Name = "DAG"
        Url  = "$base/dag"
        Body = @{ query = "Doanh thu quý 1 năm 2025 là bao nhiêu?" }
    },
    @{
        Name = "RAG"
        Url  = "$base/rag"
        Body = @{ query = "Điều khoản hợp đồng về thanh toán là gì?" }
    },
    @{
        Name = "TAG"
        Url  = "$base/tag"
        Body = @{ query = "Tính trung bình cộng: 120, 150, 180 triệu" }
    }
)

Write-Host "=== Demo MCP — kiểm tra webhook N8N ===" -ForegroundColor Cyan
Write-Host "Lưu ý: Workflow phải đã Activate trong N8N`n"

foreach ($demo in $demos) {
    Write-Host "--- $($demo.Name) ---" -ForegroundColor Yellow
    try {
        $json = $demo.Body | ConvertTo-Json -Compress
        $result = Invoke-RestMethod -Method POST -Uri $demo.Url -ContentType "application/json" -Body $json -TimeoutSec 120
        $result | ConvertTo-Json -Depth 5
        if ($result.summary) { Write-Host "Summary: $($result.summary)" -ForegroundColor Green }
        if ($result.answer)  { Write-Host "Answer: $($result.answer.Substring(0, [Math]::Min(200, $result.answer.Length)))..." -ForegroundColor Green }
    } catch {
        Write-Host "LỖI: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "  → Kiểm tra workflow $($demo.Name) đã Activate và credential Groq đã gán." -ForegroundColor Gray
    }
    Write-Host ""
}
