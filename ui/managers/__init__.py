"""
ui/managers — 多会话管理系统 Manager 模块

导出：
- SessionManager: 会话生命周期管理（CRUD + 切换状态机）
- SessionRegistry: 工作线程注册表（前后台分离核心）
- QueueManager: 双槽位队列状态管理器
- WorkerManager: AgentWorker 生命周期管理器
- PhaseCoordinator: Phase 工作流协调器
"""

from .session_manager import SessionManager, SessionState
from .session_registry import SessionRegistry, SessionSlot, WorkerState
from .queue_manager import QueueManager, QueueState
from .worker_manager import WorkerManager
from .phase_coordinator import PhaseCoordinator

__all__ = [
    "SessionManager",
    "SessionState",
    "SessionRegistry",
    "SessionSlot",
    "WorkerState",
    "QueueManager",
    "QueueState",
    "WorkerManager",
    "PhaseCoordinator",
]
