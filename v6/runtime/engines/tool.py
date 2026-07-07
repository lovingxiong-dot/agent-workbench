"""v6/runtime/engines/tool.py — Tool Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，不接入任何真实工具或 MCP。
未来职责：工具注册、Phase 白名单、执行编排、结果返回。
"""
from __future__ import annotations

from v6.runtime.engines.base import BaseEngine


class ToolEngine(BaseEngine):
    """Tool Engine：负责工具调用与编排。"""

    name = "tool"
    capabilities = ["tool_execution"]
