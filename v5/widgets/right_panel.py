"""V5 右侧面板组件。"""
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPixmap
from .base import theme, V5_THEMES, C, font, svg_icon
from .terminal_widget import TerminalWidget
from .file_reader_widget import FileReaderWidget
from .browser_widget import BrowserWidget

# ══════════════════════════════════════════════════════════════
# 右栏（400px）
# ══════════════════════════════════════════════════════════════

class TabButton(QWidget):
    """右栏标签按钮：标签文本与关闭圆钮共用同一背景，实现 SVG 中的透明圆框高亮效果。
       SVG: rect rx=6 h=24; close circle r=5 fill=tab_bg 与标签同色。
    """
    clicked = Signal()
    close_clicked = Signal()

    def __init__(self, text: str, width: int, active: bool = False, closable: bool = True, parent=None):
        super().__init__(parent)
        self._text = text
        self._active = active
        self._closable = closable
        self.setMinimumWidth(30)  # 可被压缩，仅保留关闭/文本最小空间
        self.setMaximumHeight(24)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()
        theme.changed.connect(self._refresh_style)

    def _setup_ui(self):
        self._lbl = QLabel(self._text, self)
        self._lbl.setFont(font(10))
        self._lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._lbl.setStyleSheet("background: transparent;")

        if self._closable:
            self._close = QPushButton("✕", self)
            self._close.setFixedSize(10, 10)
            self._close.setFont(font(9))
            self._close.setCursor(Qt.PointingHandCursor)
            self._close.clicked.connect(self.close_clicked.emit)
        else:
            self._close = None
        self._update_child_geometry()
        self._refresh_style()

    def _update_child_geometry(self):
        w = self.width()
        self._lbl.setGeometry(10, 0, max(10, w - 28), 24)
        if self._close:
            self._close.setGeometry(max(4, w - 17), 7, 10, 10)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_child_geometry()

    def _refresh_style(self):
        is_dark = theme.name == "dark"
        bg = (C["bg_darker"] if is_dark else C["bg_card"]) if self._active else (C["bg_right"] if is_dark else C["bg_darker"])
        fg = C["text_primary"] if self._active else C["text_secondary"]
        fw = 600 if self._active else 500
        self.setStyleSheet(f"TabButton {{ background-color: {bg}; border-radius: 6px; }}")
        self._lbl.setStyleSheet(f"color: {fg}; background: transparent; font-weight: {fw};")
        if self._close:
            self._close.setStyleSheet(
                f"QPushButton {{ background-color: {bg}; color: {C['text_muted']}; "
                f"border-radius: 5px; font-size: 9px; border: none; }}"
                f"QPushButton:hover {{ color: {C['text_primary']}; }}"
            )

    def text(self) -> str:
        return self._text

    def set_active(self, active: bool):
        self._active = active
        self._refresh_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._close is None or not self._close.geometry().contains(event.pos()):
                self.clicked.emit()
        super().mousePressEvent(event)


