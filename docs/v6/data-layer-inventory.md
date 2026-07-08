# V6 数据层清单与分类

> 本清单用于在接入 UI 之前，先理清所有数据实体、持久化服务、运行时状态容器及其测试覆盖情况。任何 UI 展示的数据都必须能追溯到本清单中的某一项。

## 分类说明

| 分类 | 含义 | 是否持久化 |
|---|---|---|
| **配置数据 (Config)** | 应用设置、用户偏好、Provider 配置 | YAML /  SQLite |
| **会话数据 (Session)** | 会话列表、消息历史、会话状态 | SQLite |
| **项目/工作区数据 (Workspace)** | 项目路径、工作区快照、文件选择 | 内存 + 文件系统 |
| **Runtime 事实数据 (Runtime Facts)** | 单次任务执行期间的完整状态容器 | 内存（可序列化） |
| **能力契约数据 (Capability Contract)** | 能力定义、状态、上下文、意图 | 内存 / 注册表 |
| **Provider/Tool 注册数据 (Registry)** | Provider、Tool、Skill 的注册与配置 | 内存 + 配置 |
| **Trace/Metric 数据 (Observability)** | 执行轨迹、指标、结果 | 内存（未来归档） |

---

## 一、配置数据 (Config)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `v6/config_manager.py` | `ConfigManager` | `storage/config.yaml` | 应用配置：主题、最后模式/模型、窗口几何。点分路径 get/set，深度合并默认值。 | `tests/v6/test_v6_config_manager.py` |
| `v6/services/config_service.py` | `ConfigService` | 同上 | ConfigManager 的业务服务封装，面向 RuntimeContext 的 `apply` / `persist`。 | `tests/v6/test_v6_services.py` |

**关键字段**：`theme.name`, `app.last_mode`, `app.last_model`, `window.geometry`

---

## 二、会话数据 (Session)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `v6/session_manager.py` | `SessionManager` | `storage/sessions.db` | 会话 CRUD、active 管理、时间分组、置顶。 | `tests/v6/test_v6_session_manager.py` |
| `v6/services/session_service.py` | `SessionService` | 同上 | SessionManager 的业务服务封装，面向 RuntimeContext。 | `tests/v6/test_v6_services.py` |
| `v6/services/chat_service.py` | `ChatService` | 复用 `sessions.db` | 消息历史读写，追加时同步刷新会话 preview。 | `tests/v6/test_v6_services.py` |

**数据库表**：
- `sessions(id, title, preview, updated_at, created_at, is_active, is_pinned)`
- `messages(id, sid, role, content, created_at)`

---

## 三、项目/工作区数据 (Workspace)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `v6/_paths.py` | `data_dir()` / `project_dir()` | 文件系统 | 数据目录与项目路径解析。 | 间接覆盖 |
| `services/project_service.py` | `ProjectService` | 文件系统 + 内存 | V5 项目服务，管理项目路径与上下文。 | `tests/test_v5_service.py` |
| `services/path_resolver.py` | `PathResolver` | 文件系统 | 路径解析与验证。 | 间接覆盖 |

**注意**：V6 的 Workspace 快照目前分散在 `RuntimeContext.project_path` 和各 Engine 的 metadata 中，尚无统一持久化实体。

---

## 四、Runtime 事实数据 (Runtime Facts)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `v6/runtime/context.py` | `RuntimeContext` | 内存（可 snapshot/restore） | 单次任务运行时唯一状态容器。 | `tests/v6/test_v6_runtime.py`, `tests/v6/test_v6_smoke.py` |
| `v6/runtime/types.py` | `ChatMessage`, `ToolCall`, `ToolResult`, `TokenUsage`, `InferenceMetrics` | 内存 | Runtime 基础共享类型。 | `tests/v6/test_v6_task.py` |
| `v6/runtime/task.py` | `Task`, `ChatTask`, `AnalyzeTask` | 内存 | Runtime 任务模型。 | `tests/v6/test_v6_task.py` |
| `v6/runtime/enums.py` | `RuntimeState` | 内存 | 运行时状态枚举。 | 间接覆盖 |
| `v6/runtime/result.py` | `RuntimeResult` | 内存 | 任务结果。 | 间接覆盖 |
| `v6/runtime/metrics.py` | `RuntimeMetrics` | 内存 | 任务指标。 | `tests/v6/test_v6_runtime_kernel.py` |
| `v6/runtime/trace.py` | `RuntimeTrace` | 内存 | 执行轨迹。 | `tests/v6/test_v6_trace.py` |

