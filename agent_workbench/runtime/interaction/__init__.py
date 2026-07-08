"""agent_workbench/runtime/interaction/ — Workbench Interaction Boundary Layer.

该包位于 UI / MCP / Local Agent 与 Runtime 之间，职责：
- 定义外部输入协议 RuntimeRequest。
- 定义 UI 事件协议 InteractionEvent。
- 将 RuntimeEvent 映射为 InteractionEvent。
- 提供 UIEventRenderer 协议。
- 通过 WorkbenchInteractionLayer 把 RuntimeRequest 提交给 Runtime。

约束：
- 本包不包含任何 Qt / Web / CLI 渲染实现。
- 本包不持有 DecisionManager，不做出 Capability 路由决策。
- 本包不依赖 capability / planner / service / orchestrator 实现。
"""
from __future__ import annotations

from agent_workbench.runtime.interaction.event import InteractionEvent, InteractionEventType
from agent_workbench.runtime.interaction.layer import WorkbenchInteractionLayer
from agent_workbench.runtime.interaction.mapper import RuntimeEventMapper
from agent_workbench.runtime.interaction.renderer import UIEventRenderer
from agent_workbench.runtime.interaction.request import RuntimeRequest, RuntimeRequestSource

__all__ = [
    "InteractionEvent",
    "InteractionEventType",
    "RuntimeEventMapper",
    "RuntimeRequest",
    "RuntimeRequestSource",
    "UIEventRenderer",
    "WorkbenchInteractionLayer",
]
