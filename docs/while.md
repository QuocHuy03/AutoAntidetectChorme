# 🔁 while

**Chức năng:** Lặp lại khối hành động cho đến khi điều kiện sai.

```json
{
    "action": "while",
    "condition": "{{COUNT_MAIL}} > 0",  # Điều kiện vòng lặp
    "variable": "i",
    "do": [
        {
            "action": "log",
            "value": "Lặp qua {{i}} với COUNT_MAIL={{COUNT_MAIL}}"
        },
        {
            "action": "eval_script",
            "value": "var result = {{i}} * 2; return result;",
            "store_as": "result"
        }
    ]
}

```

**Tham số:**
- `condition`: Điều kiện lặp (`variable`, `operator`, `value`).
- `do`: Danh sách hành động bên trong vòng lặp.