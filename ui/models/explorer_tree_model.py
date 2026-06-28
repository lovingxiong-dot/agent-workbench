"""
ExplorerTreeModel — 资源管理器树模型（QAbstractItemModel）

职责：
- 以多根节点树形式呈现：打开编辑器、当前项目、最近项目、此电脑、全局配置
- 支持目录懒加载（占位 → 展开 → 读取目录）
- 不依赖 View，可被任意 QTreeView 复用

数据角色：
- Qt.DisplayRole: 显示文本
- Qt.UserRole: 节点路径
- Qt.UserRole + 1: 节点类型（NodeKind.name）
- Qt.DecorationRole: 图标（emoji 字符串，由 View 渲染）
"""
import os
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QAbstractItemModel, QModelIndex, QObject, Qt, Signal

from ui.models.explorer_model import ExplorerModel


class NodeKind(Enum):
    """树节点类型"""
    ROOT = auto()
    CATEGORY = auto()
    OPEN_DOC = auto()
    DIRECTORY = auto()
    FILE = auto()
    DRIVE = auto()
    RECENT_ITEM = auto()
    CONFIG_ITEM = auto()
    PLACEHOLDER = auto()


class ExplorerTreeItem:
    """树节点"""

    def __init__(
        self,
        kind: NodeKind,
        name: str,
        path: str = "",
        icon: str = "",
        tooltip: str = "",
        payload: Optional[Dict[str, Any]] = None,
        parent: Optional["ExplorerTreeItem"] = None,
    ):
        self.kind = kind
        self.name = name
        self.path = path
        self.icon = icon
        self.tooltip = tooltip
        self.payload = payload or {}
        self.parent = parent
        self.children: List[ExplorerTreeItem] = []
        self.loaded = False

    def append(self, item: "ExplorerTreeItem") -> "ExplorerTreeItem":
        item.parent = self
        self.children.append(item)
        return item

    def child(self, row: int) -> "ExplorerTreeItem":
        return self.children[row]

    def child_count(self) -> int:
        return len(self.children)

    def row(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.children.index(self)

    def clear(self):
        self.children.clear()
        self.loaded = False

    def is_category(self) -> bool:
        return self.kind == NodeKind.CATEGORY

    def is_directory_like(self) -> bool:
        return self.kind in (NodeKind.DIRECTORY, NodeKind.DRIVE, NodeKind.CATEGORY)


class ExplorerTreeModel(QAbstractItemModel):
    """资源管理器 QAbstractItemModel 实现"""

    project_root_changed = Signal(str)
    open_documents_changed = Signal(list)
    recent_projects_changed = Signal(list)
    storage_dir_changed = Signal(str)

    CATEGORY_OPEN_EDITORS = "open_editors"
    CATEGORY_CURRENT_PROJECT = "current_project"
    CATEGORY_RECENT_PROJECTS = "recent_projects"
    CATEGORY_THIS_PC = "this_pc"
    CATEGORY_GLOBAL_CONFIG = "global_config"

    def __init__(self, explorer_model: ExplorerModel, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._explorer_model = explorer_model
        self._root = ExplorerTreeItem(NodeKind.ROOT, "root")
        self._build_categories()
        self._connect_model()
        self._refresh_all()

    # ═══════════════════════════════════════════════════
    # Model 信号连接
    # ═══════════════════════════════════════════════════
    def _connect_model(self):
        em = self._explorer_model
        em.project_root_changed.connect(self._on_project_root_changed)
        em.storage_dir_changed.connect(self._on_storage_dir_changed)
        em.recent_projects_changed.connect(self._on_recent_projects_changed)
        em.open_documents_changed.connect(self._on_open_documents_changed)
        em.data_changed.connect(self._refresh_all)

    # ═══════════════════════════════════════════════════
    # QAbstractItemModel 接口
    # ═══════════════════════════════════════════════════
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_item = self._item_from_index(parent) if parent.isValid() else self._root
        if parent_item is None or row < 0 or row >= len(parent_item.children):
            return QModelIndex()
        return self.createIndex(row, column, parent_item.children[row])

    def parent(self, index: QModelIndex = QModelIndex()) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        item = self._item_from_index(index)
        if item is None or item.parent is None or item.parent == self._root:
            return QModelIndex()
        return self.createIndex(item.parent.row(), 0, item.parent)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        item = self._item_from_index(parent) if parent.isValid() else self._root
        return len(item.children) if item else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        item = self._item_from_index(index)
        if item is None:
            return None
        if role == Qt.DisplayRole:
            return item.name
        if role == Qt.UserRole:
            return item.path
        if role == Qt.UserRole + 1:
            return item.kind.name
        if role == Qt.DecorationRole:
            return item.icon
        if role == Qt.ToolTipRole:
            return item.tooltip or item.path
        if role == Qt.UserRole + 2:
            return item.payload
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.NoItemFlags
        item = self._item_from_index(index)
        if item and item.kind == NodeKind.PLACEHOLDER:
            return Qt.NoItemFlags
        return super().flags(index)

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:
        item = self._item_from_index(parent) if parent.isValid() else self._root
        if item is None:
            return False
        if item.kind in (NodeKind.CATEGORY, NodeKind.DRIVE, NodeKind.DIRECTORY):
            return True
        return len(item.children) > 0

    def canFetchMore(self, parent: QModelIndex) -> bool:
        if not parent.isValid():
            return False
        item = self._item_from_index(parent)
        if item is None:
            return False
        if item.kind in (NodeKind.DRIVE, NodeKind.DIRECTORY, NodeKind.CATEGORY) and not item.loaded:
            return True
        return False

    def fetchMore(self, parent: QModelIndex):
        if not parent.isValid():
            return
        item = self._item_from_index(parent)
        if item is None or item.loaded:
            return
        self._load_item_children(item)

    # ═══════════════════════════════════════════════════
    # 节点辅助
    # ═══════════════════════════════════════════════════
    def _item_from_index(self, index: QModelIndex) -> Optional[ExplorerTreeItem]:
        if not index.isValid():
            return None
        return index.internalPointer()

    def _category_item(self, category_key: str) -> Optional[ExplorerTreeItem]:
        for child in self._root.children:
            if child.payload.get("category") == category_key:
                return child
        return None

    # ═══════════════════════════════════════════════════
    # 树构建
    # ═══════════════════════════════════════════════════
    def _build_categories(self):
        self._root.clear()
        categories = [
            (self.CATEGORY_OPEN_EDITORS, "📝", "打开编辑器"),
            (self.CATEGORY_CURRENT_PROJECT, "📁", "当前项目"),
            (self.CATEGORY_RECENT_PROJECTS, "🕐", "最近项目"),
            (self.CATEGORY_THIS_PC, "💻", "此电脑"),
            (self.CATEGORY_GLOBAL_CONFIG, "⚙️", "全局配置"),
        ]
        for key, icon, name in categories:
            item = ExplorerTreeItem(
                kind=NodeKind.CATEGORY,
                name=name,
                path="",
                icon=icon,
                payload={"category": key},
                parent=self._root,
            )
            self._root.append(item)

    def _refresh_all(self):
        for cat in self._root.children:
            cat.clear()
            cat.loaded = False
        self._load_item_children(self._category_item(self.CATEGORY_OPEN_EDITORS))
        self._load_item_children(self._category_item(self.CATEGORY_CURRENT_PROJECT))
        self._load_item_children(self._category_item(self.CATEGORY_RECENT_PROJECTS))
        self._load_item_children(self._category_item(self.CATEGORY_GLOBAL_CONFIG))
        # 此电脑不自动加载，保留未加载状态以显示展开箭头
        self.modelReset.emit()

    def _load_item_children(self, item: Optional[ExplorerTreeItem]):
        if item is None or item.loaded:
            return
        item.clear()
        category = item.payload.get("category")
        if category == self.CATEGORY_OPEN_EDITORS:
            self._load_open_editors(item)
        elif category == self.CATEGORY_CURRENT_PROJECT:
            self._load_current_project(item)
        elif category == self.CATEGORY_RECENT_PROJECTS:
            self._load_recent_projects(item)
        elif category == self.CATEGORY_THIS_PC:
            self._load_this_pc(item)
        elif category == self.CATEGORY_GLOBAL_CONFIG:
            self._load_global_config(item)
        elif item.kind in (NodeKind.DRIVE, NodeKind.DIRECTORY):
            self._load_directory(item, item.path)
        item.loaded = True

    def _load_open_editors(self, parent: ExplorerTreeItem):
        docs = self._explorer_model.open_documents
        if not docs:
            self._add_placeholder(parent, "无打开文件")
            return
        for doc in docs:
            path = doc.get("path", "")
            if not path:
                continue
            name = os.path.basename(path) or path
            is_active = doc.get("is_active", False)
            label = f"{name} {'(活动)' if is_active else ''}".strip()
            parent.append(
                ExplorerTreeItem(
                    kind=NodeKind.OPEN_DOC,
                    name=label,
                    path=path,
                    icon="📄",
                    payload={"is_active": is_active},
                )
            )

    def _load_current_project(self, parent: ExplorerTreeItem):
        path = self._explorer_model.project_root
        parent.name = f"当前项目{ExplorerModel.project_basename(path)}"
        if not path or not os.path.isdir(path):
            self._add_placeholder(parent, "未选择文件夹")
            return
        self._load_directory(parent, path)

    def _load_recent_projects(self, parent: ExplorerTreeItem):
        projects = self._explorer_model.recent_projects
        if not projects:
            self._add_placeholder(parent, "无最近项目")
            return
        for project in projects:
            path = project.get("path", "") if isinstance(project, dict) else str(project)
            path = ExplorerModel.normalize_path(path)
            if not path:
                continue
            name = ExplorerModel.project_basename(path).replace(" — ", "") or path
            parent.append(
                ExplorerTreeItem(
                    kind=NodeKind.RECENT_ITEM,
                    name=name,
                    path=path,
                    icon="📂",
                    tooltip=path,
                )
            )

    def _load_this_pc(self, parent: ExplorerTreeItem):
        drives = ExplorerModel.get_drives()
        if not drives:
            self._add_placeholder(parent, "未检测到驱动器")
            return
        for drive in drives:
            child = ExplorerTreeItem(
                kind=NodeKind.DRIVE,
                name=drive,
                path=drive,
                icon="💾",
            )
            parent.append(child)
            self._add_placeholder(child, "加载中...")

    def _load_global_config(self, parent: ExplorerTreeItem):
        entries = self._explorer_model.list_global_config()
        if not entries:
            self._add_placeholder(parent, "未配置或空目录")
            return
        for entry in entries:
            parent.append(
                ExplorerTreeItem(
                    kind=NodeKind.CONFIG_ITEM,
                    name=entry["name"],
                    path=entry["path"],
                    icon="⚙️" if entry.get("is_file") else "📁",
                )
            )

    def _load_directory(self, parent: ExplorerTreeItem, path: str):
        result = self._explorer_model.list_directory(path)
        dirs, files = result["dirs"], result["files"]
        if not dirs and not files:
            self._add_placeholder(parent, "空目录")
            return
        for entry in dirs:
            child = ExplorerTreeItem(
                kind=NodeKind.DIRECTORY,
                name=entry["name"],
                path=entry["path"],
                icon="📁",
            )
            parent.append(child)
            self._add_placeholder(child, "加载中...")
        for entry in files:
            parent.append(
                ExplorerTreeItem(
                    kind=NodeKind.FILE,
                    name=entry["name"],
                    path=entry["path"],
                    icon="📄",
                )
            )

    def _add_placeholder(self, parent: ExplorerTreeItem, text: str):
        parent.append(
            ExplorerTreeItem(
                kind=NodeKind.PLACEHOLDER,
                name=text,
                icon="",
            )
        )

    # ═══════════════════════════════════════════════════
    # Model 变更回调
    # ═══════════════════════════════════════════════════
    def _on_project_root_changed(self, path: str):
        self.project_root_changed.emit(path)
        self._refresh_all()

    def _on_storage_dir_changed(self, path: str):
        self.storage_dir_changed.emit(path)
        self._refresh_all()

    def _on_recent_projects_changed(self, projects: list):
        self.recent_projects_changed.emit(projects)
        self._refresh_all()

    def _on_open_documents_changed(self, documents: list):
        self.open_documents_changed.emit(documents)
        self._refresh_all()

    # ═══════════════════════════════════════════════════
    # 公共接口
    # ═══════════════════════════════════════════════════
    def item_from_index(self, index: QModelIndex) -> Optional[ExplorerTreeItem]:
        return self._item_from_index(index)

    def category_key_from_index(self, index: QModelIndex) -> Optional[str]:
        item = self._item_from_index(index)
        if item is None:
            return None
        if item.kind == NodeKind.CATEGORY:
            return item.payload.get("category")
        return item.payload.get("category") if item else None

    def reload(self):
        """完全刷新树"""
        self._build_categories()
        self._refresh_all()

    def refresh_item(self, index: QModelIndex):
        """刷新指定节点及其子节点"""
        item = self._item_from_index(index)
        if item is None:
            return
        item.clear()
        item.loaded = False
        self._load_item_children(item)
        self.layoutChanged.emit()
