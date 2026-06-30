from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import uuid


class SessionType(Enum):
    CHAT = "chat"    # 纯对话，无环境
    WORK = "work"    # 任务执行，有环境


class TaskPhase(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    ARCHIVING = "archiving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class SessionMetadata:
    """会话元数据（不可变）"""
    session_id: str
    title: str
    session_type: SessionType
    mode: str
    model: str
    project_path: str = ""      # Chat 为空，Work 为项目目录
    pinned: bool = False          # 置顶标记
    updated_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def new(cls, title: str, session_type: str, mode: str, model: str, project_path: str = ""):
        return cls(
            session_id=f"sess_{uuid.uuid4().hex[:16]}",
            title=title,
            session_type=SessionType(session_type) if isinstance(session_type, str) else session_type,
            mode=mode,
            model=model,
            project_path=project_path,
        )


@dataclass(frozen=True)
class Message:
    """消息（不可变，唯一权威来源：DB）"""
    message_id: str
    session_id: str
    role: str       # user / ai / system / tool
    content: str
    tool_calls: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def new(cls, session_id: str, role: str, content: str):
        return cls(
            message_id=f"msg_{uuid.uuid4().hex[:16]}",
            session_id=session_id,
            role=role,
            content=content,
        )


@dataclass(frozen=True)
class Environment:
    """环境（Work 模式才有）"""
    project_root: str
    tools: List[str] = field(default_factory=list)
    interpreter: str = ""
    workspace_context: str = ""

    def is_empty(self) -> bool:
        return not self.project_root


@dataclass(frozen=True)
class TaskState:
    """任务状态快照（用于列表状态徽章）"""
    session_id: str
    phase: TaskPhase
    task_count: int = 0
    current_task: int = 0
    updated_at: datetime = field(default_factory=datetime.now)
