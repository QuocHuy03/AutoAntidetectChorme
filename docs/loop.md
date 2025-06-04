# 🔁 loop

**Chức năng:** Tạo vòng lặp `for` với biến đếm.

```json
{
  "action": "loop",
  "start": 1,
  "count": 5,
  "variable": "i",
  "do": [
    { "action": "click", "xpath": "(//button)[{{i}}]" }
  ]
}
```

**Tham số:**
- `start`: Giá trị bắt đầu của biến.
- `count`: Tổng số vòng lặp.
- `variable`: Tên biến dùng trong `do`.
- `do`: Mảng các hành động thực hiện trong mỗi vòng.

**Lưu ý:** Biến được dùng bằng `{{variable}}` trong các hành động bên trong.