# 🧠 `eval_script` - Thực thi JavaScript và lưu kết quả

**Chức năng:**  
Thực thi một đoạn JavaScript trực tiếp trong trang web hiện tại và **lưu kết quả trả về vào một biến nội bộ** (tuỳ chọn), giúp tái sử dụng trong các block sau.

---

## ✅ Cấu trúc cơ bản

```json
{
  "action": "eval_script",
  "value": "return document.title;",
  "store_as": "page_title"
}

```