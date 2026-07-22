# V6 接口与信号契约

> **架构版本**: v6.14.0-alpha — Presentation Boundary Freeze
> **v6/ui 状态**: Frozen Foundation（22 文件，详见 [v6/UI_FOUNDATION.md](../../v6/UI_FOUNDATION.md)）
> **血统**: v6/ui 是独立 Pure UI Foundation，不是旧 v6-agent 的延续

## 0. 架构边界声明（Phase 2-B.1 新增）

```
Runtime → Interaction Contract → Renderer → v6/ui → Qt
```

- **v6/ui** 是 Pure UI Foundation，不引用任何 `agent_workbench/` 包
- **Renderer** (`presentation/renderers/v6_ui/`) 允许引用 Interaction Contract，禁止引用 Runtime Implementation
- **Application** (`application/`) 使用 `WorkbenchController`，禁止使用 `WorkbenchUIController`

详见 [ARCHITECTURE_BOUNDARY.md](../../ARCHITECTURE_BOUNDARY.md)。

## 1. 分层契约

### 1.1 MainWindow 职责边界
MainWindow **只允许**做以下 5 件事：
1. 创建 `LeftPanel`、`ChatArea`、`RightPanel` 等 Widget。
2. 转发 UI 事件到 `UIController`。
3. 接收 `UIController` 的 UI 更新信号并调用对应 Widget 的公共接口。
4. 管理窗口行为（拖拽、resize、最大化、置顶）。
5. 注册全局快捷键。

**禁止**：直接调用 Runtime、Service、Worker、LLM、文件/网络/命令等任何业务逻辑。

### 1.2 UIController 职责
`UIController` 是 UI 层与业务层的唯一桥梁：
- 接收 `MainWindow` 发来的 UI 信号。
- 调用 `SessionManager`、`ConfigManager`、`AgentRuntime` 的方法。
- 将业务层事件转换为 UI 更新信号发回 `MainWindow`。
- 维护当前会话 ID、模式、模型等 UI 状态。

### 1.3 AgentRuntime 职责
`AgentRuntime` 是业务中枢：
- 接收 `UIController` 发送的任务请求（`ChatTask`、`AnalyzeTask` 等）。
- 通过 `Scheduler` 调度任务。
- 在 `RuntimeContext` 中维护任务上下文。
- 通过 `EventBus` 输出阶段事件、流式输出、工具执行、确认请求等。

## 2. UI 组件信号契约

### 2.1 LeftPanel 信号
```python
session_selected = Signal(str)          # 选中会话 ID
new_session_requested = Signal()        # 新建会话
session_action = Signal(str, str)       # action, sid  ("delete"/"rename"/"pin")
search_text_changed = Signal(str)       # 搜索文本
theme_toggled = Signal(str)             # "dark"/"light"
file_selected = Signal(str)             # 文件路径
tool_toggled = Signal(str, bool)        # 工具名, 启用状态
mcp_toggled = Signal(str, bool)         # MCP 名, 启用状态
skill_clicked = Signal(str)             # 技能名
automation_toggled = Signal(str, bool)  # 自动化名, 启用状态
```

### 2.2 ChatArea 信号
```python
send_msg = Signal(str)                  # 用户发送消息
stop_msg = Signal()                     # 停止生成
mode_changed = Signal(str)              # 模式切换
model_changed = Signal(str)             # 模型切换
export_requested = Signal()             # 导出会话
settings_requested = Signal()           # 打开设置
search_toggled = Signal()               # Ctrl+F 切换搜索条
more_clicked = Signal(QPoint)           # 更多按钮点击位置
toggle_right_panel = Signal()           # 切换右栏
```

### 2.3 RightPanel 信号
```python
open_file = Signal(str)                 # 打开文件
load_url = Signal(str)                  # 加载 URL
terminal_command = Signal(str)          # 终端执行命令
tab_closed = Signal(str)                # 关闭标签
```

