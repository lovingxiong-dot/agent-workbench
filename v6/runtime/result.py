"""v6/runtime/result.py — RuntimeResult：运行时最终输出协议。

设计来源：Runtime Kernel 演进方向及 docs/v6/SPEC.md 第 8 节。

核心原则：
- RuntimeResult 保存 Output（answer/tool_result/files/images/error/status 等），不属于 Facts。
- 当前挂载在 RuntimeContext.result 上，未来可平滑迁移到 RuntimeTask.result。
- Gateway/UI/API 最终统一读取 RuntimeResult 作为任务输出。
- 线程安全；所有写操作受锁保护；读取返回深拷贝快照。
"""
from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuntimeResult:
    """Runtime Task 的最终输出容器。

    职责：封装任务完成后对外暴露的所有产物，包括文本回答、工具结果、
    文件/图片产物、错误信息和最终状态。
    """

    answer: str = ""
    tool_result: Optional[Dict[str, Any]] = None
    files: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    error: str = ""
    status: str = "pending"

    # 扩展字段容器，供后续 Gateway / UI 自定义输出格式
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()

    def set_answer(self, text: str) -> None:
        """设置文本回答。"""
        with self._lock:
            self.answer = text

    def add_file(self, path: str) -> None:
        """追加一个文件产物路径。"""
        with self._lock:
            self.files.append(path)

    def add_image(self, path: str) -> None:
        """追加一个图片产物路径。"""
        with self._lock:
            self.images.append(path)

    def add_artifact(self, artifact: Dict[str, Any]) -> None:
        """追加一个结构化产物。"""
        with self._lock:
            self.artifacts.append(copy.deepcopy(artifact))

    def set_error(self, message: str) -> None:
        """设置错误信息，同时把状态置为 failed。"""
        with self._lock:
            self.error = message
            self.status = "failed"

    def set_status(self, status: str) -> None:
        """设置最终状态。"""
        with self._lock:
            self.status = status

    def snapshot(self) -> Dict[str, Any]:
        """返回深拷贝快照，供序列化 / Gateway 返回。"""
        with self._lock:
            return self._make_snapshot()

    def to_dict(self) -> Dict[str, Any]:
        """语义同 snapshot，兼容旧 dict 接口。"""
        return self.snapshot()

    def reset(self) -> None:
        """清空所有输出。"""
        with self._lock:
            self.answer = ""
            self.tool_result = None
            self.files.clear()
            self.images.clear()
            self.artifacts.clear()
            self.error = ""
            self.status = "pending"
            self.extra.clear()

    def _make_snapshot(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "tool_result": copy.deepcopy(self.tool_result) if self.tool_result else None,
            "files": copy.deepcopy(self.files),
            "images": copy.deepcopy(self.images),
            "artifacts": copy.deepcopy(self.artifacts),
            "error": self.error,
            "status": self.status,
            "extra": copy.deepcopy(self.extra),
        }
