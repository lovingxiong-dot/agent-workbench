"""runtime.py — v4 会话运行时

每个会话拥有独立的：
- QueueManager（双槽位队列）
- Phase 状态快照
- Environment（环境上下文）
- Worker 引用（由 WorkerManager 注入）

不直接操作 UI，只维护本会话内的业务对象。
"""
from datetime import datetime
from typing import Optional, Dict

from PySide6.QtCore import QObject

from .models import SessionMetadata, Environment
from .queue import QueueManager


class SessionRuntime(QObject):
    """单个会话的完整运行时

    职责：
    - 持有本会话的 QueueManager（独立双槽位）
    - 持有环境上下文（Work 模式）
    - 持有 Worker 引用（由 WorkerManager 注入）
    - 保存 phase 状态快照（用于切回时恢复 UI）

    不操作：
    - 不直接操作 UI
    - 不直接调用 LLM
    - 不直接操作 DB
    """

    def __init__(self, metadata: SessionMetadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self._queue = QueueManager(session_id=metadata.session_id, parent=self)
        self._phase_state: Dict = {}
        self._worker: Optional[object] = None
        self._chunks_received: bool = False
        self._created_at: datetime = datetime.now()

    # ── 属性 ──────────────────────────────────
    @property
    def session_id(self) -> str:
        return self.metadata.session_id

    @property
    def queue(self) -> QueueManager:
        return self._queue

    @property
    def phase_state(self) -> Dict:
        return self._phase_state

    @property
    def worker(self) -> Optional[object]:
        return self._worker

    @property
    def is_chat(self) -> bool:
        return self.metadata.session_type.value == "chat"

    @property
    def is_work(self) -> bool:
        return self.metadata.session_type.value == "work"

    @property
    def environment(self) -> Environment:
        """从 metadata 构建环境（Chat 模式为空，Work 模式使用 project_path）"""
        if self.is_chat:
            return Environment(project_root="")
        return Environment(project_root=self.metadata.project_path)

    # ── Worker 绑定 ──────────────────────────────────
    def attach_worker(self, worker: object) -> None:
        """绑定 Worker"""
        self._worker = worker

    def detach_worker(self) -> None:
        """解绑 Worker"""
        self._worker = None

    # ── Phase 状态快照 ──────────────────────────────────
    def save_phase_state(self, state: Dict) -> None:
        """保存 Phase 状态快照"""
        self._phase_state = dict(state)

    def clear_phase_state(self) -> None:
        """清除 Phase 状态快照"""
        self._phase_state.clear()
