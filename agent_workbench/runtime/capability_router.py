"""agent_workbench/runtime/capability_router.py — Capability Router。

职责：
- 根据 RuntimeContext 解析任务所需 Engine capability。
- v6.9.3 Commit 3 升级：优先读取 ctx.metadata["capability_id"]，通过 CapabilityRegistry
  解析为 engine_capability；无 capability_id 时回退到旧 task_type 逻辑。
- 通过 EventBus 发布 CAPABILITY_RESOLVED 事件，Trace 记录能力解析结果。

设计边界：
- CapabilityRouter 属于 Application Layer，不是 v6-core 的一部分。
- 不修改 Task.capability，只负责把 metadata 中的 capability_id 映射到 Engine capability。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from v6.runtime.event_bus import RuntimeEventType

if TYPE_CHECKING:
    from v6.runtime.context import RuntimeContext
    from v6.runtime.event_bus import EventBus

    from agent_workbench.runtime.capability.graph import CapabilityRegistry


class CapabilityRouter:
    """Capability 路由：将 RuntimeContext 中的 capability_id 映射到 Engine capability。"""

    def __init__(
        self,
        default_capability: str = "chat",
        capability_registry: Optional["CapabilityRegistry"] = None,
    ) -> None:
        self._default_capability = default_capability
        self._registry = capability_registry

    def resolve(
        self,
        ctx: "RuntimeContext",
        event_bus: Optional["EventBus"] = None,
        **kwargs: Any,
    ) -> str:
        """解析任务所需 Engine capability 并发布事件。

        解析优先级：
        1. ctx.metadata["capability_id"] → CapabilityRegistry → engine_capability。
        2. ctx.metadata["task_type"] == "tool" → "tool_execution"。
        3. 回退到 default_capability。
        """
        capability_id: str | None = ctx.metadata.get("capability_id")
        engine_capability, resolved_by, capability_path = self._resolve_from_registry(
            capability_id,
        )

        if engine_capability is None:
            engine_capability = self._fallback(ctx, kwargs)
            resolved_by = "fallback"
            capability_path = []

        payload: Dict[str, Any] = {
            "capability": engine_capability,
            "reason": f"resolved by {resolved_by}",
            "resolved_by": resolved_by,
        }
        if capability_id is not None:
            payload["capability_id"] = capability_id
        if capability_path:
            payload["capability_path"] = list(capability_path)
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
        return engine_capability

    def _resolve_from_registry(
        self,
        capability_id: str | None,
    ) -> tuple[str | None, str, list[str]]:
        """尝试从 CapabilityRegistry 解析 engine_capability。

        返回：(engine_capability 或 None, resolved_by, capability_path)
        """
        if capability_id is None or self._registry is None:
            return None, "none", []

        definition = self._registry.get(capability_id)
        if definition is None:
            return None, "none", []

        engine_capability = definition.engine_capability or "text_generation"
        lineage = self._registry.lineage(capability_id)
        return engine_capability, "registry", lineage

    def _fallback(self, ctx: "RuntimeContext", context: Dict[str, Any]) -> str:
        """旧版回退逻辑：仅基于 task_type 判断 tool，其余返回 default。"""
        if ctx.metadata.get("task_type") == "tool":
            return "tool_execution"
        return self._default_capability
