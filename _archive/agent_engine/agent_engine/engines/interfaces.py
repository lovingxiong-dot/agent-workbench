"""
Agent Workbench AI Engine Interfaces

定义八引擎的抽象接口，每个引擎通过依赖注入获得 config/memory/llm 等外部依赖。

设计原则：
- 接口与实现分离：每个引擎定义清晰的输入/输出契约
- 依赖注入：引擎通过构造函数注入依赖，而非全局单例
- 可测试性：所有接口可 Mock，支持独立单元测试
- 闭环反馈：关键引擎（Context/Inference/Memory/Metrics）通过 MetricsEngine 上报数据
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, AsyncIterator


# ═══════════════════════════════════════════════════════
# 共享数据类型
# ═══════════════════════════════════════════════════════

@dataclass
class Message:
    """标准化消息格式，桥接 LangChain 与引擎"""
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None

    def to_langchain(self):
        """转换为 LangChain 消息"""
        from langchain_core.messages import (
            SystemMessage, HumanMessage, AIMessage, ToolMessage
        )
        if self.role == "system":
            return SystemMessage(content=self.content)
        elif self.role == "user":
            return HumanMessage(content=self.content)
        elif self.role == "assistant":
            if self.tool_calls:
                return AIMessage(content=self.content, tool_calls=self.tool_calls)
            return AIMessage(content=self.content)
        elif self.role == "tool":
            return ToolMessage(content=self.content, tool_call_id=self.tool_call_id or "")
        return HumanMessage(content=self.content)


@dataclass
class TokenUsage:
    """token 用量，不可变"""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class InferenceMetrics:
    """推理指标"""
    model_id: str = ""
    provider: str = ""
    success: bool = True
    error_code: str = ""
    ttft_ms: int = 0          # Time To First Token
    total_ms: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)


@dataclass
class ToolCall:
    """工具调用请求"""
    name: str
    args: Dict[str, Any]
    call_id: str = ""


@dataclass
class ToolResult:
    """工具执行结果"""
    name: str
    result: str
    elapsed_ms: int = 0
    success: bool = True


class CompressionStrategy(str, Enum):
    SLIDING_WINDOW = "sliding_window"
    SEMANTIC_SUMMARY = "semantic_summary"
    ENTITY_PRESERVE = "entity_preserve"
    HYBRID = "hybrid"


@dataclass
class CompressionResult:
    """上下文压缩结果"""
    messages: List[Message]
    compression_ratio: float = 0.0
    summary_text: Optional[str] = None
    preserved_entities: List[str] = field(default_factory=list)
    quality_score: float = 1.0


# ═══════════════════════════════════════════════════════
# 引擎接口
# ═══════════════════════════════════════════════════════

class IContextEngine(ABC):
    """上下文引擎：消息组装、上下文压缩、历史管理"""

    @abstractmethod
    def build_context(
        self,
        user_input: str,
        chat_history: List[Message],
        system_prompt: str,
        max_tokens: int,
        compression_strategy: CompressionStrategy = CompressionStrategy.HYBRID,
    ) -> List[Message]:
        """构建上下文：组装 system + history + user，按需压缩"""
        pass

    @abstractmethod
    def estimate_tokens(self, messages: List[Message]) -> int:
        """估算 token 数量"""
        pass

    @abstractmethod
    def compress(
        self,
        messages: List[Message],
        target_tokens: int,
        strategy: CompressionStrategy = CompressionStrategy.HYBRID,
        guidance: str = "",
    ) -> CompressionResult:
        """压缩消息列表到目标 token 数量"""
        pass

    @abstractmethod
    def report_compression_quality(self, quality_score: float) -> None:
        """【闭环】接收压缩质量反馈"""
        pass


class IPromptEngine(ABC):
    """Prompt 引擎：System Prompt 构建、模板渲染、用户画像注入"""

    @abstractmethod
    def build_system_prompt(
        self,
        mode: str,
        phase: str = "execute",
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """构建完整 system prompt（基础 + 模式覆盖 + Phase 覆盖 + 画像注入）"""
        pass

    @abstractmethod
    def build_identity_block(self) -> str:
        """构建 AI 身份声明块"""
        pass

    @abstractmethod
    def build_user_rules_block(self) -> str:
        """构建用户规则块"""
        pass

    @abstractmethod
    def inject_context(self, base_prompt: str, workspace_context: str) -> str:
        """注入工作区上下文到 prompt"""
        pass


class IInferenceEngine(ABC):
    """推理引擎：LLM 调用、流式处理、超时管理、重试策略"""

    @abstractmethod
    async def invoke(
        self,
        messages: List[Message],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 90.0,
        cancel_event=None,
    ) -> tuple[str, InferenceMetrics]:
        """非流式调用，带重试和降级"""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        model_id: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        timeout: float = 90.0,
        cancel_event=None,
    ) -> AsyncIterator[str]:
        """流式生成，支持取消和指标采集"""
        pass

    @abstractmethod
    def report_metrics(self, metrics: InferenceMetrics) -> None:
        """【闭环】上报推理指标"""
        pass


class IToolEngine(ABC):
    """工具引擎：工具注册、权限校验、执行编排、结果处理"""

    @abstractmethod
    def register(self, name: str, func: Callable, definition: Dict) -> None:
        """注册工具"""
        pass

    @abstractmethod
    async def call(self, name: str, args: Dict[str, Any], phase: str = "execute") -> ToolResult:
        """调用工具（含权限校验 + 超时）"""
        pass

    @abstractmethod
    def bind_for_phase(self, phase: str, llm) -> Any:
        """按 Phase 绑定工具到 LLM"""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Callable]:
        """按名称获取工具"""
        pass


class IPhaseEngine(ABC):
    """阶段引擎：Phase 定义、流转、Checkpoint、插件扩展"""

    @abstractmethod
    def define(self, mode: str, phases: List[str]) -> None:
        """定义某个 Mode 的 Phase 流程"""
        pass

    @abstractmethod
    def next(self, mode: str, current_phase: str) -> Optional[str]:
        """获取下一个 Phase"""
        pass

    @abstractmethod
    def add_plugin(self, phase_name: str, plugin: Callable) -> None:
        """注册 Phase 插件（扩展点）"""
        pass

    @abstractmethod
    def validate(self, phase: str, can_proceed: bool) -> bool:
        """校验 Phase 是否可通过"""
        pass


class IMemoryEngine(ABC):
    """记忆引擎：三层记忆管理（短期/长期/画像）、检索、压缩"""

    @abstractmethod
    def store(self, session_id: str, messages: List[Message]) -> None:
        """存储会话记忆"""
        pass

    @abstractmethod
    def retrieve(self, session_id: str, query: str, top_k: int = 5) -> List[Message]:
        """检索相关记忆"""
        pass

    @abstractmethod
    def get_profile(self) -> Dict[str, Any]:
        """获取用户画像"""
        pass

    @abstractmethod
    def update_profile(self, updates: Dict[str, Any]) -> None:
        """更新用户画像"""
        pass

    @abstractmethod
    def build_context_block(self) -> str:
        """构建记忆上下文块（注入 prompt）"""
        pass


class IMetricsEngine(ABC):
    """指标引擎：指标采集、聚合、分析、告警"""

    @abstractmethod
    def record(
        self, namespace: str, name: str, value: Any, tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录指标"""
        pass

    @abstractmethod
    def get(self, namespace: str, name: str, aggregation: str = "avg") -> Any:
        """查询聚合指标"""
        pass

    @abstractmethod
    def subscribe(self, metric_name: str, threshold: float, callback: Callable) -> None:
        """订阅指标阈值告警"""
        pass


class IPolicyEngine(ABC):
    """策略引擎：配置管理、策略决策、A/B 测试"""

    @abstractmethod
    def get(self, path: str, default: Any = None) -> Any:
        """按路径获取配置值"""
        pass

    @abstractmethod
    def get_for_mode(self, mode: str, key: str) -> Any:
        """获取指定 Mode 的配置值"""
        pass

    @abstractmethod
    def select_model(self, query_features: Dict[str, Any]) -> str:
        """基于查询特征选择最优模型"""
        pass

    @abstractmethod
    def should_compress(self, session_metrics: Dict[str, Any]) -> bool:
        """基于会话指标决定是否触发压缩"""
        pass

    @abstractmethod
    def reload(self) -> None:
        """热加载配置"""
        pass