---

## 五、能力契约数据 (Capability Contract)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `agent_workbench/runtime/capability/model.py` | `CapabilityDefinition`, `CapabilityMatch`, `CapabilityIntent`, `CapabilityPersona` | 内存 / 注册表 | 能力静态定义、匹配结果、意图。 | `tests/v6/runtime/test_capability_model.py` |
| `agent_workbench/runtime/capability/state.py` | `CapabilityState`, `CapabilityExecutionState` | 注册表 | 能力生命周期状态。 | `tests/v6/runtime/test_capability_state.py` |
| `agent_workbench/runtime/capability/context.py` | `CapabilityContext` | 内存 | 能力执行上下文。 | `tests/v6/runtime/test_capability_context.py` |
| `agent_workbench/runtime/capability/chain.py` | `CapabilityChain` | 内存 | 能力链式调用。 | `tests/v6/runtime/test_capability_chain.py` |
| `v6/runtime/capability_registry.py` | `CapabilityRegistry` | 内存 | V6 Runtime 能力注册表。 | `tests/v6/test_v6_capability_registry.py` |
| `agent_workbench/runtime/capability_registry.py` | `CapabilityRegistry` | 内存 | Agent Workbench 能力注册表。 | `tests/v6/runtime/test_capability_registry.py`, `tests/v6/runtime/test_capability_registry_runtime.py` |

---

## 六、Provider / Tool / Skill 注册数据 (Registry)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `agent_workbench/services/tool_registry.py` | `ToolRegistry`, `Tool` | 内存 + 配置 | Tool 注册、开关、权限。 | `tests/test_tool_gateway.py`（部分） |
| `agent_workbench/services/model_provider.py` | `ModelProvider` (ABC) | 内存 | Provider 抽象接口。 | 间接覆盖 |
| `agent_workbench/services/echo_provider.py` | `EchoProvider` | 内存 | 占位 Provider。 | 间接覆盖 |
| `agent_workbench/services/openai_provider.py` | `OpenAIProvider` | 内存 | OpenAI Provider 实现。 | `tests/integration_test_deepseek_metrics.py` |
| `v6/runtime/engines/*.py` | `*Engine` | 内存 | Engine 实现（llm/tool/memory/knowledge 等）。 | `tests/v6/test_v6_engine_manager.py`, `tests/v6/test_engine_protocol.py` |

**注意**：Skill Registry 目前尚无独立实现，可用 CapabilityRegistry + ToolRegistry 组合表达。

---

## 七、Trace / Metric / Observability 数据

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `v6/runtime/trace.py` | `RuntimeTrace` | 内存 | 执行步骤轨迹。 | `tests/v6/test_v6_trace.py` |
| `v6/runtime/metrics.py` | `RuntimeMetrics` | 内存 | 任务级指标。 | `tests/v6/test_v6_runtime_kernel.py` |
| `v6/runtime/replay.py` | `Replay` | 内存 | 基于 Trace 的回放。 | `tests/v6/test_v6_replay.py` |
| `services/metrics_collector.py` | `MetricsCollector` | 内存 | V5 指标收集器。 | `tests/test_metrics_collector.py` |

---

