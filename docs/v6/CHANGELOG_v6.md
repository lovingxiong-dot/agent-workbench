# V6 变更日志

## v6.5.0-alpha (2026-07-07) — 八大引擎实现与 RuntimeContext 重构
- 新增 `v6/runtime/types.py` 作为 Runtime 类型层最底部模块，统一放置 `ChatMessage`、`ToolCall`、`ToolResult`、`TokenUsage`、`InferenceMetrics`、`CompressionStrategy`、`CompressionResult`。
- 固定依赖方向：`RuntimeContext` 与 `interfaces.py` 均从 `types.py` 导入共享类型，`RuntimeContext` 不再依赖 `interfaces.py`。
- 移除 `ChatMessage.to_langchain()` 等 V4 兼容方法，明确 V6 建立新 Runtime 模型而非迁移 V4。
- 重构 `v6/runtime/engines/interfaces.py`：新增 `ChatMessage`、 共享类型、`Engine` 统一基类，八大引擎统一接口 `async def run(ctx: RuntimeContext) -> RuntimeContext`。
- 重构 `v6/runtime/context.py`：`messages` 改为 `ChatMessage` 列表，新增可演进字段（phase / mode / model / provider / project_path / memory / tool_calls / metrics / metadata）。
- 实现八大引擎：
  - `ContextEngine`：上下文组装、压缩、token 估算。
  - `PromptEngine`：System Prompt 构建、模板渲染、画像注入。
  - `InferenceEngine`：LLM 调用、重试降级、指标上报。
  - `ToolEngine`：工具注册、Phase 白名单、执行编排。
  - `PhaseEngine`：Mode-Phase 阶段定义与流转。
  - `MemoryEngine`：记忆存储、检索、项目记忆上下文块。
  - `MetricsEngine`：指标采集、聚合、告警。
  - `PolicyEngine`：配置查询、模型选择、压缩决策。
- 更新 `v6/runtime/runtime.py`：`_echo_handler` 改用 `role="assistant"` 适配 `ChatMessage`。
- 更新 `docs/v6/SPEC.md`：
  - 8.5 节：RuntimeContext 是 Runtime 的唯一公共协议（Public Runtime Protocol）。
  - 8.6 节：RuntimeContext 作为引擎接口顶层对象。
  - 8.7 节：RuntimeContext 是可演进对象，不是固定 Schema。
  - 8.8 节：全层统一 RuntimeContext 接口铁律。
  - 8.9 节：依赖方向固定原则。
  - 8.10 节：RuntimeContext 是 Runtime State Container，不是 Runtime Manager（三条铁律）。
  - 8.11 节：未来接口 Snapshot → Replay 预留。
- 更新 `docs/v6/PROJECT_BLUEPRINT_v6.md`：阶段 5 状态更新为已完成，架构图补全八大引擎。
- 新增 `tests/v6/test_v6_engines.py`：22 个用例覆盖八大引擎构造、run(ctx) 接口、核心路径、异常降级、上下文同一性、RuntimeContext 状态容器约束、snapshot/restore/freeze/reset、Engine 零耦合。
- Review Agent 复核通过，无阻塞项；全量回归 85 个测试通过。

## v6.4.0-alpha (2026-07-07) — AgentRuntime 骨架与事件总线
- 实现 `v6/runtime/event_bus.py`：独立后台线程 + asyncio 队列的异步事件总线，支持同步/异步订阅者。
- 实现 `v6/runtime/context.py`：`RuntimeContext` 单次任务上下文，含 `messages/tools/metadata/status`，已加 `RLock` 线程安全保护。
- 实现 `v6/runtime/scheduler.py`：任务队列、并发控制（默认 1）、取消、wait_all。
- 实现 `v6/runtime/task.py`：`Task` 基类 + `ChatTask` / `AnalyzeTask`。
- 实现 `v6/runtime/runtime.py`：`AgentRuntime` 生命周期、任务调度、错误转 `error` 事件、handler 注册机制。
- 重写 `v6/ui_controller.py`：移除 `EchoRuntime` 使用，改为创建 `ChatTask` 提交到 `AgentRuntime`，订阅事件并转换为 Qt 信号。
- 新增 `tests/v6/test_v6_event_bus.py`、`test_v6_scheduler.py`、`test_v6_runtime.py`、`test_v6_integration.py`；更新 `test_v6_services.py`。
- Review Agent 复核后修复：`EventBus._running` 加锁保护；`RuntimeContext` 加锁；增强 `test_runtime_cancel_task` 断言。
- 阶段 4 全量回归 64 个测试通过；Review Agent 复核通过。

