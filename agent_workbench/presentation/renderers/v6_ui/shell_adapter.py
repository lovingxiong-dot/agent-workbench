"""presentation/renderers/v6_ui/shell_adapter.py — 状态流适配器。

V6UIShellAdapter 实现 ShellProtocol（duck typing），
将 ShellContract 数据模型映射到 v6/ui 纯 UI 组件公共 API。

约束：
  ✓ 只引用 ShellContract 数据模型 + v6/ui 组件公共 API
  ✗ 不引用 Runtime Implementation（engine, executor, session, llm, tool）
  ✗ 不 import PySide6（v6/ui 组件内部处理）
  ✗ 不 import WorkbenchUIController
  ✗ 不穿透 v6/ui 私有成员（使用 ChatArea.reset_workspace() 而非 _scene.clear_chat()）
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from agent_workbench.presentation.shell.protocol import (
    NavigationGroup,
    NavigationItem,
    WorkspaceState,
    WorkspaceMessage,
    InspectorState,
    CommandState,
)

if TYPE_CHECKING:
    from v6.ui.chat_area import ChatArea
    from v6.ui.left_panel import LeftPanel
    from v6.ui.right_panel import RightPanel


class V6UIShellAdapter:
    """ShellContract → v6/ui 组件公共 API 映射。

    实现 ShellProtocol 的 4 个方法（duck typing），
    每个方法将 OS 级抽象模型翻译为 v6/ui 组件的具体数据格式。
    """

    def __init__(
        self,
        left_panel: "LeftPanel",
        chat_area: "ChatArea",
        right_panel: "RightPanel",
    ) -> None:
        self._left = left_panel
        self._chat = chat_area
        self._right = right_panel

    # ═══════════════════════════════════════════════════════════════
    # ShellProtocol 实现
    # ═══════════════════════════════════════════════════════════════

    def update_navigation(self, groups: list[NavigationGroup]) -> None:
        """NavigationGroup[] → LeftPanel.update_sessions()。

        ShellContract 格式：
          NavigationGroup(id, title, [NavigationItem(id, title, preview, ...)])

        v6/ui LeftPanel 期望格式：
          [(group_id, group_title, [{"sid": str, "title": str, "preview": str, "time": str}, ...])]
        """
        sessions_data = []
        for group in groups:
            items = [
                {
                    "sid": item.id,
                    "title": item.title,
                    "preview": item.preview,
                    "time": "",
                    "icon": "",
                    "summary": "",
                    "pinned": False,
                }
                for item in group.items
            ]
            sessions_data.append((group.id, group.title, items))
        self._left.update_sessions(sessions_data)

    def update_workspace(self, state: WorkspaceState) -> None:
        """WorkspaceState → ChatArea 完整更新。

        使用 ChatArea.reset_workspace() 公共 API（非 _scene.clear_chat()）。
        """
        # 标题
        self._chat.set_title(state.title, state.subtitle)

        # 清空现有消息并重建
        self._chat.reset_workspace()

        for msg in state.messages:
            if msg.role == "user":
                self._chat.append_user(msg.content)
            elif msg.role == "assistant":
                self._chat.append_ai(msg.content)
            elif msg.role == "tool":
                self._chat.tool_executed(
                    msg.id, {"content": msg.content}, "ok"
                )

    def update_inspector(self, state: InspectorState) -> None:
        """InspectorState → RightPanel 更新。

        根据 properties 中的 type 字段决定显示方式：
        - "file" → RightPanel.show_file()
        - "terminal" → RightPanel.append_terminal()
        """
        if not state.object_id:
            return
        for prop in state.properties:
            prop_type = prop.get("type", "")
            if prop_type == "file":
                self._right.show_file(prop.get("value", ""))
            elif prop_type == "terminal":
                self._right.append_terminal(prop.get("value", ""))

    def update_command(self, state: CommandState) -> None:
        """CommandState → 状态栏更新（Phase 2-C 实现）。"""
        pass