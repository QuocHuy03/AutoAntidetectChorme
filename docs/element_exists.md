# 🧭 element_exists

**Chức năng:** Kiểm tra phần tử có tồn tại không. Cho phép thực thi `if_true`, `if_false`.

```json
{
  "action": "element_exists",
  "xpath": "//*[@id='input']",
  "if_true": [{ "action": "click", "xpath": "//*[@id='input']" }],
  "if_false": [{ "action": "screenshot" }],
  "stop_on_fail": true
}
```