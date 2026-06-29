"""
SessionTask — 跨会话后台任务状态模型

设计原则：
- Worker 生命周期独立于 UI，切会话不停止 Worker
- 每个 Session 可有一个活跃任务，状态持久化到 SessionTask
- Phase 状态保存在 SessionTask 中，切回时恢复 Confirm 界面
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
import json


class TaskStatus(str, Enum):
    """任务生命周期状态"""
    QUEUED = "queued"               # 排队等待 Worker
    ANALYZING = "analyzing"         # 正在分析
    EXECUTING = "executing"         # 正在执行
    VERIFYING = "verifying"         # 正在验证
    AWAITING_CONFIRM = "confirm"    # 等待用户确认
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"               # 执行失败


@dataclass
class SessionTask:
    """单个会话的后台任务状态快照

    不持有 AgentWorker / AgentSession 实例，只记录状态和引用。
    Worker 实例由 WorkerPool 管理。

    状态写操作必须由 TaskService 发起，禁止外部直接修改 status。
    """
    session_id: str
    mode: str = "ask"
    user_input: str = ""
    created_at: str = ""
    updated_at: str = ""

    # Phase 状态：用于切回时恢复 UI
    phase: str = "idle"                         # PhaseManager 当前阶段
    task_list_json: str = ""                    # TaskItem 列表的 JSON，恢复 Confirm UI
    phase_context_json: str = ""                 # PhaseContext 的 JSON

    # Worker 引用（由 WorkerPool 注入）
    worker_id: Optional[str] = None

    # 统计
    tool_calls_count: int = 0
    error_count: int = 0
    last_error: str = ""

    # 内部状态：外部应通过 TaskService 修改
    _status: TaskStatus = field(default=TaskStatus.QUEUED, repr=False)

    @property
    def status(self) -> TaskStatus:
        return self._status

    def _set_status(self, value: TaskStatus):
        """内部方法：仅允许 TaskService 调用。"""
        self._status = value

    @property
    def is_active(self) -> bool:
        return self.status in (
            TaskStatus.ANALYZING,
            TaskStatus.EXECUTING,
            TaskStatus.VERIFYING,
            TaskStatus.AWAITING_CONFIRM,
        )

    @property
    def is_waiting(self) -> bool:
        return self.status == TaskStatus.QUEUED

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)

    @property
    def task_list(self) -> List:
        """反序列化 TaskItem 列表"""
        if not self.task_list_json:
            return []
        try:
            return json.loads(self.task_list_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @task_list.setter
    def task_list(self, items: List):
        self.task_list_json = json.dumps(
            [{"id": getattr(i, "id", ""), "description": getattr(i, "description", "")} for i in items],
            ensure_ascii=False,
        )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "status": self.status.value,
            "user_input": self.user_input,
            "phase": self.phase,
            "task_list_json": self.task_list_json,
            "phase_context_json": self.phase_context_json,
            "worker_id": self.worker_id,
            "tool_calls_count": self.tool_calls_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionTask":
        return cls(
            session_id=data.get("session_id", ""),
            mode=data.get("mode", "ask"),
            _status=TaskStatus(data.get("status", "queued")),
            user_input=data.get("user_input", ""),
            phase=data.get("phase", "idle"),
            task_list_json=data.get("task_list_json", ""),
            phase_context_json=data.get("phase_context_json", ""),
            worker_id=data.get("worker_id"),
            tool_calls_count=data.get("tool_calls_count", 0),
            error_count=data.get("error_count", 0),
            last_error=data.get("last_error", ""),
        )