### 2.4 HeaderBar 信号
```python
left_expand_toggled = Signal()
expand_toggled = Signal()
search_clicked = Signal()
more_clicked = Signal(QPoint)
double_clicked = Signal()  # 双击最大化/还原
```

### 2.5 InputArea 信号
```python
send_clicked = Signal()
stop_clicked = Signal()
mode_tag_clicked = Signal()
model_tag_clicked = Signal()
skill_btn_clicked = Signal()
```

## 3. UIController 输出信号
```python
# → MainWindow → LeftPanel
sign_update_sessions = Signal(list)      # Session 列表
sign_set_active_session = Signal(str)    # 设置激活会话
sign_theme_changed = Signal(str)         # 主题变化

# → MainWindow → ChatArea
sign_set_title = Signal(str, str)        # 标题, 副标题（项目路径）
sign_chat_user = Signal(str)             # 用户消息文本
sign_chat_ai = Signal(str, str)          # AI 消息文本, phase
sign_stream_chunk = Signal(str)          # 流式片段
sign_stream_end = Signal()               # 流式结束
sign_set_streaming = Signal(bool)        # 设置发送/停止按钮状态
sign_tool_executed = Signal(str, dict, str, int)  # 工具执行结果卡片
sign_confirm_required = Signal(str, str) # 工具名, 命令
sign_show_analyze_button = Signal(bool)  # 是否显示「帮我分析当前项目」按钮

# → MainWindow → RightPanel
sign_open_file = Signal(str)             # 打开文件到编辑器
sign_update_terminal = Signal(str)       # 追加终端日志
sign_switch_tab = Signal(str)            # 切换右栏标签
```

## 4. AgentRuntime 事件契约（通过 EventBus）
```python
@dataclass
class RuntimeEvent:
    type: str            # "user_message" / "ai_start" / "ai_chunk" / "ai_end" /
                         # "phase_start" / "phase_end" / "tool_call" / "tool_result" /
                         # "confirm_request" / "confirm_result" / "error" / "metric"
    payload: dict        # 事件载荷
    task_id: str         # 任务 ID
    timestamp: float     # 时间戳
```

## 5. 模块行数约束
- `base.py`：≤ 400 行
- 单个 UI 组件：≤ 300 行，超过则拆分
- `main_window.py`：≤ 250 行
- `ui_controller.py`：≤ 400 行
- `runtime.py`：≤ 400 行
- Engine 单文件：≤ 350 行

## 6. 测试契约
每个模块必须满足：
- 至少一个 import smoke 测试。
- UI 组件必须有属性/信号存在性测试。
- Runtime/Engine 必须有行为测试。
- 集成测试必须覆盖端到端 happy path。

## 7. 安全契约
- 禁止在 UI 组件中执行 `subprocess`、`open()`、网络请求、SQL 等。
- 所有外部调用必须通过 Runtime → Engine → Service。
- 工具执行必须经用户确认（除白名单安全工具外）。
- 用户输入必须做长度和类型校验。

## 8. 引擎接口契约

### 8.1 八大引擎职责
| 引擎 | 接口 | 核心职责 | 闭环反馈 |
| --- | --- | --- | --- |
| ContextEngine | `IContextEngine` | 消息组装、上下文压缩、token 估算 | `report_compression_quality` 接收质量反馈 |
| PromptEngine | `IPromptEngine` | System Prompt 构建、模板渲染、用户画像注入 | 无（纯构建） |
| InferenceEngine | `IInferenceEngine` | LLM 调用、流式输出、重试降级 | `report_metrics` 上报推理指标 |
| ToolEngine | `IToolEngine` | 工具注册、Phase 白名单、执行编排 | 无（结果通过 `ToolResult` 返回） |
| PhaseEngine | `IPhaseEngine` | Mode-Phase 定义、阶段流转、插件扩展 | 无（状态机） |
| MemoryEngine | `IMemoryEngine` | 短期/长期/画像记忆、检索、上下文块 | 无（数据持久化由 Service 负责） |
| MetricsEngine | `IMetricsEngine` | 指标采集、聚合、阈值告警 | 供 PolicyEngine 决策使用 |
| PolicyEngine | `IPolicyEngine` | 配置查询、模型选择、压缩决策、热加载 | 读取 MetricsEngine 数据调整策略 |

