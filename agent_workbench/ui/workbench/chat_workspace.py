"""agent_workbench/ui/workbench/chat_workspace.py — Chat WorkspaceItem。

职责：
- 作为 WorkspaceHost 中的一个 WorkspaceItem 显示对话内容。
- 只负责渲染，不处理输入（输入由 Workbench CommandBar 负责）。
- 支持用户消息、AI 消息、流式输出、工具结果、系统卡片。

设计来源：复用 v6.ui.chat_scene 的渲染能力，但剥离 Header 和 InputArea，
使其符合 WorkspaceItem 的被动视图定位。
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView, QVBoxLayout, QWidget

from v6.ui.base import C
from v6.ui.chat_scene import ChatScene


class ChatWorkspaceItem(QWidget):
    """聊天工作区：只负责展示消息历史与流式输出。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._scene = ChatScene(self)
        self._view = QGraphicsView(self._scene, self)
        self._view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._view.setStyleSheet(f"background-color: {C['bg_primary']}; border: none;")
        self._layout.addWidget(self._view, 1)

        self._stream_item = None

    def append_user(self, text: str) -> None:
        """追加用户消息。"""
        self._scene.add_user_message(text)
        self._scroll_to_bottom()

    def append_ai(self, text: str, phase: str = "") -> None:
        """追加 AI 消息。"""
        self._stream_item = self._scene.add_ai_message(text, phase)
        self._scroll_to_bottom()

    def stream_chunk(self, text: str) -> None:
        """追加流式片段。"""
        if self._stream_item is None:
            self._stream_item = self._scene.add_ai_message("")
        if hasattr(self._stream_item, "_raw"):
            self._stream_item._raw += text
            self._stream_item.refresh_theme()
        self._scroll_to_bottom()

    def stream_end(self) -> None:
        """结束当前流式消息。"""
        self._stream_item = None

    def set_streaming(self, streaming: bool) -> None:
        """设置流式状态（占位，未来可显示输入指示器）。"""
        pass

    def tool_executed(self, name: str, result: dict, status: str = "ok", elapsed_ms: int = 0) -> None:
        """显示工具执行结果。"""
        self._scene.add_tool(name, result, status)
        self._scroll_to_bottom()

    def confirm_required(self, tool: str, command: str) -> None:
        """显示确认请求。"""
        self._scene.add_system_card("确认请求", f"{tool}: {command}")
        self._scroll_to_bottom()

    def set_title(self, title: str, subtitle: str = "") -> None:
        """设置工作区标题（占位，未来可在 WorkspaceHost tab 显示）。"""
        pass

    def clear_chat(self) -> None:
        """清空聊天。"""
        self._scene.clear_chat()
        self._stream_item = None

    def _scroll_to_bottom(self) -> None:
        scrollbar = self._view.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._scene.set_width(max(self._view.viewport().width(), 200))
