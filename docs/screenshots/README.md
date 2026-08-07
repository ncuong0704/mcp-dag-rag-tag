# Hướng dẫn chụp screenshot N8N cho báo cáo

Sau khi import và activate workflow, chụp các ảnh sau và lưu vào thư mục này:

| File | Nội dung |
|------|----------|
| `01-workflows-list.png` | Danh sách 4 workflow đã Active (màu xanh) |
| `02-wf-dag-sql.png` | Canvas workflow `wf-dag-sql` (đủ node) |
| `03-wf-rag-docs.png` | Canvas workflow `wf-rag-docs` |
| `04-wf-tag-tools.png` | Canvas workflow `wf-tag-tools` |
| `05-wf-master-router.png` | Canvas workflow `wf-master-router` |
| `06-execution-dag.png` | Execution log thành công của query DAG |

**Cách chụp nhanh:** Mở http://localhost:5678 → Workflows → chọn workflow → `Win + Shift + S` (Windows Snipping Tool).

**Lệnh PowerShell mở N8N:**
```powershell
Start-Process "http://localhost:5678"
```
