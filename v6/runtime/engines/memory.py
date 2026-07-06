"""v6/runtime/engines/memory.py — Memory Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，不接入向量库或数据库。
未来职责：短期/长期/画像记忆、检索、上下文块管理。
"""
from __future__ import annotations

from v6.runtime.engines.base import BaseEngine


class MemoryEngine(BaseEngine):
    """Memory Engine：负责记忆管理与检索。"""

    name = "memory"