## v6.3.0-alpha (2026-07-07) — ConfigManager + SessionManager + Services
- 实现 `v6/config_manager.py`：YAML 配置持久化、点分路径 get/set、changed 信号、默认配置（app.version / last_mode / last_model / theme.name 等）。
- 实现 `v6/session_manager.py`：SQLite 会话持久化（`storage/sessions.db`）、CRUD、active 管理、按时间分组（今天/昨天/最近7天/更早）、置顶。
- 实现 `v6/services/config_service.py`、`session_service.py`、`chat_service.py`，对 Manager 进行业务层封装，保持 UI 零业务逻辑。
- 重写 `v6/ui_controller.py`：移除 `DEMO_SESSIONS`，注入 ConfigService / SessionService / ChatService，`startup()` 加载真实配置与会话。
- 新增 `tests/v6/test_v6_config_manager.py`、`test_v6_session_manager.py`、`test_v6_services.py`；更新 `test_v6_ui_contract.py` 以适配真实服务。
- 引入 `v6/_paths.py` 与 `V6_DATA_DIR` 环境变量支持，确保测试数据隔离。
- Review Agent 复核后修复：移除 `LeftPanel.DEMO_SESSIONS`，避免启动前闪现假数据；为 `SessionManager` 增加 `db_path` 属性，消除 `ChatService` 直接访问私有字段 `_db` 的封装破坏。
- 阶段 3 全部 43 个测试通过；Review Agent 复核通过。

## v6.1.0-alpha (2026-07-07) — 纯 UI 层完成与契约测试
- 完成 V6 纯 UI 层全部组件实现（`v6/ui/` 23 个模块 + `v6/main_window.py` + `v6/layout_manager.py` + `v6/ui_controller.py`）。
- 严格遵循 `docs/v6/SPEC.md` 信号契约：UI 组件仅发射信号，不直接调用业务方法。
- 所有占位区域填充真实 Demo 数据：左栏会话/功能/文件、中区聊天场景、右栏文件/终端/浏览器。
- 实现无边框窗口、三栏拖拽分栏、折叠/展开、主题深浅切换、Apple 风格菜单等完整交互。
- 新增 `tests/v6/test_v6_ui_contract.py` 契约测试，12 个用例全部通过（含 stub runtime 测试）；UI 层总计 17 个测试通过。
- 修复 `FramelessWindowHelper`、`InvisibleResizeHandle` 事件过滤器中的 `AttributeError`。
- 修复 Review Agent 阻塞问题：将 `UIController.on_send_msg` 的 AI 回声逻辑下沉到 `v6/runtime/stub_runtime.py:EchoRuntime`；连接 `sign_show_analyze_button` 到 `ChatArea` 的「帮我分析当前项目」按钮；连接 `sign_theme_changed` 到 `MainWindow` 并消除 `LeftPanel` 重复设置主题。
- Review Agent 复核通过，确认 UI 层零业务逻辑、单文件职责单一、信号完整。

## v6.0.0-alpha (2026-07-07) — 项目启动与架构规格
- 建立 V6 独立目录 `v6/`，与 V5 完全隔离。
- 编写 `PROJECT_BLUEPRINT_v6.md`、`SPEC.md`、`ROADMAP.md`。
- 明确分层架构：MainWindow → UIController → Manager → AgentRuntime → Engines。
- 确立专业 Agent 协作流程：UI Agent / Runtime Agent / Review Agent。
- 确立每阶段 Review + Smoke + Git 存档的验收标准。
