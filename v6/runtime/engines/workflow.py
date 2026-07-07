"""v6/runtime/engines/workflow.py — Workflow Engine 空壳。

设计来源：V6.5 Runtime Foundation Layer Step 4。

当前阶段：Runtime 骨架验证，不实现任何 Workflow DSL 或执行器。
未来职责：工作流定义、节点调度、状态机执行。
"""
from __future__ import annotations

from v6.runtime.engines.base import BaseEngine


class WorkflowEngine(BaseEngine):
    """Workflow Engine：负责工作流编排与执行。"""

    name = "workflow"
    capabilities = ["workflow_execution"]