### 8.2 依赖注入关系
```
PolicyEngine ──┬──► ContextEngine（读取压缩阈值）
               ├──► InferenceEngine（读取重试/降级配置）
               ├──► ToolEngine（读取工具超时）
               └──► MemoryEngine（读取记忆策略）

MetricsEngine ──┬──► ContextEngine（上报压缩触发/压缩率）
                ├──► InferenceEngine（上报 token/耗时/成功率）
                └──► PolicyEngine（决策输入）
```

### 8.3 共享数据类型
- `Message`：标准消息（role / content / tool_calls / tool_call_id），提供 `to_langchain()` 转换。
- `TokenUsage` / `InferenceMetrics`：推理指标，用于闭环上报。
- `ToolCall` / `ToolResult`：工具调用请求与结果。
- `CompressionStrategy` / `CompressionResult`：上下文压缩策略与结果。

### 8.4 闭环原则
1. ContextEngine 压缩后，下游评估质量并调用 `report_compression_quality`，低质量触发 PolicyEngine 调整策略权重。
2. InferenceEngine 每次调用结束后调用 `report_metrics`，MetricsEngine 聚合后供 PolicyEngine 做模型选择。
3. PolicyEngine 不直接修改 MetricsEngine，只读取聚合结果进行决策。
4. 所有引擎实现必须可 Mock：构造函数注入依赖，禁止全局单例。

### 8.5 RuntimeContext 是 Runtime 的唯一公共协议（Public Runtime Protocol）
**最高层级原则：RuntimeContext 是 Runtime 层对外暴露的唯一公共协议。任何 Engine、Service、Controller、Gateway 的公共接口，只允许传递 RuntimeContext。**

**ChatMessage、ToolCall、MemoryEntry、Metrics 等对象均属于 RuntimeContext 的资源（Resources），不得作为 Runtime 的公共接口。**

核心约定：
```
RuntimeContext = Public Runtime Protocol
    │
    ├── messages: List[ChatMessage]      ← Resource
    ├── tool_calls: List[ToolCall]       ← Resource
    ├── memory: MemoryState              ← Resource
    ├── metrics: MetricsState            ← Resource
    ├── metadata: Dict[str, Any]         ← Resource
    └── ...（未来可扩展）
```

公共接口规范：
- Engine：`async def run(ctx: RuntimeContext) -> RuntimeContext`
- Service：`def run(ctx: RuntimeContext) -> RuntimeContext`
- Controller：`def dispatch(ctx: RuntimeContext) -> RuntimeContext`
- Gateway：`def forward(ctx: RuntimeContext) -> RuntimeContext`

禁止：
- `engine.run(messages)`、`engine.run(tool_call)`、`engine.run(memory)`
- `service.save(session_id, messages)`
- `controller.handle(text)`、`controller.on_send(role, content)`
- `gateway.route(message)`

收益：
- 新增状态或资源时，只需扩展 `RuntimeContext`，不需要修改任何 Engine / Service / Controller / Gateway 接口。
- `RuntimeContext` 成为架构演进的稳定锚点，公共接口长期保持不变。

### 8.6 RuntimeContext 作为引擎接口顶层对象
**原则：Engine 的公共接口统一接收 `RuntimeContext`，`ChatMessage`（或 `Message`）只是 `RuntimeContext` 的组成部分，不得成为 Engine 间通信的顶层对象。**

**RuntimeContext 是运行时唯一状态对象（Single Source of Truth）。Engine 不拥有状态，RuntimeContext 才拥有状态。**

数据流：
```
AgentRuntime
    │
    ▼
RuntimeContext（任务级状态容器）
    │
    ├── session_id / conversation_id / task_id / group_user_id
    ├── phase / mode / model / provider
    ├── project_path
    ├── memory
    ├── messages          # ChatMessage 列表
    ├── tool_calls
    ├── metrics
    └── metadata
    │
    ▼
Engines（统一接收 RuntimeContext，读取输入、写回输出）
```

