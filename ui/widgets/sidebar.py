import os

from PySide6.QtWidgets import (
    QToolButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeView, QFileSystemModel, QPushButton, QMenu, QFileDialog,
    QAbstractItemView, QFrame,
)
from PySide6.QtCore import Qt, QDir, Signal, QModelIndex
from PySide6.QtGui import QAction, QFont


class SidebarButton(QToolButton):
    def __init__(self, text, tooltip, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.setFixedSize(44, 44)
        self.setCursor(Qt.PointingHandCursor)


class FileTreeWidget(QWidget):
    """资源管理器：支持目录切换、右键菜单、文件选中"""

    file_selected = Signal(str)                 # 用户选中文件
    folder_changed = Signal(str)                # 根目录发生变更
    new_conversation_requested = Signal(str)    # 请求在当前目录下新建对话（携带目录路径）

    def __init__(self, root_path, parent=None):
        super().__init__(parent)
        self.root_path = root_path or ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # ── 标题栏 + 工具按钮 ──────────────────────
        header_row = QHBoxLayout()
        header_row.setContentsMargins(8, 0, 8, 0)
        header_row.setSpacing(6)

        header = QLabel("资源管理器")
        header.setObjectName("panelHeader")
        header_row.addWidget(header, 1)

        self.open_folder_btn = QPushButton("📂")
        self.open_folder_btn.setToolTip("打开文件夹 (Ctrl+O)")
        self.open_folder_btn.setObjectName("fileTreeToolBtn")
        self.open_folder_btn.setFixedSize(26, 26)
        self.open_folder_btn.setCursor(Qt.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        header_row.addWidget(self.open_folder_btn)

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setToolTip("刷新")
        self.refresh_btn.setObjectName("fileTreeToolBtn")
        self.refresh_btn.setFixedSize(26, 26)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._on_refresh)
        header_row.addWidget(self.refresh_btn)

        layout.addLayout(header_row)

        # ── 当前路径显示 ───────────────────────────
        self.path_label = QLabel(self._display_path(self.root_path))
        self.path_label.setObjectName("fileTreePath")
        self.path_label.setToolTip(self.root_path)
        self.path_label.setWordWrap(True)
        self.path_label.setFont(QFont("Cascadia Code", 8))
        layout.addWidget(self.path_label)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #30363D;")
        layout.addWidget(sep)

        # ── 文件树 ─────────────────────────────────
        self.model = QFileSystemModel()
        self.model.setRootPath(self.root_path)
        self.model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Files)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_path) if self.root_path else QModelIndex())
        self.tree.setHeaderHidden(True)
        self.tree.setColumnWidth(0, 220)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.clicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

        # 快捷键
        self._shortcut_open = QAction(self)
        self._shortcut_open.setShortcut("Ctrl+O")
        self._shortcut_open.triggered.connect(self._on_open_folder)
        self.addAction(self._shortcut_open)

    @staticmethod
    def _display_path(path: str) -> str:
        if not path:
            return "未选择文件夹"
        try:
            home = os.path.expanduser("~")
            if path.lower().startswith(home.lower()):
                return "~" + path[len(home):]
        except Exception:
            pass
        return path

    def set_root_path(self, path: str):
        """切换文件树根目录"""
        path = os.path.normpath(os.path.abspath(os.path.expandvars(path))) if path else ""
        self.root_path = path
        self.path_label.setText(self._display_path(path))
        self.path_label.setToolTip(path)
        self.model.setRootPath(path)
        self.tree.setRootIndex(self.model.index(path) if path and os.path.exists(path) else QModelIndex())
        self.folder_changed.emit(path)

    def _on_open_folder(self):
        start_dir = self.root_path or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "选择项目文件夹", start_dir)
        if path:
            self.set_root_path(path)

    def _on_refresh(self):
        if self.root_path and os.path.exists(self.root_path):
            self.model.setRootPath("")
            self.model.setRootPath(self.root_path)
            self.tree.setRootIndex(self.model.index(self.root_path))

    def _on_item_clicked(self, index):
        path = self.model.filePath(index)
        if not path or os.path.isdir(path):
            return
        self.file_selected.emit(path)

    def _on_context_menu(self, pos):
        index = self.tree.indexAt(pos)
        menu = QMenu(self)

        # 通用：在当前根目录下新建对话
        new_conv_root = QAction("在当前目录开启新对话", self)
        new_conv_root.triggered.connect(lambda: self.new_conversation_requested.emit(self.root_path))
        menu.addAction(new_conv_root)

        if index.isValid():
            path = self.model.filePath(index)
            if os.path.isdir(path):
                menu.addSeparator()
                switch_folder = QAction(f"切换到该文件夹", self)
                switch_folder.triggered.connect(lambda: self.set_root_path(path))
                menu.addAction(switch_folder)

                new_conv_here = QAction(f"在该文件夹下开启新对话", self)
                new_conv_here.triggered.connect(lambda: self._request_new_conv_in(path))
                menu.addAction(new_conv_here)
            else:
                menu.addSeparator()
                open_doc = QAction("在右侧打开", self)
                open_doc.triggered.connect(lambda: self.file_selected.emit(path))
                menu.addAction(open_doc)

        menu.exec(self.tree.mapToGlobal(pos))

    def _request_new_conv_in(self, path: str):
        """先切换目录，再请求在该目录下新建对话"""
        self.set_root_path(path)
        self.new_conversation_requested.emit(path)

    def selected_path(self) -> str:
        """返回当前树中选中项的完整路径"""
        indexes = self.tree.selectedIndexes()
        if not indexes:
            return ""
        return self.model.filePath(indexes[0])
