"""
right_panel.py — v4 右栏面板

包含：
- TerminalWidget：集成 TerminalWorker 的命令终端
- FileReaderWidget：文本文件读取/编辑器
- BrowserWidget：基于 QWebEngineView 的嵌入式浏览器
- RightPanelWidget：「v4 架构 / 终端 / 文件编辑器 / 浏览器」四标签页容器

样式全部从外部 theme dict 读取，支持深色/浅色即时切换。
"""
import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QLineEdit, QPushButton, QTabWidget, QLabel, QFileDialog,
    QSizePolicy, QApplication,
)
from PySide6.QtCore import Qt, Signal, QUrl, QSize
from PySide6.QtGui import QFont, QColor

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    _WEBENGINE_AVAILABLE = True
except Exception:
    _WEBENGINE_AVAILABLE = False

from .icons import svg_icon
from workers.terminal_worker import TerminalWorker
from ui.widgets.explorer import ProjectExplorer


DEFAULT_THEME = "dark"


class TerminalWidget(QWidget):
    """命令终端：显示输出 + 输入命令 + 运行/停止。"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._worker: Optional[TerminalWorker] = None
        self._cwd = os.getcwd()
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 输出区
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setFont(QFont("Cascadia Code", 10))
        self.output_edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        layout.addWidget(self.output_edit, 1)

        # 命令输入行
        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(8)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("输入命令并回车执行...")
        self.cmd_input.returnPressed.connect(self._on_run_command)
        cmd_row.addWidget(self.cmd_input, 1)

        self.run_btn = QPushButton("运行")
        self.run_btn.setFixedWidth(56)
        self.run_btn.setCursor(Qt.PointingHandCursor)
        self.run_btn.clicked.connect(self._on_run_command)
        cmd_row.addWidget(self.run_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedWidth(56)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.stop)
        cmd_row.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("清空")
        self.clear_btn.setFixedWidth(56)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear)
        cmd_row.addWidget(self.clear_btn)

        layout.addLayout(cmd_row)

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_primary']};")
        self.output_edit.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {t['bg_input']}; color: {t['text_primary']}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; padding: 8px; }}"
        )
        btn_style = (
            f"QPushButton {{ background-color: {t['tag_bg']}; color: {t['tag_text']}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
        )
        self.run_btn.setStyleSheet(btn_style)
        self.stop_btn.setStyleSheet(btn_style)
        self.clear_btn.setStyleSheet(btn_style)
        self.cmd_input.setStyleSheet(
            f"QLineEdit {{ background-color: {t['bg_input']}; color: {t['text_primary']}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
        )

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()

    def set_cwd(self, cwd: str):
        self._cwd = cwd or os.getcwd()

    def run_command(self, command: str, cwd: str = ""):
        if not command or not command.strip():
            return
        if self._worker and self._worker.isRunning():
            return
        self.append_output(f"$ {command}")
        self.cmd_input.clear()
        self.stop_btn.setVisible(True)
        self.run_btn.setEnabled(False)
        self._worker = TerminalWorker(command, cwd or self._cwd)
        self._worker.output.connect(self.append_output)
        self._worker.finished_cmd.connect(self._on_command_finished)
        self._worker.start()

    def _on_run_command(self):
        cmd = self.cmd_input.text().strip()
        if cmd:
            self.run_command(cmd)

    def _on_command_finished(self, code: int):
        self.append_output(f"[退出码: {code}]")
        self.stop_btn.setVisible(False)
        self.run_btn.setEnabled(True)
        self._worker = None

    def append_output(self, text: str):
        self.output_edit.appendPlainText(text)
        scrollbar = self.output_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        self.output_edit.clear()

    def stop(self):
        if self._worker:
            self._worker.stop()
            self._worker = None
        self.stop_btn.setVisible(False)
        self.run_btn.setEnabled(True)


class FileReaderWidget(QWidget):
    """文本文件读取/编辑器。"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._current_path = ""
        self._max_size = 1024 * 1024  # 1MB
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 文件路径行
        path_row = QHBoxLayout()
        path_row.setSpacing(8)

        self.path_label = QLabel("未打开文件")
        self.path_label.setWordWrap(True)
        self.path_label.setFont(QFont("Segoe UI", 10))
        path_row.addWidget(self.path_label, 1)

        self.open_btn = QPushButton("打开...")
        self.open_btn.setFixedWidth(64)
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.clicked.connect(self._on_open_file_dialog)
        path_row.addWidget(self.open_btn)

        layout.addLayout(path_row)

        # 编辑器
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Cascadia Code", 10))
        self.editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        layout.addWidget(self.editor, 1)

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_primary']};")
        self.editor.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {t['bg_input']}; color: {t['text_primary']}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; padding: 8px; }}"
        )
        self.path_label.setStyleSheet(f"color: {t['text_secondary']};")
        self.open_btn.setStyleSheet(
            f"QPushButton {{ background-color: {t['tag_bg']}; color: {t['tag_text']}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
        )

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()

    def _on_open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件")
        if path:
            self.open_file(path)

    def open_file(self, path: str):
        if not path or not os.path.isfile(path):
            self.editor.setPlainText(f"[文件不存在] {path}")
            return
        self._current_path = path
        self.path_label.setText(path)
        try:
            size = os.path.getsize(path)
            if size > self._max_size:
                with open(path, "rb") as f:
                    raw = f.read(self._max_size)
                text = self._decode(raw)
                self.editor.setPlainText(
                    text + f"\n\n[文件过大，仅显示前 {self._max_size // 1024}KB]"
                )
            else:
                with open(path, "rb") as f:
                    raw = f.read()
                self.editor.setPlainText(self._decode(raw))
        except Exception as e:
            self.editor.setPlainText(f"[读取失败] {e}")

    def set_content(self, content: str):
        self.editor.setPlainText(content)

    @staticmethod
    def _decode(raw: bytes) -> str:
        for encoding in ("utf-8", "gbk", "gb2312", "latin1"):
            try:
                return raw.decode(encoding)
            except Exception:
                continue
        return raw.decode("utf-8", errors="replace")


