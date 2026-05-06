# OpenAI API Usage Skill (Cost-Safe + Free Quota Aware)

## 🎯 Mục tiêu
Đảm bảo mọi request API:
- Ưu tiên dùng **free daily quota**
- Tránh vượt quota gây **mất tiền ($)**
- Tối ưu token usage cho dự án (RAG / Agent / Chatbot)

---

## 🧠 Thông tin quota (bắt buộc nhớ)

### 🔹 Nhóm model mạnh (quota nhỏ)
- **250,000 tokens / ngày**
- Bao gồm:
  - gpt-5.4
  - gpt-5.2
  - gpt-5.1
  - gpt-5.1-codex
  - gpt-5
  - gpt-5-codex
  - gpt-5-chat-latest
  - gpt-4.1
  - gpt-4o
  - o1
  - o3

---

### 🔹 Nhóm model nhẹ (quota lớn)
- **2,500,000 tokens / ngày**
- Bao gồm:
  - gpt-5.4-mini
  - gpt-5.4-nano
  - gpt-5.1-codex-mini
  - gpt-5-mini
  - gpt-5-nano
  - gpt-4.1-mini
  - gpt-4.1-nano
  - gpt-4o-mini
  - o1-mini
  - o3-mini
  - o4-mini
  - codex-mini-latest

---

## ⚠️ Nguyên tắc bắt buộc

### 1. Ưu tiên model nhẹ
```txt
DEFAULT:
→ gpt-4o-mini
→ gpt-4.1-mini
→ gpt-5-mini
```

Chỉ dùng model mạnh khi:
- reasoning phức tạp
- cần độ chính xác cao

---

### 2. Giới hạn token mỗi request

```python
max_tokens = 200 - 500 (default)
```

Không được:
- để unlimited
- trả lời dài không cần thiết

---

### 3. Giảm độ dài input

Luôn:
- truncate context
- dùng chunking (RAG)
- tránh gửi full document

---

### 4. Bật logging usage

Bắt buộc log:
```json
{
  "prompt_tokens": ..., 
  "completion_tokens": ...
}
```

---

### 5. Fallback strategy

```txt
IF model mạnh → tốn token
THEN fallback → model mini
```

---

## 🧪 Chiến lược sử dụng thông minh

### 🔹 Flow chuẩn

```txt
User request
   ↓
Try mini model (cheap/free)
   ↓
Nếu fail → escalate lên model mạnh
```

---

### 🔹 RAG tối ưu

- Top-k: 3–5 docs
- Chunk size: 300–500 tokens
- Không nhồi toàn bộ DB

---

### 🔹 Agent tối ưu

- Giới hạn số step
- Cache kết quả
- Tránh loop vô hạn

---

## 🔍 Kiểm soát chi phí

### Rule quan trọng:

```txt
IF daily free quota exceeded
→ STOP hoặc downgrade model
```

---

### Detect vượt quota (gián tiếp)

- Theo dõi:
  - OpenAI Usage
  - Cost > $0 → đã mất tiền

---

## 🔒 Safe Mode (khuyến nghị)

```txt
MODE: SAFE
- Chỉ dùng model mini
- max_tokens <= 300
- Không streaming dài
```

---

## 🚫 Những điều cấm

- Gọi GPT-5.x liên tục
- Prompt dài không kiểm soát
- Không log usage
- Không kiểm tra cost

---

## ✅ Checklist trước khi deploy

- [ ] Dùng model mini mặc định
- [ ] Có fallback logic
- [ ] Có limit max_tokens
- [ ] Có logging usage
- [ ] Test không vượt free quota

---

## 🎯 Kết luận

- Free quota đủ cho dev/test
- Muốn scale → phải tối ưu token
- Kiểm soát = sống, không kiểm soát = cháy tiền 🔥