要求：
1. 八大引擎统一接口：`async def run(self, ctx: RuntimeContext) -> RuntimeContext`。
2. 禁止 `run(messages)`、`run(session)`、`run(dict)`、`run(memory)`、`run(project_path)` 等碎片化接口。
3. 引擎之间不直接传递 `ChatMessage` 列表；所有中间状态通过 `ctx.metadata` 或 `ctx.messages` 共享。
4. `RuntimeContext` 是线程安全的（已加 `RLock`），引擎可安全读写。
5. 单元测试通过构造 `RuntimeContext` 并调用 `engine.run(ctx)`，验证 `ctx` 状态变化。

### 8.7 RuntimeContext 是可演进对象，不是固定 Schema
**原则：Engine 不允许假设 `RuntimeContext` 是固定字段集合，只访问自身职责需要的字段。**

示例演进：
```
V6.0  ctx
      ├── session_id
      └── messages

V6.5+ ctx
      ├── group_id
      ├── group_user_id
      ├── agent_id
      ├── scheduler_state
      ├── gateway_route
      ├── shared_memory
      ├── private_memory
      └── ...
```

收益：
- 新增字段（GroupUser、Gateway、AgentBus、多 Agent 协同）无需修改 Engine 接口。
- `async def run(ctx: RuntimeContext)` 保持稳定，架构可长期演进。
- Engine 只依赖自己读取/写入的字段，天然解耦。

### 8.8 全层统一 RuntimeContext 接口铁律
**原则：Engine、Service、Controller、Gateway 的公共接口统一使用 `RuntimeContext`。任何公共接口不得以 `Message`、`dict`、`Session`、`ToolCall` 等对象作为顶层参数，它们只能作为 `RuntimeContext` 的组成部分。**

数据流：
```
UI
    │
    ▼
Runtime
    │
    ▼
RuntimeContext
    │
  ┌──┴──────────────────────────┐
  │ InferenceEngine              │
  │ PromptEngine                 │
  │ ContextEngine                │
  │ MemoryEngine                 │
  │ PolicyEngine                 │
  │ ToolEngine                   │
  │ MetricsEngine                │
  │ PhaseEngine                  │
  └──────────────┬──────────────┘
                 │
                 ▼
          RuntimeContext（更新）
                 │
                 ▼
           Gateway / UI
```

禁止示例：
- `service.save_messages(session_id, messages)` — 应改为 `service.save(ctx)`
- `controller.on_send(text)` — 应改为 `controller.handle(ctx)` 或在内部构造 `ctx`
- `gateway.route(message)` — 应改为 `gateway.route(ctx)`
- `engine.run(messages)` / `engine.run(session)` / `engine.run(dict)` — 已禁止

允许示例：
- `engine.run(ctx: RuntimeContext) -> RuntimeContext`
- `service.run(ctx: RuntimeContext) -> RuntimeContext`
- `controller.dispatch(ctx: RuntimeContext) -> RuntimeContext`
- `gateway.forward(ctx: RuntimeContext) -> RuntimeContext`

收益：
- `RuntimeContext` 成为 V6 唯一数据载体，跨层传递零碎片化对象。
- 支持多 LLM、多 Agent、Group 用户、Gateway 路由、会话记忆、协同与争论等高级能力时，只需扩展 `RuntimeContext`，不动公共接口。
- 各层只读写自己职责字段，天然解耦。
### 8.9 依赖方向固定原则
**原则：依赖方向永远是 `RuntimeContext` 包含 `ChatMessage`、`MemoryState`、`MetricsState`、`ToolCall`、`SessionInfo` 等，而不是这些对象反过来决定 `RuntimeContext` 的形态。**

