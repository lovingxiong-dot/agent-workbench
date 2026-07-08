"""agent_workbench/ui/workspace.py — Workspace 抽象基类。

Workspace 是 Workbench 中间区域的独立视图单元（Chat / Skill / Tool / Provider / ...）。
它继承 QWidget，并声明生命周期钩子，供 WorkspaceRouter 统一调度。
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget


class Workspace(QWidget):
    """Workbench Workspace 基类。

    子类必须提供:
    - workspace_id: str — 唯一标识
    - title: str — 显示标题
    - icon: str — 图标/表情符号

    子类可重写生命周期钩子以处理激活/失活/关闭事件。
    """

    workspace_id: str = ""
    title: str = ""
    icon: str = ""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def on_activate(self) -> None:
        """Workspace 被切换到前台时调用。"""
        pass

    def on_deactivate(self) -> None:
        """Workspace 离开前台时调用。"""
        pass

    def on_close(self) -> None:
        """Workbench 关闭或 Workspace 被注销时调用。"""
        pass
