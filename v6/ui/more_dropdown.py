"""v6/ui/more_dropdown.py — 标题栏「更多」内嵌下拉菜单。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Signal, QPoint
from PySide6.QtWidgets import QApplication

from v6.ui.window_frame import AppleMenu


class MoreDropdown(AppleMenu):
    """更多菜单：导出会话、复制链接、会话设置、开发者工具。"""

    export_requested = Signal()
    copy_link_requested = Signal()
    settings_requested = Signal()
    devtools_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def show_at(self, pos: QPoint) -> None:
        """每次显示前重新构建，确保主题与信号最新。"""
        layout = self.layout()
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
            layout.deleteLater()
        self._items.clear()

        self.add_item("导出会话").clicked.connect(self.export_requested.emit)
        self.add_item("复制链接").clicked.connect(self.copy_link_requested.emit)
        self.add_separator()
        self.add_item("会话设置").clicked.connect(self.settings_requested.emit)
        self.add_item("开发者工具").clicked.connect(self.devtools_requested.emit)

        super().show_at(pos)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
    from PySide6.QtCore import QTimer

    app = QApplication(sys.argv)
    win = QWidget()
    layout = QVBoxLayout(win)
    btn = QPushButton("更多")
    layout.addWidget(btn)
    menu = MoreDropdown(win)
    menu.export_requested.connect(lambda: print("export"))
    menu.settings_requested.connect(lambda: print("settings"))
    btn.clicked.connect(lambda: menu.show_at(btn.mapToGlobal(QPoint(0, btn.height()))))
    win.show()
    QTimer.singleShot(500, win.close)
    sys.exit(app.exec())
