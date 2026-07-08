"""agent_workbench/ui/workbench/host_base.py — Workbench Area Host 基类。

设计边界：
- Host 是 Workbench 内部固定区域的容器，负责 mount / replace / dispose 生命周期。
- Host 不实现具体业务 UI；业务内容作为 content widget 被挂载到 Host 中。
- WorkbenchUIController 只依赖 Host 接口，不直接依赖 Qt Widget 内部实现。
"""
from __future__ import annotations

from PySide6.QtWidgets import QLayout, QVBoxLayout, QWidget


class WorkbenchAreaHost(QWidget):
    """Workbench 区域 Host 基类。

    子类应提供面向业务的稳定 API，并在内部将操作委托给当前挂载的 content widget。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._content: QWidget | None = None
        self._layout: QLayout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def mount(self, content: QWidget) -> None:
        """首次挂载内容。"""
        self._set_content(content)

    def replace(self, content: QWidget) -> None:
        """替换当前内容，旧内容会被 dispose。"""
        self._set_content(content)

    def dispose(self) -> None:
        """释放当前内容。"""
        if self._content is None:
            return
        self._content.setParent(None)
        self._content.deleteLater()
        self._content = None

    @property
    def content(self) -> QWidget | None:
        """当前挂载的内容 widget（仅用于 Host 内部或测试断言，不建议 UI Controller 直接使用）。"""
        return self._content

    def _set_content(self, content: QWidget) -> None:
        """设置内容 widget，旧内容会先被释放。"""
        self.dispose()
        self._content = content
        self._layout.addWidget(content)