class BrowserWidget(QWidget):
    """嵌入式浏览器（基于 QWebEngineView）。"""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._home_url = "https://www.bing.com"
        self._setup_ui()
        self._apply_theme()
        if _WEBENGINE_AVAILABLE:
            self.load_url(self._home_url)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        if not _WEBENGINE_AVAILABLE:
            layout.addWidget(QLabel("当前环境未安装 PySide6 WebEngine，浏览器不可用。"))
            return

        # 地址栏
        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)

        self.back_btn = QPushButton()
        self.back_btn.setFixedSize(28, 28)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.setIconSize(QSize(16, 16))
        self.back_btn.setToolTip("后退")
        self.back_btn.clicked.connect(self._on_back)
        nav_row.addWidget(self.back_btn)

        self.forward_btn = QPushButton()
        self.forward_btn.setFixedSize(28, 28)
        self.forward_btn.setCursor(Qt.PointingHandCursor)
        self.forward_btn.setIconSize(QSize(16, 16))
        self.forward_btn.setToolTip("前进")
        self.forward_btn.clicked.connect(self._on_forward)
        nav_row.addWidget(self.forward_btn)

        self.refresh_btn = QPushButton()
        self.refresh_btn.setFixedSize(28, 28)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setIconSize(QSize(16, 16))
        self.refresh_btn.setToolTip("刷新")
        self.refresh_btn.clicked.connect(self._on_refresh)
        nav_row.addWidget(self.refresh_btn)

        self.home_btn = QPushButton()
        self.home_btn.setFixedSize(28, 28)
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.setIconSize(QSize(16, 16))
        self.home_btn.setToolTip("主页")
        self.home_btn.clicked.connect(self._on_home)
        nav_row.addWidget(self.home_btn)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("输入网址...")
        self.url_input.returnPressed.connect(self._on_navigate)
        nav_row.addWidget(self.url_input, 1)

        self.go_btn = QPushButton("Go")
        self.go_btn.setFixedWidth(44)
        self.go_btn.setCursor(Qt.PointingHandCursor)
        self.go_btn.clicked.connect(self._on_navigate)
        nav_row.addWidget(self.go_btn)

        layout.addLayout(nav_row)

        # 浏览器视图
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_load_finished)
        self.web_view.urlChanged.connect(self._on_url_changed)
        layout.addWidget(self.web_view, 1)

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_primary']};")
        if not _WEBENGINE_AVAILABLE:
            return
        btn_style = (
            f"QPushButton {{ background-color: {t['tag_bg']}; color: {t['tag_text']}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
        )
        icon_color = t.get("text_secondary", "#a0a0b0")
        self.back_btn.setStyleSheet(btn_style)
        self.back_btn.setIcon(svg_icon("arrow-left", icon_color, 16))
        self.forward_btn.setStyleSheet(btn_style)
        self.forward_btn.setIcon(svg_icon("arrow-right", icon_color, 16))
        self.refresh_btn.setStyleSheet(btn_style)
        self.refresh_btn.setIcon(svg_icon("refresh", icon_color, 16))
        self.home_btn.setStyleSheet(btn_style)
        self.home_btn.setIcon(svg_icon("home", icon_color, 16))
        self.go_btn.setStyleSheet(btn_style)
        self.url_input.setStyleSheet(
            f"QLineEdit {{ background-color: {t['bg_input']}; color: {t['text_primary']}; "
            f"border: 1px solid {t['border']}; border-radius: 6px; padding: 4px 8px; font-size: 12px; }}"
        )

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()

    def set_home_page(self, url: str):
        self._home_url = url

    def load_url(self, url: str):
        if not _WEBENGINE_AVAILABLE:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.web_view.setUrl(QUrl(url))
        self.url_input.setText(url)

    def load_html(self, html: str):
        if not _WEBENGINE_AVAILABLE:
            return
        self.web_view.setHtml(html)

    def _on_navigate(self):
        self.load_url(self.url_input.text().strip())

    def _on_back(self):
        if _WEBENGINE_AVAILABLE:
            self.web_view.back()

    def _on_forward(self):
        if _WEBENGINE_AVAILABLE:
            self.web_view.forward()

    def _on_refresh(self):
        if _WEBENGINE_AVAILABLE:
            self.web_view.reload()

    def _on_home(self):
        self.load_url(self._home_url)

    def _on_load_finished(self, ok: bool):
        if not ok:
            self.web_view.setHtml("<h3>页面加载失败</h3>")

    def _on_url_changed(self, url: QUrl):
        self.url_input.setText(url.toString())


