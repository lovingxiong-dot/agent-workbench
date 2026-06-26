"""
ProjectExplorer — 多根节点项目资源管理器（MVC 重构版）

参考 VS Code / TRAE 左侧 Explorer：
- 打开编辑器
- 当前项目
- 最近项目
- 此电脑（C/D/E 等驱动器，按需展开）
- 全局配置

使用 QTreeWidget + 懒加载，避免启动时扫描大目录。
新增：过滤搜索框、多选、面包屑导航、标准化右键菜单。
"""
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QComboBox, QMenu, QFileDialog, QAbstractItemView,
    QLabel, QFrame, QLineEdit, QApplication, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont

from ui.models.explorer_model import ExplorerModel


class ProjectExplorer(QWidget):
    """多根节点资源管理器（View + Controller）"""

    file_selected = Signal(str)                 # 单击/双击文件（请求在右侧打开）
    document_activated = Signal(str)            # 点击已打开文档，请求激活
    document_closed = Signal(str)               # 关闭已打开文档
    folder_changed = Signal(str)                # 当前项目根目录变更
    new_conversation_requested = Signal(str)    # 在指定目录下新建对话
    open_in_system_explorer = Signal(str)       # 在系统资源管理器中打开
    copy_path = Signal(str)                     # 复制路径到剪贴板
    file_created = Signal(str)                  # 新建文件/文件夹成功（path）
    file_deleted = Signal(str)                  # 删除文件/文件夹成功（path）
    file_renamed = Signal(str, str)             # 重命名成功（old_path, new_path）

    # 树节点类型
    KIND_OPEN_EDITORS = "open_editors"
    KIND_CURRENT_PROJECT = "current_project"
    KIND_RECENT_PROJECTS = "recent_projects"
    KIND_THIS_PC = "this_pc"
    KIND_GLOBAL_CONFIG = "global_config"
    KIND_DRIVE = "drive"
    KIND_DIRECTORY = "directory"
    KIND_FILE = "file"
    KIND_RECENT_ITEM = "recent_item"
    KIND_OPEN_DOC = "open_doc"
    KIND_CONFIG_ITEM = "config_item"

    def __init__(self, project_root: str = "", storage_dir: str = "", parent=None):
        super().__init__(parent)
        self.model = ExplorerModel(project_root, storage_dir, parent=self)
        self._filter_text = ""
        self._current_display_path = self.model.project_root
        self._setup_ui()
        self._connect_model()
        self.refresh()

    # ═══════════════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════════════
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
        header_row.addWidget(header)

        self.recent_combo = QComboBox()
        self.recent_combo.setObjectName("recentProjectCombo")
        self.recent_combo.setToolTip("最近项目")
        self.recent_combo.setMinimumWidth(80)
        self.recent_combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.recent_combo.currentIndexChanged.connect(self._on_recent_project_selected)
        header_row.addWidget(self.recent_combo, 1)

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
        self.refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(self.refresh_btn)

        layout.addLayout(header_row)

        # ── 过滤框 ────────────────────────────────
        self.filter_edit = QLineEdit()
        self.filter_edit.setObjectName("explorerFilterEdit")
        self.filter_edit.setPlaceholderText("🔍 过滤文件...")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.filter_edit)

        # ── 面包屑导航 ───────────────────────────
        self.breadcrumb = QLabel(self._build_breadcrumb(self.model.project_root))
        self.breadcrumb.setObjectName("fileTreeBreadcrumb")
        self.breadcrumb.setToolTip(self.model.project_root)
        self.breadcrumb.setWordWrap(True)
        self.breadcrumb.setFont(QFont("Cascadia Code", 8))
        self.breadcrumb.setTextFormat(Qt.RichText)
        self.breadcrumb.setOpenExternalLinks(False)
        self.breadcrumb.linkActivated.connect(self._on_breadcrumb_clicked)
        layout.addWidget(self.breadcrumb)

        # ── 当前路径显示 ───────────────────────────
        self.path_label = QLabel(ExplorerModel.display_path(self.model.project_root))
        self.path_label.setObjectName("fileTreePath")
        self.path_label.setToolTip(self.model.project_root)
        self.path_label.setWordWrap(True)
        self.path_label.setFont(QFont("Cascadia Code", 8))
        layout.addWidget(self.path_label)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #30363D;")
        layout.addWidget(sep)

        # ── 树形控件 ───────────────────────────────
        self.tree = QTreeWidget()
        self.tree.setObjectName("projectExplorer")
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.setColumnCount(1)
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.tree)

    # ═══════════════════════════════════════════════════
    # Model 连接
    # ═══════════════════════════════════════════════════
    def _connect_model(self):
        self.model.project_root_changed.connect(self._on_model_project_root_changed)
        self.model.storage_dir_changed.connect(self._on_model_storage_dir_changed)
        self.model.recent_projects_changed.connect(self._on_model_recent_projects_changed)
        self.model.open_documents_changed.connect(self._on_model_open_documents_changed)
        self.model.data_changed.connect(self._build_root_items)

    # ═══════════════════════════════════════════════════
    # 公共接口（保持 MainWindow 兼容）
    # ═══════════════════════════════════════════════════
    def set_project_root(self, path: str):
        self.model.set_project_root(path)

    def set_storage_dir(self, path: str):
        self.model.set_storage_dir(path)

    def set_recent_projects(self, projects: list):
        self.model.set_recent_projects(projects)

    def set_open_documents(self, documents: list):
        self.model.set_open_documents(documents)

    def refresh(self):
        """刷新整个树"""
        self._build_root_items()

    # ═══════════════════════════════════════════════════
    # Model 变更回调
    # ═══════════════════════════════════════════════════
    def _on_model_project_root_changed(self, path: str):
        self._set_current_path(path, update_tree=False)
        self.folder_changed.emit(path)

    def _on_model_storage_dir_changed(self, path: str):
        self.path_label.setToolTip(path)

    def _on_model_recent_projects_changed(self, projects: list):
        self._refresh_recent_combo(projects)

    def _on_model_open_documents_changed(self, documents: list):
        pass  # _build_root_items 会处理

    # ═══════════════════════════════════════════════════
    # 根节点构建
    # ═══════════════════════════════════════════════════
    def _build_root_items(self):
        self.tree.clear()

        # 1. 打开编辑器
        self._open_editors_item = QTreeWidgetItem(self.tree, ["打开编辑器"])
        self._open_editors_item.setData(0, Qt.UserRole, "")
        self._open_editors_item.setData(0, Qt.UserRole + 1, self.KIND_OPEN_EDITORS)
        self._open_editors_item.setIcon(0, self._style_icon("📝"))
        self._refresh_open_editors()

        # 2. 当前项目
        self._current_project_item = QTreeWidgetItem(self.tree, ["当前项目"])
        self._current_project_item.setData(0, Qt.UserRole, self.model.project_root)
        self._current_project_item.setData(0, Qt.UserRole + 1, self.KIND_CURRENT_PROJECT)
        self._current_project_item.setIcon(0, self._style_icon("📁"))
        self._refresh_current_project()

        # 3. 最近项目
        self._recent_projects_item = QTreeWidgetItem(self.tree, ["最近项目"])
        self._recent_projects_item.setData(0, Qt.UserRole, "")
        self._recent_projects_item.setData(0, Qt.UserRole + 1, self.KIND_RECENT_PROJECTS)
        self._recent_projects_item.setIcon(0, self._style_icon("🕐"))
        self._refresh_recent_projects()

        # 4. 此电脑
        self._this_pc_item = QTreeWidgetItem(self.tree, ["此电脑"])
        self._this_pc_item.setData(0, Qt.UserRole, "")
        self._this_pc_item.setData(0, Qt.UserRole + 1, self.KIND_THIS_PC)
        self._this_pc_item.setIcon(0, self._style_icon("💻"))
        self._this_pc_item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)

        # 5. 全局配置
        self._global_config_item = QTreeWidgetItem(self.tree, ["全局配置"])
        self._global_config_item.setData(0, Qt.UserRole, self.model.storage_dir)
        self._global_config_item.setData(0, Qt.UserRole + 1, self.KIND_GLOBAL_CONFIG)
        self._global_config_item.setIcon(0, self._style_icon("⚙️"))
        self._refresh_global_config()

        # 默认展开当前项目
        if self.model.project_root:
            self._current_project_item.setExpanded(True)

        self.tree.expandAll()
        self._this_pc_item.setExpanded(False)
        self._recent_projects_item.setExpanded(False)

        self._apply_filter()

    # ═══════════════════════════════════════════════════
    # 各区域刷新
    # ═══════════════════════════════════════════════════
    def _refresh_open_editors(self):
        self._open_editors_item.takeChildren()
        docs = self.model.open_documents
        if not docs:
            self._add_placeholder_item(self._open_editors_item, "无打开文件")
            return
        for doc in docs:
            path = doc.get("path", "")
            if not path:
                continue
            name = os.path.basename(path) or path
            is_active = doc.get("is_active", False)
            label = f"{name} {'(活动)' if is_active else ''}".strip()
            item = QTreeWidgetItem(self._open_editors_item, [label])
            item.setData(0, Qt.UserRole, path)
            item.setData(0, Qt.UserRole + 1, self.KIND_OPEN_DOC)
            item.setIcon(0, self._style_icon("📄"))

    def _refresh_current_project(self):
        self._current_project_item.takeChildren()
        path = self.model.project_root
        self._current_project_item.setText(0, f"当前项目{ExplorerModel.project_basename(path)}")
        if not path or not os.path.isdir(path):
            self._add_placeholder_item(self._current_project_item, "未选择文件夹")
            return
        self._load_directory(self._current_project_item, path, expanded=True)

    def _refresh_recent_projects(self):
        self._recent_projects_item.takeChildren()
        projects = self.model.recent_projects
        if not projects:
            self._add_placeholder_item(self._recent_projects_item, "无最近项目")
            return
        for project in projects:
            path = project.get("path", "")
            name = ExplorerModel.project_basename(path).replace(" — ", "") or path
            item = QTreeWidgetItem(self._recent_projects_item, [name])
            item.setData(0, Qt.UserRole, path)
            item.setData(0, Qt.UserRole + 1, self.KIND_RECENT_ITEM)
            item.setToolTip(0, path)
            item.setIcon(0, self._style_icon("📂"))

    def _refresh_global_config(self):
        self._global_config_item.takeChildren()
        entries = self.model.list_global_config()
        if not entries:
            self._add_placeholder_item(self._global_config_item, "未配置或空目录")
            return
        for entry in entries:
            name = entry["name"]
            full = entry["path"]
            item = QTreeWidgetItem(self._global_config_item, [name])
            item.setData(0, Qt.UserRole, full)
            item.setData(0, Qt.UserRole + 1, self.KIND_CONFIG_ITEM)
            item.setIcon(0, self._style_icon("⚙️" if entry.get("is_file") else "📁"))

    def _refresh_recent_combo(self, projects: list):
        """同步顶部下拉框"""
        self.recent_combo.blockSignals(True)
        self.recent_combo.clear()
        self.recent_combo.addItem("最近项目", "")
        for project in projects:
            path = project.get("path", "")
            display = ExplorerModel.display_path(path)
            self.recent_combo.addItem(display, path)
            self.recent_combo.setItemData(self.recent_combo.count() - 1, path, Qt.ToolTipRole)
        self.recent_combo.blockSignals(False)

    # ═══════════════════════════════════════════════════
    # 过滤
    # ═══════════════════════════════════════════════════
    def _on_filter_changed(self, text: str):
        self._filter_text = text.strip().lower()
        self._apply_filter()

    def _apply_filter(self):
        """递归应用过滤：隐藏不匹配项，保留父节点以显示匹配子节点"""
        self._apply_filter_on_item(self.tree.invisibleRootItem())

    def _apply_filter_on_item(self, parent: QTreeWidgetItem):
        any_visible = False
        for i in range(parent.childCount()):
            item = parent.child(i)
            child_visible = self._apply_filter_on_item(item)
            kind = item.data(0, Qt.UserRole + 1)
            name = item.text(0).lower()
            matches = (not self._filter_text) or (self._filter_text in name)
            # 根节点始终显示；叶子节点按名称过滤；若子节点匹配则保留
            visible = kind in (
                self.KIND_OPEN_EDITORS, self.KIND_CURRENT_PROJECT,
                self.KIND_RECENT_PROJECTS, self.KIND_THIS_PC, self.KIND_GLOBAL_CONFIG
            ) or matches or child_visible
            item.setHidden(not visible)
            if visible:
                any_visible = True
        return any_visible

    # ═══════════════════════════════════════════════════
    # 面包屑与当前路径
    # ═══════════════════════════════════════════════════
    def _set_current_path(self, path: str, update_tree: bool = True):
        """更新当前显示路径、面包屑与路径标签"""
        path = ExplorerModel.normalize_path(path) if path else self.model.project_root
        self._current_display_path = path
        self.path_label.setText(ExplorerModel.display_path(path))
        self.path_label.setToolTip(path)
        self.breadcrumb.setText(self._build_breadcrumb(path))
        self.breadcrumb.setToolTip(path)
        if update_tree:
            self._reveal_path_in_tree(path)

    def _build_breadcrumb(self, path: str) -> str:
        """生成可点击的面包屑 HTML；path 为空时返回空"""
        if not path:
            return ""
        segments = []
        current = path
        while current and current != os.path.dirname(current):
            name = os.path.basename(current) or current
            # 对 href 中的反斜杠做转义，避免 HTML 解析异常
            safe_path = current.replace("\\", "/")
            segments.append((name, safe_path))
            current = os.path.dirname(current)
        if not segments:
            return path
        segments.reverse()
        # 使用 span 分隔，保持整体可点击
        parts = [
            f"<a href=\"{p}\" style=\"color:#58A6FF;text-decoration:none;\">{n}</a>"
            for n, p in segments
        ]
        return " &gt; ".join(parts)

    def _on_breadcrumb_clicked(self, path: str):
        """点击面包屑段时切换当前显示路径"""
        # href 中被我们替换为 /，恢复为本地路径
        native_path = path.replace("/", os.sep)
        self._set_current_path(native_path, update_tree=True)

    def _reveal_path_in_tree(self, path: str):
        """在树中展开并选中指定路径（尽量定位，不强制）"""
        if not path or not path.startswith(self.model.project_root):
            return
        # 先找到当前项目根节点
        root = self._current_project_item
        if not root:
            return
        # 如果就是根节点，直接选中
        if path == self.model.project_root:
            self.tree.setCurrentItem(root)
            return
        # 计算相对路径组件
        rel = os.path.relpath(path, self.model.project_root)
        parts = rel.split(os.sep)
        current = root
        # 逐级展开
        for part in parts:
            if not part:
                continue
            found = None
            for i in range(current.childCount()):
                child = current.child(i)
                if child.text(0) == part:
                    found = child
                    break
            if found is None:
                break
            current = found
            if not current.isExpanded():
                current.setExpanded(True)
            # 触发懒加载
            self._on_item_expanded(current)
        self.tree.setCurrentItem(current)

    # ═══════════════════════════════════════════════════
    # 目录懒加载
    # ═══════════════════════════════════════════════════
    def _on_item_expanded(self, item: QTreeWidgetItem):
        kind = item.data(0, Qt.UserRole + 1)
        path = item.data(0, Qt.UserRole) or ""

        if kind == self.KIND_THIS_PC and item.childCount() == 0:
            self._load_drives(item)
            return

        if kind in (self.KIND_DRIVE, self.KIND_DIRECTORY) and item.childCount() == 1:
            first = item.child(0)
            if first and first.data(0, Qt.UserRole + 1) == "__placeholder__":
                item.takeChildren()
                self._load_directory(item, path)
                return

    def _load_drives(self, parent: QTreeWidgetItem):
        """加载 Windows 驱动器"""
        parent.takeChildren()
        drives = self.model.get_drives()
        if not drives:
            self._add_placeholder_item(parent, "未检测到驱动器")
            return
        for drive in drives:
            item = QTreeWidgetItem(parent, [drive])
            item.setData(0, Qt.UserRole, drive)
            item.setData(0, Qt.UserRole + 1, self.KIND_DRIVE)
            item.setIcon(0, self._style_icon("💾"))
            self._add_placeholder(item)

    def _load_directory(self, parent: QTreeWidgetItem, path: str, expanded: bool = False):
        """加载指定目录的子项"""
        result = self.model.list_directory(path)
        dirs, files = result["dirs"], result["files"]

        if not dirs and not files:
            self._add_placeholder_item(parent, "空目录")
            return

        for entry in dirs:
            child = QTreeWidgetItem(parent, [entry["name"]])
            child.setData(0, Qt.UserRole, entry["path"])
            child.setData(0, Qt.UserRole + 1, self.KIND_DIRECTORY)
            child.setIcon(0, self._style_icon("📁"))
            self._add_placeholder(child)

        for entry in files:
            child = QTreeWidgetItem(parent, [entry["name"]])
            child.setData(0, Qt.UserRole, entry["path"])
            child.setData(0, Qt.UserRole + 1, self.KIND_FILE)
            child.setIcon(0, self._style_icon("📄"))

        if expanded:
            parent.setExpanded(True)

    def _add_placeholder(self, parent: QTreeWidgetItem):
        """为目录节点添加占位子项，使其显示展开箭头"""
        placeholder = QTreeWidgetItem(parent, ["加载中..."])
        placeholder.setData(0, Qt.UserRole + 1, "__placeholder__")
        placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsEnabled)

    def _add_placeholder_item(self, parent: QTreeWidgetItem, text: str):
        placeholder = QTreeWidgetItem(parent, [text])
        placeholder.setData(0, Qt.UserRole + 1, "__placeholder__")
        placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsEnabled)

    # ═══════════════════════════════════════════════════
    # 事件处理
    # ═══════════════════════════════════════════════════
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        kind = item.data(0, Qt.UserRole + 1)
        path = item.data(0, Qt.UserRole) or ""
        # 目录/文件点击时同步面包屑当前路径
        if kind in (self.KIND_DIRECTORY, self.KIND_DRIVE, self.KIND_CURRENT_PROJECT):
            self._set_current_path(path, update_tree=False)
        elif kind == self.KIND_FILE:
            self._set_current_path(os.path.dirname(path) or self.model.project_root, update_tree=False)
            self.file_selected.emit(path)
        elif kind == self.KIND_OPEN_DOC:
            self.document_activated.emit(path)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        kind = item.data(0, Qt.UserRole + 1)
        path = item.data(0, Qt.UserRole) or ""
        if kind == self.KIND_FILE:
            self.file_selected.emit(path)
        elif kind in (self.KIND_OPEN_DOC, self.KIND_RECENT_ITEM, self.KIND_CONFIG_ITEM):
            # 已打开文档：单击激活；双击也视为激活（不重新打开新标签）
            if kind == self.KIND_OPEN_DOC:
                self.document_activated.emit(path)
            else:
                self.file_selected.emit(path)

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        selected_items = self.tree.selectedItems()
        # 优先以点击项为上下文；若点击空白处且无选中，不弹出
        if not item and not selected_items:
            return
        target = item if item else selected_items[0]
        kind = target.data(0, Qt.UserRole + 1)
        path = target.data(0, Qt.UserRole) or ""

        menu = QMenu(self)
        self._build_context_menu(menu, kind, path, target)
        if menu.isEmpty():
            return
        menu.exec(self.tree.mapToGlobal(pos))

    def _build_context_menu(self, menu: QMenu, kind: str, path: str, item: QTreeWidgetItem):
        """标准化右键菜单构建器"""
        actions = []

        if kind == self.KIND_FILE:
            actions.append(("在右侧打开", lambda: self.file_selected.emit(path)))
            actions.append(("重命名", lambda: self._rename_path(path)))
            actions.append(("删除", lambda: self._delete_path(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))
            actions.append(("在文件资源管理器中打开", lambda: self.open_in_system_explorer.emit(path)))

        elif kind in (self.KIND_DIRECTORY, self.KIND_DRIVE, self.KIND_CURRENT_PROJECT, self.KIND_RECENT_ITEM):
            if kind in (self.KIND_DIRECTORY, self.KIND_DRIVE, self.KIND_CURRENT_PROJECT):
                actions.append(("新建文件", lambda: self._create_file(path)))
                actions.append(("新建文件夹", lambda: self._create_folder(path)))
                actions.append(None)  # 分隔线
            actions.append(("切换为当前项目", lambda: self.set_project_root(path)))
            actions.append(("在该目录下开启新对话", lambda: self.new_conversation_requested.emit(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))
            actions.append(("在文件资源管理器中打开", lambda: self.open_in_system_explorer.emit(path)))
            if kind in (self.KIND_DIRECTORY, self.KIND_DRIVE, self.KIND_CURRENT_PROJECT):
                actions.append(("刷新", lambda: self._refresh_item(item)))
                if kind != self.KIND_CURRENT_PROJECT:
                    actions.append(("删除", lambda: self._delete_path(path)))

        elif kind == self.KIND_OPEN_DOC:
            actions.append(("激活", lambda: self.document_activated.emit(path)))
            actions.append(("关闭", lambda: self.document_closed.emit(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))

        elif kind == self.KIND_CONFIG_ITEM:
            actions.append(("在右侧打开", lambda: self.file_selected.emit(path)))
            actions.append(("删除", lambda: self._delete_path(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))
            actions.append(("在文件资源管理器中打开", lambda: self.open_in_system_explorer.emit(path)))

        for entry in actions:
            if entry is None:
                menu.addSeparator()
                continue
            label, callback = entry
            action = QAction(label, self)
            action.triggered.connect(callback)
            menu.addAction(action)

    def _copy_path(self, path: str):
        """复制路径到剪贴板并发出信号"""
        if path:
            QApplication.clipboard().setText(path)
            self.copy_path.emit(path)

    def _create_file(self, parent_path: str):
        """右键新建文件"""
        name, ok = QInputDialog.getText(self, "新建文件", "文件名:")
        if not ok or not name:
            return
        success, result = self.model.create_file(parent_path, name)
        if success:
            self.file_created.emit(result)
            self.refresh()
        else:
            QMessageBox.warning(self, "新建文件失败", result)

    def _create_folder(self, parent_path: str):
        """右键新建文件夹"""
        name, ok = QInputDialog.getText(self, "新建文件夹", "文件夹名:")
        if not ok or not name:
            return
        success, result = self.model.create_folder(parent_path, name)
        if success:
            self.file_created.emit(result)
            self.refresh()
        else:
            QMessageBox.warning(self, "新建文件夹失败", result)

    def _delete_path(self, path: str):
        """右键删除文件/文件夹（空文件夹才可删除）"""
        if not path:
            return
        name = os.path.basename(path) or path
        reply = QMessageBox.question(
            self, "确认删除",
            f'确定要删除 "{name}" 吗？\n此操作不可恢复。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        success, msg = self.model.delete_path(path)
        if success:
            self.file_deleted.emit(path)
            self.refresh()
        else:
            QMessageBox.warning(self, "删除失败", msg)

    def _rename_path(self, path: str):
        """右键重命名文件/文件夹"""
        if not path:
            return
        old_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=old_name)
        if not ok or not new_name or new_name == old_name:
            return
        success, result = self.model.rename_path(path, new_name)
        if success:
            self.file_renamed.emit(path, result)
            self.refresh()
        else:
            QMessageBox.warning(self, "重命名失败", result)

    def _refresh_item(self, item: QTreeWidgetItem):
        """刷新指定目录节点"""
        kind = item.data(0, Qt.UserRole + 1)
        path = item.data(0, Qt.UserRole) or ""
        if kind == self.KIND_CURRENT_PROJECT:
            self._refresh_current_project()
        elif kind == self.KIND_GLOBAL_CONFIG:
            self._refresh_global_config()
        elif kind == self.KIND_THIS_PC:
            self._load_drives(item)
        elif kind in (self.KIND_DRIVE, self.KIND_DIRECTORY):
            item.takeChildren()
            self._load_directory(item, path)
        elif kind == self.KIND_RECENT_PROJECTS:
            self._refresh_recent_projects()
        elif kind == self.KIND_OPEN_EDITORS:
            self._refresh_open_editors()

    # ═══════════════════════════════════════════════════
    # 工具栏事件
    # ═══════════════════════════════════════════════════
    def _on_recent_project_selected(self, index: int):
        if index <= 0:
            return
        path = self.recent_combo.itemData(index)
        if path and path != self.model.project_root:
            self.set_project_root(path)

    def _on_open_folder(self):
        start_dir = self.model.project_root or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "选择项目文件夹", start_dir)
        if path:
            self.set_project_root(path)

    # ═══════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════
    @staticmethod
    def _style_icon(emoji: str):
        """返回一个空 QIcon 占位；emoji 由 QLabel/QSS 渲染"""
        from PySide6.QtGui import QIcon
        return QIcon()
