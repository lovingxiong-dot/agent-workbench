"""
ContextService — 会话上下文服务

作为 Agent 感知用户当前工作空间的单一真相源：
- 当前项目根目录（Project Root）
- 右侧文档区当前活动文件
- 右侧已打开文件列表
- 资源管理器中选中项

提供 build_prompt_context() 生成可注入 LLM prompt 的文本摘要。
"""
import os
from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from services.project_service import ProjectService
from services.path_resolver import resolve_path


@dataclass
class DocumentContext:
    """文档上下文对象"""
    path: str
    size: int = 0
    preview: str = ""
    is_active: bool = False


class ContextService(QObject):
    """维护当前会话上下文，供 UI 和 Agent 共享"""

    context_changed = Signal()

    # 摘要长度上限
    PREVIEW_MAX_LEN = 500

    def __init__(self, project_service: ProjectService, parent=None):
        super().__init__(parent)
        self._project_service = project_service
        self._project_root = ""
        self._active_document: Optional[DocumentContext] = None
        self._open_documents: List[DocumentContext] = []
        self._selected_paths: List[str] = []

    # ═══════════════════════════════════════════════════
    # 项目根目录
    # ═══════════════════════════════════════════════════
    def set_project_root(self, path: str):
        """设置当前项目根目录"""
        path = self._project_service.normalize_path(path) if path else ""
        if path == self._project_root:
            return
        self._project_root = path
        # 切换项目时清空文档上下文，避免旧项目文件残留
        self._active_document = None
        self._open_documents.clear()
        self._selected_paths.clear()
        self.context_changed.emit()

    def get_project_root(self) -> str:
        return self._project_root

    # ═══════════════════════════════════════════════════
    # 活动文档
    # ═══════════════════════════════════════════════════
    def set_active_document(self, path: str, preview: str = "", size: int = 0):
        """设置当前活动文档（右侧当前显示的文件）"""
        path = self._normalize(path)
        if not path:
            return
        preview = self._truncate_preview(preview)
        # 如果已经在打开列表中，更新它并标记为 active
        existing = self._find_doc(path)
        if existing:
            existing.preview = preview
            existing.size = size
            existing.is_active = True
        else:
            doc = DocumentContext(path=path, size=size, preview=preview, is_active=True)
            self._open_documents.append(doc)
        # 取消其他文档的 active 标记
        for doc in self._open_documents:
            if doc.path != path:
                doc.is_active = False
        self._active_document = self._find_doc(path)
        self.context_changed.emit()

    def clear_active_document(self):
        """清除活动文档（例如关闭所有文档时）"""
        self._active_document = None
        for doc in self._open_documents:
            doc.is_active = False
        self.context_changed.emit()

    # ═══════════════════════════════════════════════════
    # 打开文档列表
    # ═══════════════════════════════════════════════════
    def add_open_document(self, path: str, preview: str = "", size: int = 0):
        """右侧打开新文档时调用"""
        path = self._normalize(path)
        if not path or self._find_doc(path):
            return
        preview = self._truncate_preview(preview)
        doc = DocumentContext(path=path, size=size, preview=preview, is_active=False)
        self._open_documents.append(doc)
        self.context_changed.emit()

    def remove_open_document(self, path: str):
        """右侧关闭文档时调用"""
        path = self._normalize(path)
        self._open_documents = [d for d in self._open_documents if d.path != path]
        if self._active_document and self._active_document.path == path:
            # 若还有其他打开文档，把最后一个设为 active
            if self._open_documents:
                self._open_documents[-1].is_active = True
                self._active_document = self._open_documents[-1]
            else:
                self._active_document = None
        self.context_changed.emit()

    def get_active_document(self) -> Optional[DocumentContext]:
        return self._active_document

    def get_open_documents(self) -> List[DocumentContext]:
        return list(self._open_documents)

    # ═══════════════════════════════════════════════════
    # 选中项
    # ═══════════════════════════════════════════════════
    def set_selected_paths(self, paths: List[str]):
        """设置资源管理器中当前选中的路径列表"""
        normalized = [self._normalize(p) for p in paths if p]
        if normalized == self._selected_paths:
            return
        self._selected_paths = normalized
        self.context_changed.emit()

    def get_selected_paths(self) -> List[str]:
        return list(self._selected_paths)

    # ═══════════════════════════════════════════════════
    # Prompt 上下文构建
    # ═══════════════════════════════════════════════════
    def build_prompt_context(self) -> str:
        """构建注入到 LLM prompt 的当前环境摘要"""
        return self.get_phase_context("default")

    def get_phase_context(self, phase: str) -> str:
        """
        按当前 phase 构建不同的上下文摘要。

        - default / analyze: 完整环境摘要（项目、活动文件、打开文件、选中项）
        - execute: 侧重当前任务相关上下文，附带活动文件
        - verify: 侧重项目根目录和最近修改痕迹
        """
        phase = (phase or "default").lower()

        if phase == "execute":
            return self._build_execute_context()
        if phase == "verify":
            return self._build_verify_context()
        return self._build_default_context()

    def _build_default_context(self) -> str:
        """默认/Analyze 阶段：完整环境摘要"""
        lines = ["[当前工作环境]"]
        project_root = self._project_root or "未设置"
        lines.append(f"项目目录: {project_root}")

        active = self._active_document
        if active:
            rel_path = self._relative_path(active.path)
            lines.append(f"活动文件: {rel_path} ({self._format_size(active.size)})")
            if active.preview:
                lines.append("活动文件摘要:")
                lines.append("---")
                lines.append(active.preview)
                lines.append("---")
        else:
            lines.append("活动文件: 无")

        if self._open_documents:
            rel_paths = [self._relative_path(d.path) for d in self._open_documents]
            lines.append(f"打开文件: {', '.join(rel_paths)}")

        if self._selected_paths:
            rel_paths = [self._relative_path(p) for p in self._selected_paths]
            lines.append(f"选中项: {', '.join(rel_paths)}")

        lines.append("")
        return "\n".join(lines)

    def _build_execute_context(self) -> str:
        """Execute 阶段：精简，只保留项目根目录和活动文件"""
        lines = ["[执行上下文]"]
        project_root = self._project_root or "未设置"
        lines.append(f"项目目录: {project_root}")

        active = self._active_document
        if active:
            rel_path = self._relative_path(active.path)
            lines.append(f"当前操作文件: {rel_path}")
            if active.preview:
                lines.append("文件摘要:")
                lines.append("---")
                lines.append(active.preview[:300])
                lines.append("---")
        lines.append("")
        return "\n".join(lines)

    def _build_verify_context(self) -> str:
        """Verify 阶段：侧重项目信息"""
        lines = ["[验证上下文]"]
        project_root = self._project_root or "未设置"
        lines.append(f"项目目录: {project_root}")
        if self._open_documents:
            rel_paths = [self._relative_path(d.path) for d in self._open_documents]
            lines.append(f"已修改/打开文件: {', '.join(rel_paths)}")
        lines.append("")
        return "\n".join(lines)

    # ═══════════════════════════════════════════════════
    # 路径解析（供工具使用）
    # ═══════════════════════════════════════════════════
    def resolve_path(self, path: str) -> str:
        """基于当前 project_root 解析路径"""
        return resolve_path(path, self._project_root)

    # ═══════════════════════════════════════════════════
    # 内部辅助
    # ═══════════════════════════════════════════════════
    def _normalize(self, path: str) -> str:
        if not path:
            return ""
        return self._project_service.normalize_path(path)

    def _find_doc(self, path: str) -> Optional[DocumentContext]:
        for doc in self._open_documents:
            if doc.path == path:
                return doc
        return None

    def _truncate_preview(self, text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        if len(text) <= self.PREVIEW_MAX_LEN:
            return text
        return text[: self.PREVIEW_MAX_LEN] + "\n[... 已截断]"

    def _relative_path(self, path: str) -> str:
        """尝试返回相对于 project_root 的路径"""
        if not self._project_root or not path:
            return path
        try:
            return os.path.relpath(path, self._project_root)
        except Exception:
            return path

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} bytes"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size / (1024 * 1024):.1f} MB"