class RecentFilesList(QWidget):
    """最近文件列表：路径 + 相对时间。"""

    file_clicked = Signal(str)

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._files: list[tuple[str, str]] = []  # (path, time_label)
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(0)

        # 标题
        self.header = QLabel("最近文件")
        self.header.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.header)

        # 文件列表容器
        self.list_container = QVBoxLayout()
        self.list_container.setSpacing(0)
        layout.addLayout(self.list_container)
        layout.addStretch()

    def _apply_theme(self):
        t = self._theme
        self.setStyleSheet(f"background-color: {t['bg_primary']};")
        self.header.setStyleSheet(
            f"color: {t.get('text_muted', t['text_secondary'])}; "
            f"font-size: 9px; font-weight: 600; letter-spacing: 0.5px; "
            f"padding: 0 0 4px 0;"
        )

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()

    def set_files(self, files: list[tuple[str, str]]):
        """设置文件列表 [(path, time_label), ...]"""
        self._files = files
        # 清空旧项
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        t = self._theme
        for path, time_label in files:
            row = QWidget()
            row.setFixedHeight(24)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)

            name_label = QLabel(path)
            name_label.setFont(QFont("Segoe UI", 11))
            name_label.setStyleSheet(f"color: {t['text_primary']}; border: none; background: transparent;")

            time_label_w = QLabel(time_label)
            time_label_w.setFont(QFont("Segoe UI", 9))
            time_label_w.setStyleSheet(f"color: {t.get('text_muted', t['text_secondary'])}; border: none; background: transparent;")
            time_label_w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # SVG: row background fill=#16213e stroke=#2a2a4a rx=4
            row.setStyleSheet(
                f"QWidget {{ background-color: {t['bg_sidebar']}; "
                f"border: 0.5px solid {t['border']}; border-radius: 4px; }}"
            )

            row_layout.addWidget(name_label, 1)
            row_layout.addWidget(time_label_w)
            self.list_container.addWidget(row)

    def add_file(self, path: str):
        """追加一个文件到列表顶部。"""
        import time
        now = time.strftime("%H:%M")
        self._files.insert(0, (path, now))
        self.set_files(self._files[:20])


