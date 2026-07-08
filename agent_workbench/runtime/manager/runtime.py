"""agent_workbench/runtime/manager/runtime.py — ManagerRuntime（Commit 2 实现）。

Commit 0 仅提供类结构占位：
- 实现 Manager Protocol 签名。
- 构造函数持有 CapabilityRegistry 与 EventBus 引用。
- classify / resolve / _build_chain / _publish_manager_events 方法体留空或抛 NotImplementedError。

设计约束：
- ManagerRuntime 不调用 Engine，只生成 Task。
- 所有执行交给 Runtime / Orchestrator。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from v6.runtime.manager import Manager
from v6.runtime.task import Task
from v6.runtime.user_request import UserRequest

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

    def classify(self, request: UserRequest) -> None:
        """将 UserRequest 分类为 CapabilityIntent（Commit 2 实现）。"""
        raise NotImplementedError

    def resolve(self, request: UserRequest) -> Task:
        """将 UserRequest 解析为 Task（Commit 2 实现）。"""
        raise NotImplementedError

    def _build_chain(self, match: None, intent: None) -> None:
        """根据 CapabilityMatch 与 CapabilityIntent 生成静态链（Commit 2 实现）。"""
        raise NotImplementedError

    def _publish_manager_events(self, intent: None, match: None) -> None:
        """发布 Manager 级事件（Commit 2 实现）。"""
        raise NotImplementedError
