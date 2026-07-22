"""MessageViewModel → WorkspaceState 转换器。"""
from __future__ import annotations

from typing import List

from agent_workbench.presentation.view_models.session import MessageViewModel
from agent_workbench.presentation.shell.protocol import WorkspaceMessage, WorkspaceState


def to_workspace_state(
    title: str = "",
    subtitle: str = "",
    messages: List[MessageViewModel] | None = None,
    models: List[str] | None = None,
) -> WorkspaceState:
    """MessageViewModel 列表 → WorkspaceState。

    将 ViewModel 层的消息契约转换为 Shell 层的 Workspace 状态。
    不包含 UI 渲染信息——由具体 Shell 实现负责渲染。
    """
    ws_messages = [
        WorkspaceMessage(
            id=m.id,
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls,
        )
        for m in (messages or [])
    ]
    return WorkspaceState(
        title=title,
        subtitle=subtitle,
        messages=ws_messages,
        models=models or [],
    )
