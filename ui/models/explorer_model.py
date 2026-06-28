"""
ExplorerModel — 资源管理器数据模型

职责：
- 维护项目根目录、最近项目、打开文档、全局配置目录等状态
- 提供标准化路径、目录扫描、驱动器枚举等数据访问
- 通过 Qt 信号通知 View 数据变化

不依赖具体 UI，可被 ProjectExplorer / Controller 复用。
"""
import os
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal


class ExplorerModel(QObject):
    project_root_changed = Signal(str)
    recent_projects_changed = Signal(list)
    open_documents_changed = Signal(list)
    storage_dir_changed = Signal(str)
    data_changed = Signal()  # 通用刷新信号

    def __init__(self, project_root: str = "", storage_dir: str = "", parent=None):
        super().__init__(parent)
        self._project_root = self._normalize_path(project_root)
        self._storage_dir = self._normalize_path(storage_dir)
        self._recent_projects: List[Dict] = []
        self._open_documents: List[Dict] = []

    # ═══════════════════════════════════════════════════
    # 属性读写
    # ═══════════════════════════════════════════════════
    @property
    def project_root(self) -> str:
        return self._project_root

    def set_project_root(self, path: str):
        path = self._normalize_path(path)
        if path == self._project_root:
            return
        self._project_root = path
        self.project_root_changed.emit(path)
        self.data_changed.emit()

    @property
    def storage_dir(self) -> str:
        return self._storage_dir

    def set_storage_dir(self, path: str):
        path = self._normalize_path(path)
        if path == self._storage_dir:
            return
        self._storage_dir = path
        self.storage_dir_changed.emit(path)
        self.data_changed.emit()

    @property
    def recent_projects(self) -> List[Dict]:
        return list(self._recent_projects)

    def set_recent_projects(self, projects: List):
        parsed = []
        for project in projects or []:
            path = project.get("path", "") if isinstance(project, dict) else str(project)
            path = self._normalize_path(path)
            if path:
                parsed.append({"path": path})
        self._recent_projects = parsed
        self.recent_projects_changed.emit(self._recent_projects)
        self.data_changed.emit()

    @property
    def open_documents(self) -> List[Dict]:
        return list(self._open_documents)

    def set_open_documents(self, documents: List[Dict]):
        """外部（ContextService）批量同步打开文件列表"""
        self._open_documents = documents or []
        self.open_documents_changed.emit(self._open_documents)
        self.data_changed.emit()

    def open_document(self, path: str, is_active: bool = False, preview: str = "", size: int = 0):
        """打开或更新一个文档；若已存在则更新激活状态"""
        path = self._normalize_path(path)
        if not path:
            return
        for doc in self._open_documents:
            if doc.get("path") == path:
                doc["is_active"] = is_active
                doc["preview"] = preview or doc.get("preview", "")
                doc["size"] = size or doc.get("size", 0)
                self._set_single_active(path)
                self.open_documents_changed.emit(self._open_documents)
                self.data_changed.emit()
                return
        self._open_documents.append({
            "path": path,
            "is_active": is_active,
            "preview": preview,
            "size": size,
        })
        self._set_single_active(path)
        self.open_documents_changed.emit(self._open_documents)
        self.data_changed.emit()

    def close_document(self, path: str):
        """关闭指定文档"""
        path = self._normalize_path(path)
        original_len = len(self._open_documents)
        self._open_documents = [d for d in self._open_documents if d.get("path") != path]
        if len(self._open_documents) != original_len:
            # 若关闭的是 active 且还有其他文档，把最后一个设为 active
            if self._open_documents and not any(d.get("is_active") for d in self._open_documents):
                self._open_documents[-1]["is_active"] = True
            self.open_documents_changed.emit(self._open_documents)
            self.data_changed.emit()

    def activate_document(self, path: str):
        """激活指定文档（不重复打开）"""
        path = self._normalize_path(path)
        for doc in self._open_documents:
            if doc.get("path") == path:
                self._set_single_active(path)
                self.open_documents_changed.emit(self._open_documents)
                self.data_changed.emit()
                return
        # 未在列表中则视为打开
        self.open_document(path, is_active=True)

    def _set_single_active(self, active_path: str):
        """确保只有一个 active 文档"""
        for doc in self._open_documents:
            doc["is_active"] = doc.get("path") == active_path

    # ═══════════════════════════════════════════════════
    # 数据查询
    # ═══════════════════════════════════════════════════
    @staticmethod
    def get_drives() -> List[str]:
        """枚举 Windows 驱动器"""
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives

    @staticmethod
    def list_directory(path: str) -> Dict[str, List[Dict]]:
        """列出目录内容，返回 {"dirs": [...], "files": [...]}"""
        dirs, files = [], []
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            return {"dirs": [], "files": []}

        for name in entries:
            full = os.path.join(path, name)
            entry = {"name": name, "path": full}
            if os.path.isdir(full):
                dirs.append(entry)
            else:
                files.append(entry)
        return {"dirs": dirs, "files": files}

    def list_global_config(self) -> List[Dict]:
        """列出全局配置目录内容"""
        path = self._storage_dir
        if not path or not os.path.isdir(path):
            return []
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            return []
        return [
            {"name": name, "path": os.path.join(path, name), "is_file": os.path.isfile(os.path.join(path, name))}
            for name in entries
        ]

    # ═══════════════════════════════════════════════════
    # 文件系统操作（供 View/Controller 调用）
    # ═══════════════════════════════════════════════════
    @staticmethod
    def create_file(parent_path: str, name: str) -> tuple[bool, str]:
        """在指定目录下创建空文件，返回 (success, message_or_path)"""
        if not parent_path or not os.path.isdir(parent_path):
            return False, "父目录不存在"
        name = name.strip()
        if not name:
            return False, "文件名不能为空"
        full = os.path.join(parent_path, name)
        if os.path.exists(full):
            return False, f"已存在: {name}"
        try:
            open(full, "a", encoding="utf-8").close()
            return True, full
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_folder(parent_path: str, name: str) -> tuple[bool, str]:
        """在指定目录下创建文件夹，返回 (success, message_or_path)"""
        if not parent_path or not os.path.isdir(parent_path):
            return False, "父目录不存在"
        name = name.strip()
        if not name:
            return False, "文件夹名不能为空"
        full = os.path.join(parent_path, name)
        if os.path.exists(full):
            return False, f"已存在: {name}"
        try:
            os.makedirs(full, exist_ok=False)
            return True, full
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_path(path: str) -> tuple[bool, str]:
        """删除文件或空文件夹，返回 (success, message)"""
        if not path or not os.path.exists(path):
            return False, "路径不存在"
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                os.rmdir(path)
            else:
                return False, "未知路径类型"
            return True, ""
        except Exception as e:
            return False, str(e)

    @staticmethod
    def rename_path(old_path: str, new_name: str) -> tuple[bool, str]:
        """重命名文件或文件夹，返回 (success, message_or_new_path)"""
        if not old_path or not os.path.exists(old_path):
            return False, "原路径不存在"
        new_name = new_name.strip()
        if not new_name:
            return False, "新名称不能为空"
        parent = os.path.dirname(old_path)
        new_path = os.path.join(parent, new_name)
        if os.path.exists(new_path):
            return False, f"目标已存在: {new_name}"
        try:
            os.rename(old_path, new_path)
            return True, new_path
        except Exception as e:
            return False, str(e)

    # ═══════════════════════════════════════════════════
    # 路径工具
    # ═══════════════════════════════════════════════════
    @staticmethod
    def normalize_path(path: str) -> str:
        return ExplorerModel._normalize_path(path)

    @staticmethod
    def _normalize_path(path: str) -> str:
        if not path:
            return ""
        try:
            return os.path.normpath(os.path.abspath(os.path.expandvars(path)))
        except Exception:
            return path

    @staticmethod
    def display_path(path: str) -> str:
        if not path:
            return "未选择文件夹"
        try:
            home = os.path.expanduser("~")
            if path.lower().startswith(home.lower()):
                return "~" + path[len(home):]
        except Exception:
            pass
        return path

    @staticmethod
    def project_basename(path: str) -> str:
        if not path:
            return ""
        name = os.path.basename(path) or path
        return f" — {name}"