正确依赖图：
```
v6/runtime/types.py
    │
    ├── ChatMessage
    ├── ToolCall / ToolResult
    ├── TokenUsage / InferenceMetrics
    └── CompressionStrategy / CompressionResult
    │
v6/runtime/context.py ── imports from types.py
    │
    RuntimeContext
        ├── messages: List[ChatMessage]
        ├── tool_calls: List[ToolCall]
        ├── metrics: Dict[str, Any]
        └── metadata: Dict[str, Any]
    │
v6/runtime/engines/interfaces.py ── imports from types.py
    │
    Engine.run(ctx: RuntimeContext)
```

禁止：
- `context.py` 从 `interfaces.py` 导入 `ChatMessage`。
- `ChatMessage` 携带 `to_langchain()` 等 V4 兼容方法，反向污染 V6 类型层。
- Engine 接口围绕 `ChatMessage` 设计（如 `run(messages)`）。

要求：
- `v6/runtime/types.py` 是类型层最底部模块，不依赖 Engine、RuntimeContext 或业务代码。
- `RuntimeContext` 从 `types.py` 导入所需类型；`interfaces.py` 也从 `types.py` 导入。
- V6 的设计目标不是迁移 V4，而是建立新的 Runtime 模型；兼容 V4 只能作为迁移策略，不能成为 V6 架构约束。

### 8.10 RuntimeContext 是 Runtime State Container，不是 Runtime Manager
**原则：RuntimeContext 保存 Runtime Facts，不拥有 Runtime Behavior / 业务能力。**

#### 铁律一：Context 不拥有业务能力（Ownership）
- `RuntimeContext` 负责保存 Runtime Facts。
- `Engine` / `Service` 负责产生 Runtime Facts。
- `RuntimeContext` 不拥有任何业务能力。

禁止在 `RuntimeContext` 上定义：
- `ctx.call_llm()`
- `ctx.execute_tool()`
- `ctx.save_memory()`
- `ctx.invoke_agent()`
- `ctx.dispatch()`
- 任何涉及外部调用、策略决策、持久化、编排的方法。

#### 铁律二：Context 允许拥有数据管理能力（Data Management）
允许在 `RuntimeContext` 上定义：
- `ctx.add_message()`
- `ctx.clone()`
- `ctx.snapshot()` / `ctx.freeze()`
- `ctx.restore(snapshot)`
- `ctx.reset()`
- `ctx.to_dict()`

未来可扩展：
- `ctx.diff(old_ctx)`
- `ctx.merge(other_ctx)`

这些全部是数据管理，不是业务。

#### 铁律三：Engine 永远修改 Context，而不是彼此调用
正确模式：
```
Runtime
    │
    ▼
Phase
    │
    ▼
Engine A ──► ctx
    │
    ▼
Engine B ──► ctx
    │
    ▼
Engine C ──► ctx
```

错误模式：
```
InferenceEngine ──► ToolEngine.run() ──► MemoryEngine.run()
```

要求：
- Engine 之间零耦合。
- 每个 Engine 只读取/修改 `RuntimeContext` 中自己负责的字段。
- Runtime 负责编排 Engine 执行顺序。

原因：
- 防止 Context 越长越胖，最终变成上帝对象。
- 保证 Engine / Service 是纯业务逻辑单元，便于独立测试和替换。
- 让 `RuntimeContext` 保持稳定的形态：它是被操作的数据，不是操作者。

### 8.11 未来接口：Snapshot → Replay（预留）
**原则：`RuntimeContext.snapshot()` / `restore()` 为未来的 Checkpoint / Replay 能力奠定基础。**

未来执行模型：
```
Phase
    │
    ▼
Snapshot
    │
    ▼
ToolEngine
    │
    ▼
Snapshot
    │
    ▼
InferenceEngine
    │
    ▼
Snapshot
```

价值：
- **Checkpoint**：每个 Phase 或关键操作后可保存快照。
- **Rollback**：Review / Approval 失败时恢复到上一快照。
- **Replay**：像录像一样重放完整 Agent 执行过程。
- **Debugger**：基于快照序列定位问题、查看中间状态。

