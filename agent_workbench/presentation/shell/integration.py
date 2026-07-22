"""presentation/shell/integration.py — Presentation Pipeline 编排。

Phase 1-C：编排全链路数据流，证明：
    Runtime Object → Adapter → ViewModel → Transformer → Shell Contract
可以完整跑通。

Shell Boundary：
    ✅ 允许：import presentation/adapters + shell/transformers + shell/protocol
    ❌ 禁止：import PySide6、创建 QWidget、import Runtime
"""
from __future__ import annotations

from typing import Any, Dict, List

from agent_workbench.presentation.shell.protocol import (
    InspectorState,
    NavigationGroup,
    NavigationItem,
    WorkspaceMessage,
    WorkspaceState,
)
from agent_workbench.presentation.shell.transformers.capability import (
    to_navigation_items as _cap_to_nav_items,
)
from agent_workbench.presentation.shell.transformers.message import to_workspace_state
from agent_workbench.presentation.shell.transformers.session import to_navigation_groups
from agent_workbench.presentation.view_models.capability import CapabilityViewModel
from agent_workbench.presentation.view_models.session import (
    MessageViewModel,
    SessionViewModel,
)


class PresentationPipeline:
    """编排 Runtime Object → Shell Contract 的完整数据链路。

    职责：
    - 接收 Runtime 原始数据（dict/object），转换为 ViewModel
    - 将 ViewModel 通过 Transformer 转换为 Shell Contract
    - 不创建 Widget，不 import PySide6

    使用方：
    - WorkbenchUIController（Phase 1-C 接入点）
    - QtShell（Phase 1-D 接入点）
    """

    # ── Session → Navigation ──

    @staticmethod
    def sessions_to_navigation_groups(
        raw_sessions: List[Dict[str, Any]],
    ) -> List[NavigationGroup]:
        """Runtime Session 原始数据 → NavigationGroup 列表。

        原始数据格式：ConversationService.list_groups() 返回的 dict 列表：
        {"sid": str, "title": str, "group_id": str, ...}
        """
        view_models = [
            SessionViewModel(
                id=s.get("sid", ""),
                title=s.get("title", "Untitled"),
                preview=s.get("preview", ""),
                timestamp=s.get("timestamp", ""),
                message_count=s.get("message_count", 0),
                is_active=s.get("is_active", False),
                group_id=s.get("group_id", "default"),
            )
            for s in raw_sessions
        ]
        return to_navigation_groups(view_models)

    # ── Messages → Workspace ──

    @staticmethod
    def messages_to_workspace_state(
        title: str,
        subtitle: str,
        raw_messages: List[Dict[str, Any]],
        models: List[str] | None = None,
    ) -> WorkspaceState:
        """Runtime Message 原始数据 → WorkspaceState。

        原始数据格式：RuntimeContext.messages 对应的 dict 列表：
        {"id": str, "role": str, "content": str, "tool_calls": [...]}
        """
        view_models = [
            MessageViewModel(
                id=m.get("id", ""),
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", ""),
                tool_calls=m.get("tool_calls", []),
            )
            for m in raw_messages
        ]
        return to_workspace_state(
            title=title,
            subtitle=subtitle,
            messages=view_models,
            models=models,
        )

    # ── Capability → Navigation ──

    @staticmethod
    def capabilities_to_navigation_items(
        raw_capabilities: List[Dict[str, Any]],
    ) -> List[NavigationItem]:
        """Runtime Capability 原始数据 → NavigationItem 列表。"""
        view_models = [
            CapabilityViewModel(
                id=c.get("id", ""),
                name=c.get("name", ""),
                description=c.get("description", ""),
                category=c.get("category", "tool"),
                status=c.get("status", "available"),
                is_enabled=c.get("is_enabled", False),
            )
            for c in raw_capabilities
        ]
        return _cap_to_nav_items(view_models)

    # ── Metadata → Inspector ──

    @staticmethod
    def metadata_to_inspector_state(
        module_id: str,
        raw_properties: List[Dict[str, Any]],
    ) -> InspectorState:
        """Runtime Metadata → InspectorState。

        原始数据格式：ModulePresentation.properties 对应的 dict 列表：
        {"name": str, "value": Any, "type": str, ...}
        """
        return InspectorState(
            object_id=module_id,
            properties=[
                {
                    "name": p.get("name", ""),
                    "value": p.get("value", ""),
                    "type": p.get("type", "string"),
                    "label": p.get("label", p.get("name", "")),
                }
                for p in raw_properties
            ],
        )
