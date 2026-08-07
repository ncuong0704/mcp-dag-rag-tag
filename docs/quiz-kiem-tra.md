# Quiz Kiểm Tra — DAG, RAG, TAG (Model Context Protocol)

**Môn:** Generative AI & AI Agent  
**Số câu:** 10 câu trắc nghiệm  
**Thời gian gợi ý:** 15 phút

---

## Hướng dẫn

- Mỗi câu có **một đáp án đúng duy nhất** (A, B, C hoặc D).
- Ghi lại đáp án của bạn trước khi xem phần **Đáp án** ở cuối tài liệu.
- Nội dung dựa trên lý thuyết MCP và dự án chatbot doanh nghiệp (N8N + PostgreSQL + FastAPI).

---

## Câu hỏi

### Câu 1

**DAG (Data-Augmented Generation) trong dự án này mở rộng LLM bằng cách nào?**

A. Retrieve đoạn văn bản từ PDF rồi đưa vào prompt  
B. Sinh câu truy vấn SQL SELECT, thực thi trên PostgreSQL và tổng hợp kết quả  
C. Gọi function calling để chọn công cụ Python hoặc web search  
D. Fine-tune mô hình trên toàn bộ dữ liệu bán hàng  

---

### Câu 2

**Thành phần nào trong pipeline RAG của dự án chịu trách nhiệm tìm kiếm vector gần nhất với câu hỏi?**

A. PostgreSQL  
B. Groq LLM  
C. FAISS index (qua FastAPI `/retrieve`)  
D. N8N Switch node  

---

### Câu 3

**TAG (Tool-Augmented Generation) khác RAG ở điểm then chốt nào?**

A. TAG luôn nhanh hơn RAG vì không cần embedding  
B. TAG dùng LLM để **chọn và gọi công cụ bên ngoài** (Python, web, SQL), không chỉ retrieve văn bản tĩnh  
C. TAG chỉ hoạt động với dữ liệu có cấu trúc  
D. TAG không sử dụng LLM trong quá trình xử lý  

---

### Câu 4

**Trong workflow `wf-dag-sql`, node Validate SQL có vai trò gì?**

A. Tạo embedding cho câu hỏi người dùng  
B. Chặn các lệnh SQL nguy hiểm (DROP, DELETE, UPDATE, …) và chỉ cho phép SELECT  
C. Phân loại câu hỏi vào DAG hoặc RAG  
D. Format câu trả lời thành JSON cho webhook  

---

### Câu 5

**Master Router (`wf-master-router`) phân loại câu hỏi "Chính sách chiết khấu cho đơn trên 50 triệu?" vào nhãn nào?**

A. DAG  
B. RAG  
C. TAG  
D. HYBRID  

---

### Câu 6

**Câu hỏi "Doanh thu quý 1 năm 2025 là bao nhiêu?" nên được route tới workflow nào?**

A. `wf-rag-docs`  
B. `wf-tag-tools`  
C. `wf-dag-sql`  
D. Không cần workflow — LLM trả lời trực tiếp  

---

### Câu 7

**Trong TAG workflow, công cụ `sql_query` thực chất làm gì?**

A. Chạy mã Python trong sandbox  
B. Gọi webhook nội bộ `/webhook/dag` để ủy quyền truy vấn SQL  
C. Tìm kiếm DuckDuckGo  
D. Đọc trực tiếp file PDF trong `data/documents/`  

---

### Câu 8

**Nhãn HYBRID trong Master Router được kích hoạt khi nào?**

A. Khi câu hỏi bằng tiếng Anh  
B. Khi cần **cả tài liệu nội bộ (RAG) và dữ liệu CSDL (DAG)** hoặc nhiều nguồn kết hợp  
C. Khi Groq API bị rate limit  
D. Khi FAISS index chưa được ingest  

---

### Câu 9

**Rủi ro hallucination (bịa thông tin) được giảm thiểu tốt nhất bằng cách nào trong từng biến thể?**

A. DAG: grounding bằng kết quả SQL thực tế; RAG: grounding bằng chunks retrieve; TAG: grounding bằng output công cụ  
B. Tắt temperature = 0 cho mọi LLM call là đủ, không cần retrieve hay SQL  
C. Chỉ dùng một LLM lớn nhất, không cần phân biệt DAG/RAG/TAG  
D. Luôn trả lời bằng tiếng Anh để giảm sai sót  

---

### Câu 10

**Trước khi workflow RAG hoạt động, bước bắt buộc nào phải thực hiện trên FastAPI?**

A. `POST /execute-python`  
B. `POST /web-search`  
C. `POST /ingest` — chunk PDF, embed và xây dựng FAISS index  
D. `DELETE /faiss` — xóa index cũ  

---

## Đáp án

| Câu | Đáp án | Giải thích ngắn |
|-----|--------|-----------------|
| **1** | **B** | DAG sinh SQL SELECT, query PostgreSQL, format kết quả — không retrieve PDF hay function calling. |
| **2** | **C** | FAISS lưu vector embedding; `/retrieve` trả top-k chunks liên quan. |
| **3** | **B** | TAG = Tool-Augmented: LLM chọn tool động; RAG chỉ retrieve văn bản đã index. |
| **4** | **B** | Guardrail chặn lệnh ghi/xóa, bắt buộc SELECT — bảo vệ DB. |
| **5** | **B** | Chiết khấu nằm trong `chinh-sach-ban-hang.pdf` → RAG. |
| **6** | **C** | Doanh thu là số liệu CSDL → DAG (`wf-dag-sql`). |
| **7** | **B** | `sql_query` delegate sang workflow DAG qua webhook nội bộ N8N. |
| **8** | **B** | HYBRID = câu hỏi cần RAG + DAG (hoặc đa nguồn); router gọi song song. |
| **9** | **A** | Mỗi biến thể ground LLM vào nguồn ngoài: SQL rows, retrieved chunks, tool output. |
| **10** | **C** | Ingest PDF → chunk → embed → FAISS; không ingest thì retrieve trả 404. |

---

## Thang điểm gợi ý

| Số câu đúng | Mức đạt |
|-------------|---------|
| 9–10 | Xuất sắc — nắm vững DAG/RAG/TAG và kiến trúc dự án |
| 7–8 | Khá — cần ôn thêm routing và pipeline RAG |
| 5–6 | Trung bình — nên xem lại báo cáo mục 1 và 3 |
| Dưới 5 | Cần học lại lý thuyết MCP và chạy demo thực tế |

---

*Chúc bạn ôn tập hiệu quả!*