实现策略：
- 当前阶段只需保证 `snapshot()` / `restore()` / `freeze()` 数据正确、深拷贝完整。
- Replay 编排器在后续阶段基于快照序列实现，不修改 `RuntimeContext` 公共接口。

### 8.12 Runtime Interface Principle（运行时接口原则）
**原则：所有 Runtime 内部模块统一接受 `RuntimeContext` 作为唯一输入协议（Input Protocol），各模块保留符合自身职责的语义化方法名，不强制统一为 `execute()`。**

正确示例：
- `ChatService.generate(ctx)`
- `MemoryService.store(ctx)`
- `ConfigService.apply(ctx)`
- `ToolService.invoke(ctx)`
- `SessionService.load(ctx)`
- `PromptEngine.run(ctx)`
- `InferenceEngine.run(ctx)`
- `IRuntimeAdapter.submit(ctx)`

错误示例：
- `ChatService.execute(ctx)` — 语义模糊，无法一眼判断职责。
- `MemoryService.execute(ctx)` — 同上。
- `ToolService.execute(ctx)` — 同上。

原因：
- 统一的是输入协议 `RuntimeContext`，不是方法名。
- 语义化方法名是模块职责的自我表达。
- 便于代码阅读、调试、日志追踪和接口审计。

适用范围：
- Engine、Service、Adapter、Gateway 的公共方法。
- Controller 可保留 `on_send_msg(text)` 等 UI 事件处理名，但内部必须尽快转换为 `RuntimeContext` 并调用 `adapter.submit(ctx)`。

### 8.13 Adapter 属于 Application Layer，不侵入 Runtime
**原则：Adapter 不属于 Runtime，属于 Application Layer。**

架构边界：
```
Application Layer
    │
    ├── UIAdapter
    ├── GatewayAdapter
    ├── CLIAdapter
    ├── MCPAdapter
    └── RuntimeAdapter
            │
            ▼
        Runtime Core
            │
            ▼
        Runtime.run(ctx)
```

Runtime 永远不知道：
- 谁在调用它。
- 是 GUI、Gateway、REST 还是 CLI。

Runtime 只知道：`Runtime.run(ctx)`。

这样 Runtime 成为可嵌入的 Runtime Core。

#### 关键边界：RuntimeAdapter 是 Application Boundary
**RuntimeAdapter 是 Application Boundary，不属于 Runtime Core。**

依赖方向强制为单向：
```
Adapter ──depends──► Runtime Core
Runtime Core ──does not depend──► Adapter
```

禁止：
- Runtime Core 导入任何 Adapter 实现或协议。
- Runtime Core 中引用 `IRuntimeAdapter`、`LocalRuntimeAdapter` 等 Application Layer 类型。
- Engine / Scheduler / EventBus 依赖 Adapter。

允许：
- Adapter 依赖 Runtime Core 的 `AgentRuntime`、`RuntimeContext`、`EventBus` 等。

原因：
- 保证 Runtime Core 可独立运行、独立测试、独立打包。
- 防止 Application Layer 的变动反向污染 Runtime Core。
- 为未来多入口（UI / Gateway / CLI / MCP）共享同一 Runtime Core 奠定基础。

#### Adapter 两条铁律
**铁律一：Adapter 不保存状态**
- 所有状态必须保存在 `RuntimeContext` 中。
- Adapter 自身不允许持有业务状态、会话状态或运行时状态。

**铁律二：Adapter 不做业务**
- Adapter 只负责格式转换与转发：
  ```
  Input → Context → Runtime → Output
  ```
- 不允许在 Adapter 中实现 LLM 调用、工具执行、记忆存储、策略决策等业务逻辑。

### 8.14 RuntimeContext.new() 的语义：创建 Runtime Task，而非创建数据对象
**原则：`RuntimeContext.new()` 不应被理解为“创建一个空的数据对象”，而应被理解为“创建一个 Runtime Task”。**

正确语义：
```
ctx = RuntimeContext.new(
    session_id=...,
    messages=...,
)

等价于：
  创建一个 Runtime Task
        ↓
  生成 task_id（任务唯一标识）
        ↓
  初始化 Runtime Facts
        ↓
  得到携带这些事实的 RuntimeContext
```

