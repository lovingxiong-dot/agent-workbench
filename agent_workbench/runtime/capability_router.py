"""agent_workbench/runtime/capability_router.py — Capability Router Stub。

职责：
- 根据 RuntimeContext 解析任务所需 Capability。
- Foundation 阶段默认返回 "chat"，未来可扩展为基于内容/意图的智能路由。
- 通过 EventBus 发布 CAPABILITY_RESOLVED 事件，使 Trace 记录能力解析结果。

设计边界：
- CapabilityRouter 属于 Application Layer，不是 v6-core 的一部分。
- Orchestrator 调用 CapabilityRouter，但 Trace 中的 CAPABILITY_RESOLVED 事件由 Router 自己发出。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from v6.runtime.event_bus import RuntimeEventType

if TYPE_CHECKING:
    from v6.runtime.context import RuntimeContext
    from v6.runtime.event_bus import EventBus


class CapabilityRouter:
    """Capability 路由 Stub。

    Foundation 阶段仅做默认能力回退，后续可替换为基于 Planner/Rules 的真实路由。
    """

    def __init__(self, default_capability: str = "chat") -> None:
        self._default_capability = default_capability

    def resolve(
        self,
        ctx: "RuntimeContext",
        event_bus: Optional["EventBus"] = None,
        **kwargs: Any,
    ) -> str:
        """解析任务所需 Capability 并发布事件。

        Args:
            ctx: 当前 RuntimeContext。
            event_bus: 用于发布 CAPABILITY_RESOLVED 事件；未注入时静默跳过。
            **kwargs: 预留扩展参数，供未来 Planner/Rules 传入决策上下文。

        Returns:
            解析出的 capability 名称。
        """
        capability = self._fallback(ctx, kwargs)
        payload: Dict[str, Any] = {
            "capability": capability,
            "reason": "foundation default",
        }
        if kwargs:
            payload["context"] = kwargs

        if event_bus is not None:
            event_bus.publish(
                event_type=RuntimeEventType.CAPABILITY_RESOLVED,
                payload=payload,
                task_id=ctx.task_id,
                source="capability_router",
                phase=ctx.phase,
            )
        return capability

    def _fallback(self, ctx: "RuntimeContext", context: Dict[str, Any]) -> str:
        """Foundation 阶段默认能力选择。

        返回用户可见的 capability 名称（如 chat / tool / image），
        由 Orchestrator 进一步映射到 Engine capability（如 text_generation）。
        """
        if ctx.metadata.get("task_type") == "tool":
            return "tool"
        return self._default_capability
