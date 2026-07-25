"""v6/runtime/execution_control.py — 执行控制容器。

Phase 3.11-A: ExecutionControl 抽象。
设计文档：docs/v6/phase3-11-a-execution-model-design.md

核心原则：
- ExecutionControl 是控制令牌的聚合容器，避免 CancellationToken 成为孤立模块。
- 使用 threading.Event 实现协作式取消（非 thread.kill()）。
- 未来扩展：PauseToken、CheckpointToken。
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


class TaskCancelledError(Exception):
    """任务被取消时抛出的异常。"""

    def __init__(self, task_id: str = "", reason: str = "") -> None:
        self.task_id = task_id
        self.reason = reason
        super().__init__(
            f"Task {task_id} cancelled: {reason}" if task_id else f"Task cancelled: {reason}"
        )


class CancellationToken:
    """协作式取消令牌。

    设计原则：
    - 不使用 thread.kill()（Python 不支持安全 kill）
    - Worker 线程定期检查 token，主动停止
    - 取消信号通过 threading.Event 传播
    """

    def __init__(self) -> None:
        self._event = threading.Event()
        self._reason: str = ""

    def cancel(self, reason: str = "") -> None:
        """设置取消信号，唤醒所有等待线程。

        首次 cancel 时记录原因，后续调用保留首次原因。
        """
        if reason and not self._reason:
            self._reason = reason
        self._event.set()

    def is_cancelled(self) -> bool:
        """检查是否已被取消。"""
        return self._event.is_set()

    @property
    def reason(self) -> str:
        """取消原因。"""
        return self._reason

    def raise_if_cancelled(self) -> None:
        """若已取消则抛出 TaskCancelledError。"""
        if self._event.is_set():
            raise TaskCancelledError(reason=self._reason)

    def wait(self, timeout: Optional[float] = None) -> bool:
        """阻塞等待取消信号，返回是否被取消（True=已取消，False=超时）。"""
        return self._event.wait(timeout=timeout)


@dataclass
class ExecutionControl:
    """执行控制容器。

    聚合所有执行控制令牌，避免 CancellationToken 成为孤立模块。
    未来扩展：
        - pause: PauseToken
        - checkpoint: CheckpointToken
    """

    cancellation: CancellationToken = field(default_factory=CancellationToken)

    # Future:
    # pause: PauseToken = field(default_factory=PauseToken)
    # checkpoint: CheckpointToken = field(default_factory=CheckpointToken)

    @property
    def is_cancelled(self) -> bool:
        """快捷方式：检查是否已取消。"""
        return self.cancellation.is_cancelled()

    def cancel(self, reason: str = "") -> None:
        """快捷方式：发送取消信号。"""
        self.cancellation.cancel(reason)

    def raise_if_cancelled(self) -> None:
        """快捷方式：若已取消则抛出异常。"""
        self.cancellation.raise_if_cancelled()