核心澄清：
- `task_id` **不是** `RuntimeContext` 创建出来的。
- `task_id` **是** `Runtime Task` 创建出来的。
- `RuntimeContext` 只是携带 `task_id`，作为该任务生命周期内的事实容器。

当前实现：
- `RuntimeContext.new()` 内部自动生成 `task_id`（UUIDv4）。
- 业务代码优先使用 `RuntimeContext.new()`，避免手动填写无意义的 `task_id="test"` 或 `task_id="service"`。
- 这保持了 `task_id` 的必填语义，同时减轻了调用方负担。

未来演进方向：
```
Runtime.start_task(...)          → RuntimeContext
TaskFactory.create(...)          → RuntimeContext
```

届时：
- `RuntimeContext(...)` 永远只是一个纯数据对象（Facts Container）。
- `Runtime` / `TaskFactory` 负责创建任务生命周期、生成 `task_id`、初始化 Trace。
- 职责边界会更加清晰：创建 Context ≠ 创建 Task。

说明：
- 当前阶段使用 `RuntimeContext.new()` 作为统一入口是合理且务实的过渡方案。
- 它既保持了 `task_id` 的必填语义和 Runtime 可追踪性（Traceability / Lifecycle），又不要求每个调用方都手动生成任务 ID。
- 当 Runtime 的任务生命周期管理足够成熟时，再逐步将 Task 创建语义从 Context 中分离出来。

### 8.15 Runtime Trace：记录 Task 执行历史，支持 Replay
**原则：每个 Runtime Task 必须留下可审计、可回放、可调试的执行历史。**

Runtime Trace 记录的不是业务结果，而是执行过程：
```
Task
  ↓
Phase
  ↓
Engine / Service / Tool
  ↓
Finish
```

`RuntimeContext` 携带 `trace: RuntimeTrace`，与 Task 同生命周期：
- `trace` 属于 History（历史），不是当前状态。
- `trace` 只追加、不修改已有步骤。
- `Runtime`、`Adapter`、`Engine`、`Service`、`Tool` 均可向 `ctx.trace.add(...)` 写入自己负责的步骤。
- 每个 `TraceStep` 包含：`timestamp`、`phase`、`node`、`action`、`payload`。

推荐记录约定：
| node | 说明 |
|---|---|
| `runtime` | Runtime 层生命周期：`task_start` / `handler_dispatch` / `task_finish` / `task_error` |
| `adapter` | Application Boundary：`submit` / `cancel` |
| `engine` | 八大引擎：`inference_start` / `prompt_build` / `emit_chunk` / `emit_end` |
| `service` | 业务服务：`store` / `load` / `apply` |
| `tool` | 工具执行：`invoke` / `result` |

Replay：
- `ReplayPlayer(trace, event_bus)` 可按 `trace` 中记录的 `emit_*` 步骤重放事件。
- Replay 用于调试、可视化、审计、回归测试。
- Replay 不重新执行业务逻辑，只重放历史事件。

注意：
- `RuntimeTrace` 只记录摘要（small facts），不应存储大对象、原始响应全文或敏感数据。
- `trace` 与 `metrics`、`result`、`messages` 一样，是 `RuntimeContext` 的组成部分，不得作为 Runtime 的顶层公共接口。

### 8.16 长期演进：RuntimeTask 五对象模型
**展望：Runtime 的核心对象最终可收敛为五个。**

```
RuntimeTask
    │
    ├── RuntimeContext   — 当前事实（Facts）
    │
    ├── RuntimeTrace     — 执行历史（History）
    │
    ├── RuntimeMetrics   — 性能统计（Performance）
    │
    ├── RuntimeResult    — 最终输出（Output）
    │
    └── RuntimeState     — 生命周期（Lifecycle）
```

