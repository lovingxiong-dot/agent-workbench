"""presentation/protocols/ — 跨层通信协议。

Protocols 是 Runtime ↔ Presentation 之间的通信契约。
它们不属于 Runtime，也不属于 UI。类似 HTTP 不属于 nginx 也不属于浏览器。

约束：
  ✓ 纯 Python 数据模型（dataclasses + Protocol）
  ✓ 零 Runtime Implementation import
  ✓ 零 PySide6 import
  ✗ 不 import Runtime（engine, executor, session, llm, tool）
  ✗ 不 import UI 框架
"""