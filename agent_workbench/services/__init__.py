"""agent_workbench/services — Agent Workbench V6 内部服务实现。

第一版在 agent 内实现：
- Prompt 渲染服务
- SQLite Memory 服务
- Model Provider 统一接口
- Tool Registry

未来部分能力可上移到 v6-service，但接口保持向后兼容。
"""
from __future__ import annotations
