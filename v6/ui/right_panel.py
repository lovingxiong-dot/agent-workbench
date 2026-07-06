"""v6/ui/right_panel.py — 右栏面板。
设计来源：experiments/ui_template.py（Git 标签 v0.6-alpha）。"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QMenu,
)

from v6.ui.base import C, font, svg_icon
from v6.ui.tab_button import TabButton, TabType
from v6.ui.recent_files import RecentFiles
from v6.ui.terminal_widget import TerminalWidget
from v6.ui.file_reader_widget import FileReaderWidget
from v6.ui.browser_widget import BrowserWidget


class RightPanel(QWidget):
    """右栏面板：标签栏 + 内容堆叠 + 窗口控制按钮。

    信号（遵循 docs/v6/SPEC.md 2.3）：
        open_file(str)         — 请求打开文件
        load_url(str)          — 请求加载 URL
        terminal_command(str)  — 终端执行命令
        tab_closed(str)        — 关闭标签，参数为标签类型
    """

    open_file = Signal(str)
    load_url = Signal(str)
    terminal_command = Signal(str)
    tab_closed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumWidth(180)
        self._active_tab = 0
        self._tab_defs = [
            ("文件", TabType.FILE, 70),
            ("终端", TabType.TERMINAL, 70),
            ("浏览器", TabType.BROWSER, 74),
        ]
        self._tab_btns: list[TabButton] = []
        self._setup_ui()
        self._refresh_theme()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 标签栏 ──
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(32)
        tb_layout = QHBoxLayout(self._tab_bar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(4)

        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(16, 16)
        self._add_btn.setFont(font(10, bold=True))
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border-radius: 8px; font-size: 10px; border: none; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._add_btn.clicked.connect(self._show_add_menu)
        tb_layout.addWidget(self._add_btn)

        for i, (text, tab_type, width) in enumerate(self._tab_defs):
            btn = TabButton(text, tab_type, width=width, active=(i == 0))
            btn.clicked.connect(lambda idx=i: self._switch_tab(idx))
            btn.close_clicked.connect(lambda idx=i: self._close_tab(idx))
            tb_layout.addWidget(btn)
            self._tab_btns.append(btn)

        tb_layout.addStretch()

        # 窗口控制按钮容器（固定显示，不随分栏收窄隐藏）
        self._win_btns = QWidget()
        self._win_hl = QHBoxLayout(self._win_btns)
        self._win_hl.setContentsMargins(0, 0, 0, 0)
        self._win_hl.setSpacing(2)
        tb_layout.addWidget(self._win_btns)

        layout.addWidget(self._tab_bar)

        # 分隔线
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        layout.addWidget(self._sep)

        # ── 内容区 ──
        self._stack = QStackedWidget()

        # 文件页：最近文件 + 文件阅读器
        self._file_page = QStackedWidget()
        self._recent_files = RecentFiles()
        self._recent_files.file_selected.connect(self._on_file_selected)
        self._file_reader = FileReaderWidget()
        self._file_reader.open_requested.connect(self.open_file.emit)
        self._file_page.addWidget(self._recent_files)
        self._file_page.addWidget(self._file_reader)
        self._stack.addWidget(self._file_page)

        # 终端页
        self._terminal = TerminalWidget()
        self._terminal.command_entered.connect(self.terminal_command.emit)
        self._stack.addWidget(self._terminal)

        # 浏览器页
        self._browser = BrowserWidget()
        self._browser.load_requested.connect(self.load_url.emit)
        self._stack.addWidget(self._browser)

        layout.addWidget(self._stack, 1)
        self._switch_tab(0)

    def _switch_tab(self, idx: int) -> None:
        if not (0 <= idx < len(self._tab_btns)):
            return
        self._active_tab = idx
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            btn.set_active(i == idx)

    def _close_tab(self, idx: int) -> None:
        btn = self._tab_btns[idx]
        btn.hide()
        self.tab_closed.emit(btn.tab_type)
        # 若关闭的是当前活动标签，切换到最近一个可见标签
        if self._active_tab == idx:
            for j in range(len(self._tab_btns)):
                if self._tab_btns[j].isVisible():
                    self._switch_tab(j)
                    return

    def _reopen_tab(self, idx: int) -> None:
        self._tab_btns[idx].show()
        self._switch_tab(idx)

    def _show_add_menu(self) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {C['bg_card']}; color: {C['text_primary']}; "
            f"border: 1px solid {C['border']}; border-radius: 6px; padding: 4px; }}"
            f"QMenu::item {{ padding: 6px 16px; border-radius: 4px; }}"
            f"QMenu::item:selected {{ background-color: {C['bg_hover']}; }}"
        )
        for i, (text, tab_type, _) in enumerate(self._tab_defs):
            if not self._tab_btns[i].isVisible():
                action = menu.addAction(text)
                action.triggered.connect(lambda checked=False, idx=i: self._reopen_tab(idx))
        menu.exec(self._add_btn.mapToGlobal(self._add_btn.rect().bottomLeft()))

    def _on_file_selected(self, path: str) -> None:
        self.open_file.emit(path)
        self._file_reader.open_file(path, f"# {path}\n\n[Demo 内容占位]\n")
        self._file_page.setCurrentIndex(1)

    def set_window_buttons(
        self,
        minimize_cb,
        maximize_cb,
        close_cb,
    ) -> None:
        """把系统最小化/最大化/关闭按钮嵌入右栏顶部状态栏最右侧。"""
        icons = [
            ("M 6 10 L 18 10", minimize_cb),
            ("M 7 5 L 16 5 L 16 14 L 7 14 Z M 5 7 L 14 7 L 14 16 L 5 16 Z", maximize_cb),
            ("M 6 6 L 18 18 M 18 6 L 6 18", close_cb),
        ]
        for path, cb in icons:
            btn = QPushButton()
            btn.setFixedSize(28, 20)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )
            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="20" viewBox="0 0 24 20">'
                f'<path d="{path}" fill="none" stroke="{C["text_secondary"]}" stroke-width="1.5" '
                f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
            )
            lbl = QLabel(btn)
            lbl.setPixmap(svg_icon(svg, 24, 20))
            lbl.move(2, 0)
            btn.clicked.connect(cb)
            self._win_hl.addWidget(btn)

    def _refresh_theme(self) -> None:
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._tab_bar.setStyleSheet(f"background-color: {C['bg_right']};")
        self._sep.setStyleSheet(f"background-color: {C['border']};")

    def switch_tab(self, tab_type: str) -> None:
        """外部调用：按标签类型切换。"""
        for i, (_, t, _) in enumerate(self._tab_defs):
            if t == tab_type:
                self._reopen_tab(i)
                return

    def show_file(self, path: str) -> None:
        """在文件阅读器中显示指定文件。"""
        self._reopen_tab(0)
        self._file_reader.open_file(path, f"# {path}\n\n[Demo 内容占位]\n")
        self._file_page.setCurrentIndex(1)

    def append_terminal(self, text: str) -> None:
        """向终端追加输出。"""
        self._terminal.append_output(text)


if __name__ == "__main__":
    import sys

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.resize(500, 400)
    right = RightPanel()
    right.open_file.connect(lambda p: print(f"open file {p}"))
    right.load_url.connect(lambda u: print(f"load url {u}"))
    right.terminal_command.connect(lambda c: print(f"terminal {c}"))
    right.tab_closed.connect(lambda t: print(f"closed {t}"))
    right.set_window_buttons(
        lambda: print("minimize"),
        lambda: print("maximize"),
        lambda: win.close(),
    )
    win.setCentralWidget(right)
    win.show()
    QTimer.singleShot(300, win.close)
    sys.exit(app.exec())
