"""agent_workbench/runtime/capability/context.py — Capability 运行时上下文契约。

设计约束：
- CapabilityContext 只描述能力执行时的环境上下文，不携带 Capability 本身定义。
- 所有子上下文都是 typed dataclass，禁止做成万能 Dict。
- RuntimeRequest.source 只映射到 CapabilityContext.origin，不参与 Capability 路由决策。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from agent_workbench.runtime.capability.model import CapabilityDefinition


@dataclass
class WorkspaceContext:
    """工作空间上下文。"""

    workspace_id: str | None = None
    project_root: str | None = None
    open_files: list[str] = field(default_factory=list)
    git_branch: str | None = None
    git_commit: str | None = None
    terminal: dict[str, Any] = field(default_factory=dict)


@dataclass
class AttachmentContext:
    """附件上下文。"""

    items: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SelectionContext:
    """用户当前选中的内容上下文。"""

    path: str | None = None
    range: dict[str, Any] = field(default_factory=dict)
    text: str | None = None


@dataclass
class ExecutionContext:
    """能力执行参数上下文。"""

    parameters: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityContext:
    """Capability 执行时的完整环境上下文。

    - origin: 请求来源，仅用于追踪，不进入 Capability 路由。
    - workspace: 工作空间上下文。
    - attachments: 附件上下文。
    - selection: 用户选中内容上下文。
    - execution: 执行参数与环境上下文。
    """

    origin: str = ""
    workspace: WorkspaceContext = field(default_factory=WorkspaceContext)
    attachments: AttachmentContext = field(default_factory=AttachmentContext)
    selection: SelectionContext = field(default_factory=SelectionContext)
    execution: ExecutionContext = field(default_factory=ExecutionContext)


class CapabilityContextBuilder(Protocol):
    """从 RuntimeRequest / UserRequest 构建 CapabilityContext 的协议。

    注意：不命名为 Provider，避免与 Provider Runtime 的 Provider 概念混淆。
    """

    def build(
        self,
        definition: CapabilityDefinition,
        request: Any,
    ) -> CapabilityContext: ...


class DefaultCapabilityContextBuilder:
    """默认 Builder：从 request 提取 source 作为 origin，其余字段保持为空。

    这是 v6.9.6-alpha 的最小实现；Workspace Runtime 阶段再扩展 workspace/selection。
    """

    def build(
        self,
        definition: CapabilityDefinition,
        request: Any,
    ) -> CapabilityContext:
        origin = ""
        if hasattr(request, "source"):
            origin = request.source.value if hasattr(request.source, "value") else str(request.source)
        elif hasattr(request, "metadata") and isinstance(request.metadata, dict):
            source = request.metadata.get("source")
            origin = source.value if hasattr(source, "value") else str(source) if source is not None else ""
        return CapabilityContext(origin=origin)