class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 宽度由外部 QSplitter 控制（MainWindow 中设置 min）
        self._active_tab = 0
        self._recent_files: list[tuple[str, datetime]] = []
        self._setup_ui()
        self.setMinimumWidth(120)
        theme.changed.connect(self._refresh_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 标签栏（SVG dark h=28 fill=#0f1729; light fill=#f1f3f5）──
        self._tab_bar = QWidget()
        self._tab_bar.setFixedHeight(28)
        tb_layout = QHBoxLayout(self._tab_bar)
        tb_layout.setContentsMargins(8, 2, 0, 2)
        tb_layout.setSpacing(0)

        # 标签 + 搜索区域（可随右侧栏宽度压缩/拉伸）
        self._tab_container = QWidget()
        self._tab_container.setMinimumWidth(1)
        self._tab_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        tc_layout = QHBoxLayout(self._tab_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(2)

        # SVG: add btn circle r=7 (d=14) fill=#2a2a4a / #e9ecef
        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(14, 14)
        self._add_btn.setCursor(Qt.PointingHandCursor)
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border-radius: 7px; font-size: 10px; font-weight: 500; border: none; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        tc_layout.addWidget(self._add_btn)

        # 标签按钮（宽度可随容器伸缩）
        tab_defs = [("架构", 86, False), ("终端", 74, True), ("文件编辑器", 100, True), ("浏览器", 74, True)]
        self._tab_btns: list[TabButton] = []
        for i, (name, width, closable) in enumerate(tab_defs):
            btn = TabButton(name, width, active=(i == 0), closable=closable)
            btn.clicked.connect(lambda idx=i: self._switch_tab(idx))
            btn.close_clicked.connect(lambda idx=i: self._on_close_tab(idx))
            tc_layout.addWidget(btn, 1)  # 允许拉伸/压缩
            self._tab_btns.append(btn)

        # SVG: 搜索按钮 x=930 y=6 w=16 h=16 rx=3 fill=#2a2a4a / #e9ecef
        self._search_btn = QPushButton("🔍")
        self._search_btn.setFixedSize(16, 16)
        self._search_btn.setCursor(Qt.PointingHandCursor)
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {C['text_secondary']}; "
            f"border: none; border-radius: 3px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        tc_layout.addSpacing(4)
        tc_layout.addWidget(self._search_btn)

        tb_layout.addWidget(self._tab_container, 1)

        # 窗口控制按钮容器（固定在最右侧，不被拖拽收窄/隐藏）
        self._win_btns = QWidget()
        self._win_btns.setFixedWidth(92)  # 3×28 + 2×2 + 左右留白
        win_hl = QHBoxLayout(self._win_btns)
        win_hl.setContentsMargins(0, 0, 8, 0)
        win_hl.setSpacing(2)
        win_hl.addStretch()
        self._win_hl = win_hl
        tb_layout.addWidget(self._win_btns)

        layout.addWidget(self._tab_bar)

        # 标签栏下分隔线
        self._sep = QFrame()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f"background-color: {C['border']};")
        layout.addWidget(self._sep)

        # ── 内容区（QStackedWidget）──
        self._stack = QStackedWidget()

        # Tab0: 架构（最近文件）
        self._tab0 = QWidget()
        self._tab0_layout = QVBoxLayout(self._tab0)
        self._tab0_layout.setContentsMargins(16, 8, 16, 8)
        self._tab0_layout.setSpacing(4)

        self._tab0_layout.addWidget(self._make_section_header("最近文件"))
        self._file_rows: list[QWidget] = []
        self._tab0_layout.addStretch()
        self._tab0.setStyleSheet(f"background-color: {C['bg_right']};")
        self._stack.addWidget(self._tab0)

        # Tab1: 终端
        self.terminal = TerminalWidget()
        self._stack.addWidget(self.terminal)

        # Tab2: 文件编辑器
        self.file_reader = FileReaderWidget()
        self._stack.addWidget(self.file_reader)

        # Tab3: 浏览器
        self.browser = BrowserWidget()
        self._stack.addWidget(self.browser)

        layout.addWidget(self._stack, 1)
        self._switch_tab(0)
        self.setStyleSheet(f"background-color: {C['bg_right']};")

        # 初始化默认最近文件（项目根目录下部分源码）
        self._refresh_recent_files()

    def _make_section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {C['text_muted']}; font-size: 9px; font-weight: 600; "
            f"letter-spacing: 0.5px; padding: 0 0 4px 0;"
        )
        return lbl

    def _make_file_row(self, path: str, time_str: str) -> QWidget:
        row = QWidget()
        row.setFixedHeight(24)
        row.setCursor(Qt.PointingHandCursor)
        row.setProperty("file_path", path)
        hl = QHBoxLayout(row)
        hl.setContentsMargins(10, 0, 10, 0)
        hl.setSpacing(8)

        display = os.path.basename(path) if os.path.exists(path) else path
        name_lbl = QLabel(display)
        name_lbl.setFont(font(11))
        name_lbl.setStyleSheet(f"color: {C['text_secondary']}; border: none; background: transparent;")
        hl.addWidget(name_lbl, 1)

        time_lbl = QLabel(time_str)
        time_lbl.setFont(font(9))
        time_lbl.setStyleSheet(f"color: {C['text_muted']}; border: none; background: transparent;")
        time_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hl.addWidget(time_lbl)

        # SVG dark: fill=#16213e stroke=#2a2a4a rx=4; light: fill=#f8f9fa stroke=#dee2e6
        row.setStyleSheet(
            f"QWidget {{ background-color: {C['bg_file_row']}; "
            f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
            f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
        )
        row.mousePressEvent = lambda e, p=path: self._on_recent_file_click(p)
        return row

    def _on_recent_file_click(self, path: str):
        """点击最近文件行：在文件编辑器中打开并切换到该标签。"""
        self.open_file(path)

    def _refresh_recent_files(self):
        """根据 self._recent_files 重建最近文件列表；空时填充项目根目录默认文件。"""
        # 清理旧行（保留标题和 stretch）
        for row in self._file_rows:
            self._tab0_layout.removeWidget(row)
            row.deleteLater()
        self._file_rows.clear()

        entries = list(self._recent_files)
        if not entries:
            # 默认展示项目根目录下可访问的核心文件
            root = os.getcwd()
            candidates = [
                "v5/main_window.py",
                "v5/widgets/right_panel.py",
                "config/config.yaml",
            ]
            for rel in candidates:
                full = os.path.join(root, rel)
                if os.path.isfile(full):
                    entries.append((full, datetime.fromtimestamp(os.path.getmtime(full))))

        for path, ts in entries[:10]:
            time_str = self._format_time_ago(ts)
            row = self._make_file_row(path, time_str)
            # 插入到 stretch 之前
            self._tab0_layout.insertWidget(self._tab0_layout.count() - 1, row)
            self._file_rows.append(row)

    @staticmethod
    def _format_time_ago(ts: datetime) -> str:
        """将时间戳格式化为相对文本。"""
        delta = datetime.now() - ts
        if delta < timedelta(minutes=1):
            return "刚刚"
        if delta < timedelta(hours=1):
            return f"{delta.seconds // 60} 分钟前"
        if delta < timedelta(days=1):
            return f"{delta.seconds // 3600} 小时前"
        if delta < timedelta(days=7):
            return f"{delta.days} 天前"
        return ts.strftime("%m-%d")

    def add_recent_file(self, path: str):
        """添加一条最近文件记录并刷新列表。"""
        if not path or not os.path.isfile(path):
            return
        path = os.path.abspath(path)
        # 去重并置顶
        self._recent_files = [(p, t) for p, t in self._recent_files if p != path]
        self._recent_files.insert(0, (path, datetime.now()))
        self._refresh_recent_files()

    def set_window_buttons(self, minimize_cb, maximize_cb, close_cb):
        """把系统最小化/最大化/关闭按钮嵌入右栏顶部状态栏最右侧，使用SVG图标。"""
        icons = [
            ("M 6 10 L 18 10", minimize_cb),   # 最小化：横线
            # 标准还原框：前后两个重叠矩形
            ("M 7 5 L 16 5 L 16 14 L 7 14 Z M 5 7 L 14 7 L 14 16 L 5 16 Z", maximize_cb),
            ("M 6 6 L 18 18 M 18 6 L 6 18", close_cb),       # 关闭：X
        ]
        for path, cb in icons:
            btn = QPushButton()
            btn.setFixedSize(28, 20)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )
            # 用 QLabel 显示 SVG 路径图标
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="20" viewBox="0 0 24 20">
                <path d="{path}" fill="none" stroke="{C['text_secondary']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
            lbl = QLabel(btn)
            lbl.setPixmap(svg_icon(svg, 24, 20))
            lbl.move(2, 0)
            btn.clicked.connect(cb)
            self._win_hl.addWidget(btn)

    def _switch_tab(self, idx: int):
        self._active_tab = idx
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tab_btns):
            btn.set_active(i == idx)

    def _on_close_tab(self, idx: int):
        # 关闭非首个标签后切回第一个
        if idx > 0 and idx < len(self._tab_btns):
            self._tab_btns[idx].setVisible(False)
            self._switch_tab(0)

    def _refresh_theme(self):
        is_dark = theme.name == "dark"
        tab_bar_bg = C["bg_right"] if is_dark else C["bg_darker"]
        self.setStyleSheet(f"background-color: {C['bg_right']};")
        self._tab_bar.setStyleSheet(f"background-color: {tab_bar_bg};")
        self._sep.setStyleSheet(f"background-color: {C['border']};")
        self._tab0.setStyleSheet(f"background-color: {C['bg_right']};")
        # 子控件已各自连接 theme.changed，此处仅刷新文件行样式
        self._refresh_recent_files()
        icon_fg = C['text_secondary'] if theme.name == "dark" else C['text_label']
        self._add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {icon_fg}; "
            f"border-radius: 7px; font-size: 10px; font-weight: 500; border: none; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        self._search_btn.setStyleSheet(
            f"QPushButton {{ background-color: {C['btn_bg']}; color: {icon_fg}; "
            f"border: none; border-radius: 3px; font-size: 9px; }}"
            f"QPushButton:hover {{ background-color: {C['bg_hover']}; color: {C['text_primary']}; }}"
        )
        for row in self._file_rows:
            row.setStyleSheet(
                f"QWidget {{ background-color: {C['bg_file_row']}; "
                f"border: 0.5px solid {C['border']}; border-radius: 4px; }}"
                f"QWidget:hover {{ background-color: {C['bg_hover']}; }}"
            )
            # 刷新内部 label 颜色
            for child in row.findChildren(QLabel):
                if child.alignment() & Qt.AlignRight:
                    child.setStyleSheet(f"color: {C['text_muted']}; border: none; background: transparent;")
                else:
                    child.setStyleSheet(f"color: {C['text_secondary']}; border: none; background: transparent;")
        # 刷新窗口控制按钮图标颜色
        for btn in self._win_btns.findChildren(QPushButton):
            btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: none; }}"
                f"QPushButton:hover {{ background-color: {C['bg_hover']}; }}"
            )
            lbl = btn.findChild(QLabel)
            if lbl:
                # 重新渲染图标（stroke 颜色更新）
                pass  # 图标在主题切换后颜色不变即可，此处省略重渲染
        self._switch_tab(self._active_tab)

    # ══════════════════════════════════════════════════════════════
    # UIRenderer 桥接 API（P7 真实功能回填）
    # ══════════════════════════════════════════════════════════════

    def open_file(self, path: str):
        """在文件编辑器中打开文件，切换到文件编辑器标签，并加入最近文件。"""
        self.add_recent_file(path)
        self.file_reader.open_file(path)
        self.switch_tab("文件编辑器")

    def update_terminal(self, text: str):
        """向终端追加文本。"""
        self.terminal.append_output(text)

    def switch_tab(self, tab_name: str):
        """根据标签名切换右栏标签页。"""
        for i, btn in enumerate(self._tab_btns):
            if btn.text() == tab_name:
                self._switch_tab(i)
                return

    def load_url(self, url: str):
        """在浏览器标签页加载 URL。"""
        self.browser.load_url(url)
        self.switch_tab("浏览器")

    def set_project_root(self, root: str):
        """设置终端工作目录。"""
        self.terminal.set_cwd(root)
