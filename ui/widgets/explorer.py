"""
ProjectExplorer — 多根节点项目资源管理器（完整 MVC 版）

架构：
- ExplorerModel（业务模型）: ui/models/explorer_model.py
- ExplorerTreeModel（QAbstractItemModel）: ui/models/explorer_tree_model.py
- ExplorerTreeView（QTreeView）: ui/widgets/explorer_view.py
- ProjectExplorer（Controller）: 本文件

参考 VS Code / TRAE 左侧 Explorer：
- 打开编辑器
- 当前项目
- 最近项目
- 此电脑（C/D/E 等驱动器，按需展开）
- 全局配置

特性：过滤搜索框、标准化右键菜单、面包屑导航、懒加载。
"""
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QMenu, QFileDialog,
    QLabel, QFrame, QLineEdit, QApplication, QInputDialog, QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QModelIndex
from PySide6.QtGui import QAction, QFont

from ui.models.explorer_model import ExplorerModel
from ui.models.explorer_tree_model import ExplorerTreeModel, NodeKind
from ui.widgets.explorer_view import ExplorerTreeView


class ProjectExplorer(QWidget):
    """多根节点资源管理器（Controller）"""

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

    # 兼容旧版：节点类型常量
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
        self.tree_model = ExplorerTreeModel(self.model, parent=self)
        self._filter_text = ""
        self._current_display_path = self.model.project_root
        self._setup_ui()
        self._connect_model()
        self._connect_view()

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

        # ── 树形控件（MVC）───────────────────────────
        self.tree_view = ExplorerTreeView(self)
        self.tree_view.setModel(self.tree_model)
        self.tree_view.file_clicked.connect(self._on_item_clicked)
        self.tree_view.file_double_clicked.connect(self._on_item_double_clicked)
        self.tree_view.context_menu_requested.connect(self._on_context_menu)
        layout.addWidget(self.tree_view)

    # ═══════════════════════════════════════════════════
    # 信号连接
    # ═══════════════════════════════════════════════════
    def _connect_model(self):
        self.model.project_root_changed.connect(self._on_model_project_root_changed)
        self.model.storage_dir_changed.connect(self._on_model_storage_dir_changed)
        self.model.recent_projects_changed.connect(self._on_model_recent_projects_changed)
        self.model.open_documents_changed.connect(self._on_model_open_documents_changed)

    def _connect_view(self):
        """初始化展开状态：仅展开非文件系统的顶层分类，避免 expandAll 触发此电脑下驱动器递归加载。"""
        root_index = QModelIndex()
        expandable = {
            ExplorerTreeModel.CATEGORY_OPEN_EDITORS,
            ExplorerTreeModel.CATEGORY_CURRENT_PROJECT,
            ExplorerTreeModel.CATEGORY_RECENT_PROJECTS,
            ExplorerTreeModel.CATEGORY_GLOBAL_CONFIG,
        }
        for row in range(self.tree_model.rowCount(root_index)):
            idx = self.tree_model.index(row, 0, root_index)
            cat = self.tree_model.category_key_from_index(idx)
            if cat == ExplorerTreeModel.CATEGORY_THIS_PC:
                self.tree_view.setExpanded(idx, False)
            elif cat in expandable:
                self.tree_view.setExpanded(idx, True)

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
        self.tree_model.reload()
        self._connect_view()
        self._apply_filter()

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
        pass  # tree_model 会处理刷新

    # ═══════════════════════════════════════════════════
    # 过滤
    # ═══════════════════════════════════════════════════
    def _on_filter_changed(self, text: str):
        self._filter_text = text.strip().lower()
        self._apply_filter()

    def _apply_filter(self):
        self.tree_view.apply_filter(self._filter_text)

    # ═══════════════════════════════════════════════════
    # 面包屑与当前路径
    # ═══════════════════════════════════════════════════
    def _set_current_path(self, path: str, update_tree: bool = True):
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
            safe_path = current.replace("\\", "/")
            segments.append((name, safe_path))
            current = os.path.dirname(current)
        if not segments:
            return path
        segments.reverse()
        parts = [
            f"<a href=\"{p}\" style=\"color:#58A6FF;text-decoration:none;\">{n}</a>"
            for n, p in segments
        ]
        return " &gt; ".join(parts)

    def _on_breadcrumb_clicked(self, path: str):
        native_path = path.replace("/", os.sep)
        self._set_current_path(native_path, update_tree=True)

    def _reveal_path_in_tree(self, path: str):
        """在树中展开并选中指定路径（尽量定位，不强制）"""
        if not path or not path.startswith(self.model.project_root):
            return
        if path == self.model.project_root:
            self._select_category(ExplorerTreeModel.CATEGORY_CURRENT_PROJECT)
            return
        rel = os.path.relpath(path, self.model.project_root)
        parts = rel.split(os.sep)

        # 定位当前项目分类节点
        cat_index = self._category_index(ExplorerTreeModel.CATEGORY_CURRENT_PROJECT)
        if not cat_index.isValid():
            return
        current = cat_index
        for part in parts:
            if not part:
                continue
            found = QModelIndex()
            rows = self.tree_model.rowCount(current)
            for row in range(rows):
                idx = self.tree_model.index(row, 0, current)
                name = idx.data(Qt.DisplayRole) or ""
                if name == part:
                    found = idx
                    break
            if not found.isValid():
                break
            current = found
            if not self.tree_view.isExpanded(current):
                self.tree_view.setExpanded(current, True)
        self.tree_view.setCurrentIndex(current)

    def _category_index(self, category_key: str) -> QModelIndex:
        root_index = QModelIndex()
        for row in range(self.tree_model.rowCount(root_index)):
            idx = self.tree_model.index(row, 0, root_index)
            if self.tree_model.category_key_from_index(idx) == category_key:
                return idx
        return QModelIndex()

    def _select_category(self, category_key: str):
        idx = self._category_index(category_key)
        if idx.isValid():
            self.tree_view.setCurrentIndex(idx)

    # ═══════════════════════════════════════════════════
    # 事件处理
    # ═══════════════════════════════════════════════════
    def _on_item_clicked(self, path: str, kind_name: str):
        if kind_name in (NodeKind.DIRECTORY.name, NodeKind.DRIVE.name, NodeKind.CATEGORY.name):
            self._set_current_path(path, update_tree=False)
        elif kind_name == NodeKind.FILE.name:
            self._set_current_path(os.path.dirname(path) or self.model.project_root, update_tree=False)
            self.file_selected.emit(path)
        elif kind_name == NodeKind.OPEN_DOC.name:
            self.document_activated.emit(path)
        elif kind_name == NodeKind.RECENT_ITEM.name:
            # 最近项目单击：切换当前项目
            self.set_project_root(path)
        elif kind_name == NodeKind.CONFIG_ITEM.name:
            self.file_selected.emit(path)

    def _on_item_double_clicked(self, path: str, kind_name: str):
        if kind_name == NodeKind.FILE.name:
            self.file_selected.emit(path)
        elif kind_name == NodeKind.OPEN_DOC.name:
            self.document_activated.emit(path)
        elif kind_name in (NodeKind.RECENT_ITEM.name, NodeKind.CONFIG_ITEM.name):
            self.file_selected.emit(path)

    def _on_context_menu(self, index, global_pos):
        if not index.isValid():
            return
        path = index.data(Qt.UserRole) or ""
        kind_name = index.data(Qt.UserRole + 1) or ""
        menu = QMenu(self)
        self._build_context_menu(menu, kind_name, path, index)
        if menu.isEmpty():
            return
        menu.exec(global_pos)

    def _build_context_menu(self, menu: QMenu, kind_name: str, path: str, index):
        """标准化右键菜单构建器"""
        actions = []

        if kind_name == NodeKind.FILE.name:
            actions.append(("在右侧打开", lambda: self.file_selected.emit(path)))
            actions.append(("重命名", lambda: self._rename_path(path)))
            actions.append(("删除", lambda: self._delete_path(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))
            actions.append(("在文件资源管理器中打开", lambda: self.open_in_system_explorer.emit(path)))

        elif kind_name in (NodeKind.DIRECTORY.name, NodeKind.DRIVE.name, NodeKind.CATEGORY.name):
            cat = self.tree_model.category_key_from_index(index)
            if cat in (self.KIND_DIRECTORY, self.KIND_DRIVE, self.KIND_CURRENT_PROJECT) or kind_name in (
                NodeKind.DIRECTORY.name, NodeKind.DRIVE.name
            ):
                actions.append(("新建文件", lambda: self._create_file(path)))
                actions.append(("新建文件夹", lambda: self._create_folder(path)))
                actions.append(None)
            if cat == self.KIND_CURRENT_PROJECT:
                actions.append(("刷新", lambda: self.tree_model.refresh_item(index)))
            actions.append(("切换为当前项目", lambda: self.set_project_root(path)))
            actions.append(("在该目录下开启新对话", lambda: self.new_conversation_requested.emit(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))
            actions.append(("在文件资源管理器中打开", lambda: self.open_in_system_explorer.emit(path)))
            if kind_name in (NodeKind.DIRECTORY.name, NodeKind.DRIVE.name):
                actions.append(("刷新", lambda: self.tree_model.refresh_item(index)))
                actions.append(("删除", lambda: self._delete_path(path)))

        elif kind_name == NodeKind.OPEN_DOC.name:
            actions.append(("激活", lambda: self.document_activated.emit(path)))
            actions.append(("关闭", lambda: self.document_closed.emit(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))

        elif kind_name == NodeKind.RECENT_ITEM.name:
            actions.append(("切换为当前项目", lambda: self.set_project_root(path)))
            actions.append(("在该目录下开启新对话", lambda: self.new_conversation_requested.emit(path)))
            actions.append(("复制路径", lambda: self._copy_path(path)))
            actions.append(("在文件资源管理器中打开", lambda: self.open_in_system_explorer.emit(path)))

        elif kind_name == NodeKind.CONFIG_ITEM.name:
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
        if path:
            QApplication.clipboard().setText(path)
            self.copy_path.emit(path)

    def _create_file(self, parent_path: str):
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
