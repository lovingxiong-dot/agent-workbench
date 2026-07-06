"""v6/runtime/engines/knowledge.py — Knowledge Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，不接入知识图谱或 RAG 检索。
未来职责：知识检索、RAG、图谱查询、文档问答。
"""
from __future__ import annotations

from v6.runtime.engines.base import BaseEngine


class KnowledgeEngine(BaseEngine):
    """Knowledge Engine：负责知识与检索增强。"""

    name = "knowledge"
