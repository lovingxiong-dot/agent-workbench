"""v6/runtime/engines/code.py — Code Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，不接入代码执行器或沙箱。
未来职责：代码生成、执行、解释、安全校验。
"""
from __future__ import annotations

from v6.runtime.engines.base import BaseEngine


class CodeEngine(BaseEngine):
    """Code Engine：负责代码生成与执行。"""

    name = "code"
    capabilities = ["code_generation", "code_execution"]
