"""agent_workbench/runtime/manager/runtime.py — ManagerRuntime（Commit 2 实现）。

设计约束：
- ManagerRuntime 不调用 Engine，只生成 Task。
- 所有执行交给 Runtime / Orchestrator。
- Commit 2 不实现复杂 Capability Chain，仅建立 UserRequest → CapabilityMatch → Task 主链。
- 保留显式 task_type 作为强信号，保证 chat_with_tool 等旧 API 行为不变。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from v6.runtime.event_bus import RuntimeEventType
from v6.runtime.manager import Manager
from v6.runtime.task import Task
from v6.runtime.user_request import UserRequest

from agent_workbench.runtime.capability import CapabilityIntent, CapabilityStep
from agent_workbench.runtime.capability.model import CapabilityMatch

if TYPE_CHECKING:
    from v6.runtime.event_bus import EventBus

    from agent_workbench.runtime.capability.graph import CapabilityRegistry


class ManagerRuntime(Manager):
    """默认 Manager：将 UserRequest 解析为带 Capability Context 的 Task。"""

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        event_bus: EventBus | None = None,
    ) -> None:
        self._registry = capability_registry
        self._event_bus = event_bus

    def classify(self, request: UserRequest) -> CapabilityIntent:
        """将 UserRequest 分类为 CapabilityIntent。"""
        metadata = dict(request.metadata or {})
        return CapabilityIntent(
            text=request.text or "",
            metadata=metadata,
            required_permissions=list(metadata.get("required_permissions", [])),
            preferred_providers=list(metadata.get("preferred_providers", [])),
        )

    def resolve(self, request: UserRequest) -> Task:
        """将 UserRequest 解析为 Task。

        流程：
        1. classify(request) → CapabilityIntent
        2. registry.resolve(intent) → CapabilityMatch
        3. 构建 Task，capability = match.definition.engine_capability，metadata 携带 Capability Context
        """
        intent = self.classify(request)
        match = self._resolve_match(intent)
        self._publish_manager_events(intent, match)

        task_id = request.task_id
        if not task_id and request.metadata:
            task_id = request.metadata.get("task_id")
        session_id = request.session_id
        metadata = self._build_task_metadata(match, intent)

        return Task(
            id=task_id,
            session_id=session_id,
            capability=self._legacy_capability(match, intent),
            payload=self._build_payload(request),
            metadata=metadata,
        )

    def _legacy_capability(self, match: CapabilityMatch, intent: CapabilityIntent) -> str:
        """生成与旧 Engine / PlannerLoop 兼容的 Task.capability。

        Commit 2 不升级 Orchestrator / CapabilityRouter，因此保持旧取值：
        - tool 请求 -> "tool"
        - 其他 -> "chat"
        真实 Capability Context 存入 metadata（capability_id / capability_path）。
        """
        if intent.metadata.get("task_type") == "tool":
            return "tool"
        return "chat"

    def _resolve_match(self, intent: CapabilityIntent) -> CapabilityMatch:
        """解析 CapabilityMatch，优先处理显式 task_type 信号以保持旧 API 兼容。"""
        explicit_task_type = intent.metadata.get("task_type")
        if explicit_task_type == "tool":
            tool_definition = self._registry.get("tool")
            if tool_definition is not None:
                return CapabilityMatch(
                    definition=tool_definition,
                    score=1.0,
                    lineage=self._registry.lineage("tool"),
                )

        return self._registry.resolve(intent)

    def _build_payload(self, request: UserRequest) -> dict[str, Any]:
        """构建 Task payload。"""
        payload: dict[str, Any] = {"text": request.text or ""}
        if request.attachments:
            payload["attachments"] = list(request.attachments)
        if request.metadata:
            payload["tool_request"] = request.metadata.get("tool_request")
        return payload

    def _build_task_metadata(
        self,
        match: CapabilityMatch,
        intent: CapabilityIntent,
    ) -> dict[str, Any]:
        """构建 Task metadata，包含 Capability Context。"""
        metadata: dict[str, Any] = dict(intent.metadata)
        metadata["capability_id"] = match.definition.id
        metadata["capability_path"] = list(match.lineage)
        metadata["capability_name"] = match.definition.name or match.definition.id
        if match.definition.persona is not None:
            metadata["capability_persona"] = match.definition.persona.to_dict()

        chain = self._build_chain(match, intent)
        if chain:
            from agent_workbench.runtime.capability import CapabilityChain

            metadata.update(CapabilityChain.to_metadata(chain))

        return metadata

    def _build_chain(
        self,
        match: CapabilityMatch,
        intent: CapabilityIntent,
    ) -> list[CapabilityStep] | None:
        """根据 CapabilityMatch 生成静态 Capability Chain。

        Commit 4 规则：
        - 仅对父节点生成其子树所有叶子的顺序链。
        - "coding.python" -> [analysis, debugging, testing]
        - "coding" -> [python.analysis, python.debugging, python.testing, code_editor]
        - 叶子能力（chat / tool / analyze / debugging 等）不生成链。
        """
        leaves = self._registry.leaves(match.definition.id)
        if not leaves or len(leaves) == 1 and leaves[0].id == match.definition.id:
            return None

        return [
            CapabilityStep(
                capability_id=definition.id,
                engine_capability=definition.engine_capability or "text_generation",
            )
            for definition in leaves
        ]

    def _publish_manager_events(self, intent: CapabilityIntent, match: CapabilityMatch) -> None:
        """发布 Manager 级事件（Commit 2 可选，事件总线启动时生效）。"""
        if self._event_bus is None:
            return

        # 总线未启动时静默跳过，避免测试/初始化阶段抛错。
        if not getattr(self._event_bus, "running", False):
            return

        task_id = intent.metadata.get("task_id", "")
        self._event_bus.publish(
            RuntimeEventType.MANAGER_INTENT_CLASSIFIED,
            {"intent": intent.to_dict()},
            task_id=task_id,
            source="manager_runtime",
        )
        self._event_bus.publish(
            RuntimeEventType.MANAGER_CAPABILITY_SELECTED,
            {
                "capability_id": match.definition.id,
                "capability_path": list(match.lineage),
                "score": match.score,
            },
            task_id=task_id,
            source="manager_runtime",
        )