职责边界：
- `RuntimeContext`：保存当前运行状态，供 Engine 读取和修改。
- `RuntimeTrace`：记录整个执行过程，供调试、回放、可视化、审计。
- `RuntimeMetrics`：统计耗时、Token、工具调用次数等量化指标。
- `RuntimeResult`：最终对外输出，供 UI、Gateway、API 返回。
- `RuntimeState`：管理任务生命周期（Created / Queued / Running / Completed / Failed 等）。

当前阶段：
- `RuntimeContext` 已携带 `trace`、`metrics`、`result` 字段，向五对象模型兼容。
- `status` 字段已统一使用 `RuntimeState` 枚举，避免字符串漂移。
- `RuntimeContext.new()` 作为 Task 创建入口，后续可演进为 `RuntimeTask.create()` 或 `Runtime.start_task(...)`。
- 当前不强制拆分 `RuntimeTask` 类，避免过度设计；当多 Agent 协作、Gateway、可视化调试需求明确时，再正式提取 `RuntimeTask`。

### 8.17 RuntimeMetrics：统一统计接口
**原则：RuntimeMetrics 保存 Statistics，不属于 Facts，也不属于 Output。**

覆盖字段（预定义）：
| 字段 | 含义 |
|---|---|
| `tokens` | LLM Token 消耗 |
| `latency_ms` | 推理 / 执行耗时 |
| `tool_time_ms` | 工具执行耗时 |
| `memory_hits` | 记忆命中次数 |
| `cache_hits` | 缓存命中次数 |
| `cost` | 估算成本 |
| `retry` | 重试次数 |
| `queue_time_ms` | 队列等待耗时 |
| `custom` | 扩展指标容器 |

使用方式：
- Engine 通过 `ctx.metrics.record(tokens=..., latency_ms=...)` 覆盖写入。
- Engine 通过 `ctx.metrics.accumulate(tokens=..., retry=1)` 累加数值。
- `ctx.metrics.snapshot()` 返回深拷贝，供上报 / Checkpoint / Replay 使用。

当前挂载：
- `RuntimeContext.metrics: RuntimeMetrics`。
- 未来迁移到 `RuntimeTask.metrics` 时，只需移动字段，接口保持不变。

### 8.18 RuntimeResult：统一输出协议
**原则：RuntimeResult 保存 Output，不属于 Facts。**

覆盖字段：
| 字段 | 含义 |
|---|---|
| `answer` | 文本回答 |
| `tool_result` | 工具返回结果 |
| `files` | 文件产物路径列表 |
| `images` | 图片产物路径列表 |
| `artifacts` | 结构化产物列表 |
| `error` | 错误信息 |
| `status` | 最终状态 |
| `extra` | 扩展输出容器 |

使用方式：
- Engine 通过 `ctx.result.set_answer(...)`、`add_file(...)`、`set_error(...)` 写入。
- Gateway / UI 最终统一读取 `RuntimeResult` 作为任务输出。
- `ctx.result.snapshot()` 返回深拷贝，供序列化 / 返回使用。

当前挂载：
- `RuntimeContext.result: RuntimeResult`。
- 未来迁移到 `RuntimeTask.result` 时，只需移动字段，接口保持不变。

### 8.19 RuntimeState：生命周期枚举
**原则：任务生命周期状态必须使用 `RuntimeState` 枚举管理，禁止字符串硬编码。**

枚举值：
```
CREATED    → 已创建
QUEUED     → 已入队
RUNNING    → 执行中
WAITING    → 等待中
PAUSED     → 已暂停
CANCELLED  → 已取消
COMPLETED  → 已完成
FAILED     → 已失败
```

使用方式：
- `RuntimeContext.status: RuntimeState`。
- `AgentRuntime` 通过 `ctx.set_status(RuntimeState.RUNNING)` 直接设置枚举。
- 序列化时存储字符串（`.value`），恢复时重新转换为枚举。

收益：
- 消除 `"running"` / `"Running"` / `"RUNNING"` 等字符串漂移。
- `RuntimeScheduler` 可统一读取 `RuntimeState` 做生命周期管理。
- 为后续 `task.state` 预留语义，迁移成本低。