class RightPanelWidget(QWidget):
    """右栏容器：v4 架构 / 终端 / 文件编辑器 / 浏览器，标签栏对齐 SVG。"""

    file_open_requested = Signal(str)

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._theme = theme
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 自定义标签栏 ──
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(28)
        tab_layout = QHBoxLayout(self._tab_bar)
        tab_layout.setContentsMargins(8, 2, 8, 2)
        tab_layout.setSpacing(2)

        # + 新建标签按钮（r=7 → d=14）
        self._add_tab_btn = QPushButton("+")
        self._add_tab_btn.setFixedSize(14, 14)
        self._add_tab_btn.setCursor(Qt.PointingHandCursor)
        self._add_tab_btn.setToolTip("新建标签")

        # 标签按钮列表 [(btn, close_btn, widget)]
        self._tab_buttons: list[tuple[QPushButton, QPushButton, QWidget]] = []

        # 搜索按钮
        self._search_right_btn = QPushButton()
        self._search_right_btn.setFixedSize(16, 16)
        self._search_right_btn.setCursor(Qt.PointingHandCursor)
        self._search_right_btn.setToolTip("搜索文件")
        self._search_right_btn.setText("🔍")

        tab_layout.addWidget(self._add_tab_btn)
        self._tab_btn_container = QHBoxLayout()
        self._tab_btn_container.setSpacing(2)
        tab_layout.addLayout(self._tab_btn_container, 1)
        tab_layout.addWidget(self._search_right_btn)
        layout.addWidget(self._tab_bar)

        # 分隔线
        sep = QLabel()
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        self._tab_sep = sep

        # ── 内容区（QStackedWidget 简化：直接 QTabWidget 保留）──
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        self.tabs.tabBar().hide()  # 隐藏原生标签栏，用自定义的
        layout.addWidget(self.tabs, 1)

        # 搜索按钮（右侧角落，用于原生标签兼容）
        self.search_corner_btn = QPushButton()
        self.search_corner_btn.setFixedSize(16, 16)
        self.search_corner_btn.setCursor(Qt.PointingHandCursor)
        self.search_corner_btn.setToolTip("搜索文件")
        self.search_corner_btn.setText("🔍")
        self.tabs.setCornerWidget(self.search_corner_btn, Qt.TopRightCorner)

        # v4 架构（含项目资源管理器 + 最近文件）
        self._v4_tab = QWidget()
        v4_layout = QVBoxLayout(self._v4_tab)
        v4_layout.setContentsMargins(0, 0, 0, 0)
        v4_layout.setSpacing(0)
        self.explorer = ProjectExplorer(project_root="", storage_dir="", parent=self)
        self.explorer.file_selected.connect(self._on_file_selected)
        self._recent_files = RecentFilesList(self._theme)
        v4_layout.addWidget(self.explorer, 3)
        v4_layout.addWidget(self._recent_files, 1)
        self._add_tab("v4 架构", self._v4_tab)

        # 终端
        self.terminal = TerminalWidget(self._theme, parent=self)
        self._add_tab("终端", self.terminal)

        # 文件编辑器
        self.file_reader = FileReaderWidget(self._theme, parent=self)
        self._add_tab("文件编辑器", self.file_reader)

        # 浏览器
        self.browser = BrowserWidget(self._theme, parent=self)
        self._add_tab("浏览器", self.browser)

        # 默认选中第一个
        self._on_tab_button_clicked(0)

    def _add_tab(self, title: str, widget: QWidget) -> int:
        idx = self.tabs.addTab(widget, title)
        # 创建自定义标签按钮
        btn = QPushButton(title)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(24)
        btn.clicked.connect(lambda: self._on_tab_button_clicked(
            self._tab_buttons.index(next((t for t in self._tab_buttons if t[2] is widget), (None, None, None)))))
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(10, 10)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setToolTip("关闭标签")
        close_btn.clicked.connect(lambda: self._on_custom_tab_close(
            self._tab_buttons.index(next((t for t in self._tab_buttons if t[2] is widget), (None, None, None)))))

        self._tab_buttons.append((btn, close_btn, widget))
        self._tab_btn_container.addWidget(btn)
        self._tab_btn_container.addWidget(close_btn)
        self._apply_tab_btn_styles()
        return idx

    def _on_tab_button_clicked(self, idx: int):
        if 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(idx)
            for i, (btn, _, _) in enumerate(self._tab_buttons):
                btn.setChecked(i == idx)

    def _on_custom_tab_close(self, idx: int):
        self._on_tab_close_requested(idx)

    def _on_tab_close_requested(self, index: int):
        if self.tabs.count() <= 1 or index == 0:
            return
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget and widget not in (self._v4_tab, self.terminal, self.file_reader, self.browser):
            widget.deleteLater()
        # 移除自定义标签
        if 0 <= index < len(self._tab_buttons):
            btn, close_btn, _ = self._tab_buttons.pop(index)
            self._tab_btn_container.removeWidget(btn)
            self._tab_btn_container.removeWidget(close_btn)
            btn.deleteLater()
            close_btn.deleteLater()

    def _apply_tab_btn_styles(self):
        t = self._theme
        active_bg = t["bg_primary"]
        inactive_bg = t.get("bg_right_tab", "#0f1729")
        for i, (btn, close_btn, _) in enumerate(self._tab_buttons):
            is_current = (i == self.tabs.currentIndex())
            bg = active_bg if is_current else inactive_bg
            text_color = t["text_primary"] if is_current else t["text_secondary"]
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {text_color}; "
                f"border: none; border-radius: 6px; padding: 2px 10px; "
                f"font-size: 10px; font-weight: {'600' if is_current else '400'}; text-align: left; }}"
                f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
                f"QPushButton:checked {{ background-color: {active_bg}; color: {t['text_primary']}; "
                f"font-weight: 600; }}"
            )
            close_btn.setStyleSheet(
                f"QPushButton {{ background-color: {'#1a1a2e' if is_current else t.get('bg_right_tab', '#0f1729')}; "
                f"color: {t['text_muted']}; border: none; border-radius: 6px; font-size: 9px; }}"
                f"QPushButton:hover {{ background-color: {t['bg_hover']}; }}"
            )

    def _apply_theme(self):
        t = self._theme
        bg_right = t.get("bg_right", "#0f1729")
        self.setStyleSheet(f"background-color: {bg_right};")
        self._tab_bar.setStyleSheet(f"background-color: {bg_right};")
        self._tab_sep.setStyleSheet(f"background-color: {t['border']};")

        self.tabs.setStyleSheet(
            f"QTabWidget::pane {{ border: none; background-color: {bg_right}; }}"
        )
        self._add_tab_btn.setStyleSheet(
            f"QPushButton {{ background-color: {t['bg_hover']}; color: {t['text_secondary']}; "
            f"border: none; border-radius: 7px; font-size: 10px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {t['bg_selected']}; }}"
        )
        self._search_right_btn.setStyleSheet(
            f"QPushButton {{ background-color: {t['bg_hover']}; color: {t['text_secondary']}; "
            f"border-radius: 3px; font-size: 9px; border: none; }}"
        )
        self._apply_tab_btn_styles()
        self.search_corner_btn.setStyleSheet(
            f"QPushButton {{ background-color: {t['bg_hover']}; color: {t['text_secondary']}; "
            f"border-radius: 3px; font-size: 9px; }}"
        )

    def set_theme(self, theme: dict):
        self._theme = theme
        self._apply_theme()
        self._recent_files.set_theme(theme)
        self.terminal.set_theme(theme)
        self.file_reader.set_theme(theme)
        self.browser.set_theme(theme)

    def set_project_root(self, path: str):
        self.explorer.set_project_root(path)

    def set_storage_dir(self, path: str):
        self.explorer.set_storage_dir(path)

    def set_recent_projects(self, projects: list):
        self.explorer.set_recent_projects(projects)

    def set_open_documents(self, documents: list):
        self.explorer.set_open_documents(documents)
        # 同步到最近文件
        files = [(d, "——") for d in documents[:15]]
        self._recent_files.set_files(files)

    def switch_tab(self, tab_name: str):
        name_map = {
            "v4 架构": 0,
            "终端": 1,
            "文件编辑器": 2,
            "文件读取器": 2,
            "浏览器": 3,
        }
        idx = name_map.get(tab_name, -1)
        if idx >= 0:
            self.tabs.setCurrentIndex(idx)
            self._on_tab_button_clicked(idx)

    def open_file(self, path: str):
        self.switch_tab("文件编辑器")
        self.file_reader.open_file(path)
        self._recent_files.add_file(path)

    def update_terminal(self, text: str):
        self.switch_tab("终端")
        self.terminal.append_output(text)

    def run_terminal_command(self, command: str, cwd: str = ""):
        self.switch_tab("终端")
        self.terminal.run_command(command, cwd)

    def load_url(self, url: str):
        self.switch_tab("浏览器")
        self.browser.load_url(url)

    def _on_file_selected(self, path: str):
        self.open_file(path)
        self.file_open_requested.emit(path)
