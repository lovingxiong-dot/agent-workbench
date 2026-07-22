"""presentation/protocols/foundation/data.py — Data Contract。

Phase 1: Foundation Contract Freeze。
定义两个产品共同依赖的核心数据模型。

约束：
  ✓ 仅 dataclass + Enum
  ✗ 零 Runtime Implementation import
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import time


# ═══════════════════════════════════════════════════════════════════
# Agent Identity
# ═══════════════════════════════════════════════════════════════════

class AgentType(str, Enum):
    """Agent 类型分类。"""
    CHAT = "chat"
    CODER = "coder"
    RESEARCH = "research"
    PERSONAL = "personal"
    CUSTOM = "custom"


@dataclass
class AgentIdentity:
    """Agent 唯一标识。

    字段：
    - agent_id: Agent 唯一标识。
    - name: 人类可读名称。
    - type: Agent 类型。
    - version: Agent 版本（用于多版本并存）。
    - system_prompt: 系统提示词（可选）。
    - provider: 绑定的 Provider 标识（可选）。
    - model: 绑定的模型标识（可选）。
    - metadata: 扩展元数据。
    """
    agent_id: str
    name: str
    type: AgentType = AgentType.CHAT
    version: str = "1.0.0"
    system_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


# ═══════════════════════════════════════════════════════════════════
# Agent Session
# ═══════════════════════════════════════════════════════════════════

@dataclass
class AgentMessage:
    """会话中的单条消息。"""
    role: str  # "user" | "assistant" | "tool" | "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentSession:
    """Agent 会话状态。

    字段：
    - session_id: 会话标识。
    - agent_id: 关联的 Agent 标识。
    - messages: 消息历史。
    - created_at: 创建时间戳。
    - updated_at: 更新时间戳。
    - title: 会话标题（可选）。
    """
    session_id: str
    agent_id: str
    messages: List[AgentMessage] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    title: Optional[str] = None

    def __post_init__(self) -> None:
        if self.messages is None:
            self.messages = []


# ═══════════════════════════════════════════════════════════════════
# Workflow State
# ═══════════════════════════════════════════════════════════════════

class WorkflowPhase(str, Enum):
    """Workflow 执行阶段。"""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Workflow 单个步骤。"""
    step_id: str
    capability_id: str
    status: WorkflowPhase = WorkflowPhase.PENDING
    input: Dict[str, Any] = field(default_factory=dict)
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class WorkflowState:
    """Workflow 完整状态。

    字段：
    - workflow_id: Workflow 标识。
    - task_id: 关联的 Task 标识。
    - session_id: 关联的 Session 标识。
    - phase: 当前阶段。
    - steps: 步骤列表（按执行顺序）。
    - current_step_index: 当前执行步骤索引。
    - started_at: 启动时间戳。
    - completed_at: 完成时间戳（未完成时为 None）。
    - error: 错误信息（无错误时为 None）。
    """
    workflow_id: str
    task_id: str
    session_id: str
    phase: WorkflowPhase = WorkflowPhase.PENDING
    steps: List[WorkflowStep] = field(default_factory=list)
    current_step_index: int = 0
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.steps is None:
            self.steps = []


# ═══════════════════════════════════════════════════════════════════
# Capability Definition
# ═══════════════════════════════════════════════════════════════════

class CapabilityCategory(str, Enum):
    """Capability 分类。"""
    TOOL = "tool"
    SKILL = "skill"
    WORKFLOW = "workflow"
    MEMORY = "memory"
    PROVIDER = "provider"
    CUSTOM = "custom"


@dataclass
class CapabilityParameter:
    """Capability 参数定义。"""
    name: str
    type: str  # "string" | "number" | "boolean" | "object" | "array"
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass
class CapabilityDefinition:
    """Capability 定义。

    字段：
    - capability_id: Capability 唯一标识。
    - name: 人类可读名称。
    - description: Capability 描述。
    - category: 分类。
    - parameters: 参数定义列表。
    - returns: 返回值类型描述。
    - enabled: 是否启用。
    - version: 版本号。
    """
    capability_id: str
    name: str
    description: str = ""
    category: CapabilityCategory = CapabilityCategory.TOOL
    parameters: List[CapabilityParameter] = field(default_factory=list)
    returns: str = "object"
    enabled: bool = True
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.parameters is None:
            self.parameters = []