## 八、交互协议数据 (Interaction)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `agent_workbench/runtime/interaction/request.py` | `RuntimeRequest` | 内存 | 外部输入协议。 | `tests/interaction/test_request.py` |
| `agent_workbench/runtime/interaction/event.py` | `InteractionEvent` | 内存 | UI 事件协议。 | `tests/interaction/test_event.py` |
| `agent_workbench/runtime/interaction/mapper.py` | `InteractionMapper` | 内存 | Request ↔ Runtime 映射。 | `tests/interaction/test_mapper.py` |
| `agent_workbench/runtime/interaction/layer.py` | `InteractionLayer` | 内存 | 交互边界层。 | `tests/interaction/test_layer.py` |
| `agent_workbench/runtime/interaction/renderer.py` | `UIEventRenderer` | 内存 | UI 渲染协议。 | `tests/interaction/test_request_mapping.py` |

---

## 九、决策与策略数据 (Decision)

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `agent_workbench/runtime/decision/schema.py` | `RuntimeDecision` | 内存 | 运行时决策结果。 | `tests/v6/runtime/test_runtime_decision_contract.py` |
| `agent_workbench/runtime/decision/policy.py` | `DecisionPolicy` | 内存 | 决策策略。 | `tests/v6/runtime/test_decision_layer.py` |
| `agent_workbench/runtime/decision/resolver.py` | `CapabilityResolver` | 内存 | 能力解析器。 | `tests/v6/runtime/test_decision_layer.py` |
| `agent_workbench/runtime/decision/interpreter.py` | `DecisionInterpreter` | 内存 | 决策解释器。 | 间接覆盖 |
| `v6/runtime/decision.py` | `Decision` | 内存 | V6 Runtime 决策模型。 | `tests/v6/test_v6_runtime_kernel.py` |
| `v6/runtime/decision_policy.py` | `DecisionPolicy` | 内存 | V6 决策策略。 | 间接覆盖 |

---

## 十、V5 遗留数据层（仅适配使用）

| 文件 | 类型 | 存储 | 说明 | 测试 |
|---|---|---|---|---|
| `v5/service/config_service.py` | `ConfigService` | `config.yaml` | V5 配置服务。 | `tests/test_v5_adapter.py` |
| `v5/service/session_service.py` | `SessionService` | `sessions.db` | V5 会话服务。 | `tests/test_v5_adapter.py` |
| `v5/service/adapter.py` | `V5Adapter` | 同上 | V5 适配器，供 V6 过渡使用。 | `tests/test_v5_adapter.py` |

---

## 数据层 → UI 映射关系（初稿）

| UI 区域 | 依赖的数据层 | 主要服务/模型 |
|---|---|---|
| 左侧会话列表 | Session 数据 | `SessionManager` / `SessionService` |
| 聊天消息区 | Session + Runtime Facts | `ChatService` / `RuntimeContext.messages` |
| 输入区 / 模式选择 | Config 数据 | `ConfigManager` / `ConfigService` |
| 工具栏 / 工具面板 | Tool 注册数据 | `ToolRegistry` |
| 模型选择 / Provider 设置 | Provider 注册数据 | `ModelProvider` 子类 |
| 能力市场 / Skill 面板 | Capability Contract | `CapabilityRegistry`, `CapabilityDefinition` |
| 终端 / 文件浏览器 | Workspace 数据 | `project_path`, `PathResolver` |
| 状态栏 / 运行指示 | Runtime Facts + Trace | `RuntimeContext.status`, `RuntimeTrace` |

---

## 当前风险点

1. **Workspace 数据尚未统一**：项目路径、文件选择、终端状态分散在各处，UI 接入前建议先抽象出 `WorkspaceService`。
2. **Skill Registry 缺失**：第一梯队包含 Skill Registry，但目前只有 CapabilityRegistry + ToolRegistry，需要明确 Skill 的实体定义。
3. **Provider 配置未持久化**：`ModelProvider` 配置目前停留在内存或环境变量，尚未接入 `ConfigManager`。
4. **V5 数据层仍在使用**：`v5/` 目录为适配保留，长期应逐步迁移到 V6 服务。
5. **UI 直接依赖部分数据服务**：需确保 UI 只通过 `InteractionEvent` / `RuntimeRequest` 与 Runtime 通信，不直接操作数据服务。

