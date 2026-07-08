"""agent_workbench/runtime/capability/model.py — Capability 运行时数据契约。

设计约束：
- 所有类型均为纯数据对象（dataclass），禁止携带 Runtime 状态。
- CapabilityDefinition 描述能力「是什么、能做什么、如何映射到 Engine」，不做执行。
- CapabilityMatch / CapabilityIntent 用于 Manager 路由阶段，不进入 Engine。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CapabilityCategory(str, Enum):
    """能力类别：Runtime 对能力的静态分类。"""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    BROWSER = "browser"
    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    TOOL = "tool"
    MCP = "mcp"
    UNKNOWN = "unknown"


class CapabilityMode(str, Enum):
    """能力支持的 Runtime 模式。"""

    CHAT = "chat"
    ACTION = "action"
    WORKFLOW = "workflow"


@dataclass
class CapabilityPersona:
    """能力人格：作为 metadata 策略，为 Agent Identity 奠基。

    第一版仅包含静态描述；不绑定具体 Provider 或 Runtime 状态。
    """

    role: str = ""
    style: str = ""
    preferred_tools: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "style": self.style,
            "preferred_tools": list(self.preferred_tools),
            "constraints": list(self.constraints),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityPersona:
        return cls(
            role=data.get("role", ""),
            style=data.get("style", ""),
            preferred_tools=list(data.get("preferred_tools", [])),
            constraints=list(data.get("constraints", [])),
        )


@dataclass
class CapabilityDefinition:
    """能力定义：Runtime 对能力的唯一静态描述。

    字段说明：
    - id: 全局唯一能力标识，建议使用点分命名空间（如 coding.python.debugging）。
    - name: 人类可读名称。
    - summary: 一句话能力摘要。
    - description: 能力描述。
    - category: 能力类别（text/image/video/code/...）。
    - version: 能力版本。
    - provider_type: 推荐 Provider 类型（llm/tool/local_agent/mcp）。
    - supported_modes: 支持的 Runtime 模式（chat/action/workflow）。
    - priority: 同类别下选择优先级。
    - providers: 该能力可选的 Provider 列表（仅声明，不控制执行）。
    - input_schema / output_schema: 输入输出 JSON Schema 声明。
    - permissions: 能力所需权限标签。
    - cost / latency: 成本与延迟元数据（仅声明）。
    - parent_id: 父能力 id，用于构建能力树。
    - keywords: 用于 Intent 匹配的关键词。
    - engine_capability: 映射到 EngineManager 的 capability（如 text_generation）。
    - persona: 可选能力人格。
    """

    id: str
    name: str = ""
    summary: str = ""
    description: str = ""
    category: CapabilityCategory = CapabilityCategory.UNKNOWN
    version: str = "1.0.0"
    provider_type: str = ""
    supported_modes: list[CapabilityMode] = field(default_factory=list)
    priority: int = 0
    providers: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)
    cost: dict[str, Any] = field(default_factory=dict)
    latency: dict[str, Any] = field(default_factory=dict)
    parent_id: str | None = None
    keywords: list[str] = field(default_factory=list)
    engine_capability: str = ""
    persona: CapabilityPersona | None = None

    def to_dict(self) -> dict[str, Any]:
        """序列化为可 JSON 序列化的 dict。"""
        return {
            "id": self.id,
            "name": self.name,
            "summary": self.summary,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "provider_type": self.provider_type,
            "supported_modes": [mode.value for mode in self.supported_modes],
            "priority": self.priority,
            "providers": list(self.providers),
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
            "permissions": list(self.permissions),
            "cost": dict(self.cost),
            "latency": dict(self.latency),
            "parent_id": self.parent_id,
            "keywords": list(self.keywords),
            "engine_capability": self.engine_capability,
            "persona": self.persona.to_dict() if self.persona is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityDefinition:
        """从 dict 反序列化。"""
        persona_data = data.get("persona")
        persona = CapabilityPersona.from_dict(persona_data) if persona_data is not None else None
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            category=CapabilityCategory(data.get("category", CapabilityCategory.UNKNOWN.value)),
            version=data.get("version", "1.0.0"),
            provider_type=data.get("provider_type", ""),
            supported_modes=[CapabilityMode(m) for m in data.get("supported_modes", [])],
            priority=data.get("priority", 0),
            providers=list(data.get("providers", [])),
            input_schema=dict(data.get("input_schema", {})),
            output_schema=dict(data.get("output_schema", {})),
            permissions=list(data.get("permissions", [])),
            cost=dict(data.get("cost", {})),
            latency=dict(data.get("latency", {})),
            parent_id=data.get("parent_id"),
            keywords=list(data.get("keywords", [])),
            engine_capability=data.get("engine_capability", ""),
            persona=persona,
        )


@dataclass
class CapabilityMatch:
    """Manager 路由结果：能力匹配项。

    - definition: 命中能力定义。
    - score: 匹配分数（0~1）。
    - lineage: 从根到该节点的路径 id 列表。
    """

    definition: CapabilityDefinition
    score: float = 0.0
    lineage: list[str] = field(default_factory=list)


@dataclass
class CapabilityIntent:
    """Manager 输入意图：从 UserRequest 提取的结构化请求。

    - text: 用户原始文本。
    - metadata: 附加上下文（如会话、项目路径、历史能力）。
    - required_permissions: 请求方声明的必需权限。
    - preferred_providers: 请求方偏好的 Provider 列表。
    """

    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    required_permissions: list[str] = field(default_factory=list)
    preferred_providers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "metadata": dict(self.metadata),
            "required_permissions": list(self.required_permissions),
            "preferred_providers": list(self.preferred_providers),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityIntent:
        return cls(
            text=data.get("text", ""),
            metadata=dict(data.get("metadata", {})),
            required_permissions=list(data.get("required_permissions", [])),
            preferred_providers=list(data.get("preferred_providers", [])),
        )
