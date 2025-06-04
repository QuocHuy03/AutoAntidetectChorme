# 🔁 while

**Chức năng:** Lặp lại khối hành động cho đến khi điều kiện sai.

```json
{
  "action": "while",
  "condition": {
    "variable": "count",
    "operator": "<",
    "value": 5
  },
  "do": [
    { "action": "click", "xpath": "//button" },
    { "action": "increase_variable", "variable": "count", "value": 1 }
  ]
}
```

**Tham số:**
- `condition`: Điều kiện lặp (`variable`, `operator`, `value`).
- `do`: Danh sách hành động bên trong vòng lặp.