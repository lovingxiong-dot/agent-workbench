# Changelog

## v4.0.8-alpha (2026-07-01) — v4全量UI三位一体对齐SVG设计稿

### feat
- **HeaderToolbar 按钮尺寸/样式对齐 SVG**：按钮 28×24→18×22，图标 18px→14px，SVG stroke-width 2→1.5，标题字号 15/12px→12/10px，边框加 0.5px solid + border-radius 3px。
- **InputArea 标签式 mode/model 替代 QComboBox**：`TagSelectButton` 实现"标签名 + 值 + ▼"弹出菜单，模式/模型选择从下拉框改为贴纸标签样式；`SkillSendButton` 36×36→24×24（r=12），技能按钮 32×32→20×20（r=10）。
- **RightPanel 标签栏交互增强**：`setTabsClosable(True)` + `tabCloseRequested` 支持关闭非核心标签；新增搜索角标按钮（🔍）；标签栏样式改为圆角 + 紧凑边距；新增 `RecentFilesList` 组件（路径+时间列表）。
- **聊天区 Phase 面板与折叠块样式对齐**：去掉 `max-width:85%` 限制 + 4px 左边色条卡片化；fold-block 加 0.5px solid border；Phase 面板 header 加底部 border-bottom；清理旧 CSS。
- **左栏 Tag 等宽**：功能/会话标签页使用 `addWidget(btn, 1)` 均分宽度。
- **死代码清理**：删除 `v4/right_panel.py` 中未使用的 `FunctionPageWidget`（与 conversation_list 中的同名类无关）。

### refactor
- `v4/input_area.py` 重写：QComboBox → TagSelectButton，SkillSendButton 尺寸对齐 SVG，InputTextEdit 封装 Enter/Shift+Enter 逻辑。

### test
- 修复 `tests/test_v4_input_area.py` 适配新 TagSelectButton API（`mode_selector` → `mode_tag`、`model_selector` → `model_tag`）。
- 全量 29 项测试通过，零回归。

## v4.0.5-alpha (2026-06-30) — 工程目录标准化 + PyInstaller 路径适配

### refactor
- **工程目录标准化改造**：根目录文件按职责分组，结束配置/文档/脚本/图标一股脑堆在根目录的状态。
  - `config/`：存放 `config.yaml`、`.env`、`.env.example`。
  - `assets/`：存放 `app.ico` 应用图标。
  - `scripts/`：存放 `rebuild.ps1`、`runtime_hook.py`、`start.bat`。
  - `docs/`：存放 `README.md`、`ARCHITECTURE.md`、`CHANGELOG.md`、`PROJECT_BLUEPRINT.md`、`getting-started.md`。
  - 源码分组（src/）在 `PROJECT_BLUEPRINT.md` 目录树中统一标注：`agent_engine/`、`core/`、`v4/`、`services/`、`tools/`、`workers/`、`ui/`、`resources/`。

### build
- **PyInstaller 路径同步**：`AgentWorkbench.spec` 更新 `datas`（`config/config.yaml`）、`runtime_hooks`（`scripts/runtime_hook.py`）、`icon`（`assets/app.ico`）。
- **打包脚本路径修正**：`scripts/rebuild.ps1` 因自身移动到 `scripts/`，改用 `$projectRoot = Split-Path -Parent $PSScriptRoot` 计算工程根目录，并同步更新 `dist/`、`build/`、`assets/app.ico` 路径。

### fix
- **配置路径解析**：`services/config_service.py` 与 `agent_engine/llm_registry.py` 新增 `_get_app_root()` / `_get_readonly_root()`，打包时读 `_MEIPASS` 内只读副本，写 `exe 同级目录`；相对路径自动解析为绝对路径；`save()` 自动创建 `config/` 子目录。
- **调用点路径同步**：`v4/worker.py`、`v4/main_window.py`、`tests/test_v4_gui_smoke.py`、`tests/integration_test_deepseek_metrics.py`、`scripts/test_llm_direct.py`、`scripts/test_llm_orchestrator_like.py`、`scripts/smoke_craft_flow.py`、`v4/后续接入指南.md` 统一改为 `config/config.yaml` / `docs/README.md`。
- **持久化路径适配**：`v4/repository.py`、`services/activity_service.py`、`services/session_service.py` 默认数据文件定位到 `exe 同级 storage/`，避免打包后找不到数据库路径。

### docs
- **三份核心文档交叉同步**：`docs/README.md` 文件地图、当前状态、启动/打包命令更新为新目录；`docs/PROJECT_BLUEPRINT.md` 目录树重构为 config/assets/scripts/docs/src/tests/storage 分组；`docs/ARCHITECTURE.md`、`docs/getting-started.md`、`blueprints/integration/workspace-context.md` 中的配置与文档链接同步修正。

### test
- 全量 193 项测试通过，零回归。

## v4.0.4-alpha (2026-06-30) — v4 对话 UI 三层折叠结构

### feat
- **对话 UI 三层折叠结构**：`v4/main_window.py` 重写 `SimpleChatArea`，支持阶段面板、工具执行、思考过程、内部命令输出的分级折叠。
  - 阶段面板（第 1 层）始终展开：analyze / execute / verify / archive 对应不同左侧色条与标题。
  - 工具执行摘要（第 2 层）默认收起：`v4/worker.py` 测量工具耗时与成功状态，`WorkerToolEvent` 上报后由 `UIRenderer._build_tool_fold` 生成可折叠块。
  - 思考过程（第 3 层）默认收起：`UIRenderer._build_thinking_fold` 从 AI 回复中提取任务列表并显示完成进度。
  - 内部命令输出（第 3 层）默认收起：工具结果超过 200 字符时折叠，显示行数。
  - 折叠交互：聊天区改用 `QTextBrowser`，拦截 `anchorClicked` 信号，点击折叠头切换展开/收起状态。
- **左栏会话列表精简化**：`v4/conversation_list.py` 每项显示标题（20 字）+ 最后消息预览（40 字）+ 时间；注入 `SessionRepository` 获取最后一条消息内容。

### refactor
- **工具事件路由**：`v4/orchestrator.py` 订阅 `worker.tool` 并转发为 `ui.append_tool`，`v4/ui_renderer.py` 改由 `ui.append_tool` 渲染工具折叠块。

### test
- 新增 `scripts/verify_ui_fold.py`：无 LLM 依赖的 UI 折叠验证脚本，验证 craft 流程下的阶段面板、思考折叠、工具折叠及点击交互。
- 全量 193 项测试通过，零回归。

## v4.0.3-alpha (2026-06-30) — Phase 工作流接入 v4 + PyInstaller 打包适配 + 清理零引用旧代码

### feat
- **V4Worker 内建 PhaseEngine**：craft 模式完整 analyze→confirm→execute→verify→archive 流程。
  - `v4/worker.py` 重构 `_run` 方法，新增 `_run_phased` 驱动 Phase 循环。
  - analyze 阶段解绑工具，强制 LLM 输出文本任务清单。
  - execute 阶段绑定工具执行 ReAct 循环。
  - verify 阶段解绑工具，强制 LLM 输出验证总结。
- **`v4/orchestrator.py` Phase 事件路由**：订阅 `PhaseChangedEvent` / `PhaseConfirmRequiredEvent` / `PhaseCompleteEvent`，处理确认门控与任务终态同步。
- **`v4/event_bus.py` 新增 `unsubscribe`**：支持测试时解绑默认 WorkerManager。

### refactor
- **PyInstaller 打包适配 v4**：更新 `AgentWorkbench.spec` 的 hiddenimports，加入 v4 模块与 agent_engine 引擎；清理已删除的 v2/v3 模块引用。
- **清理零引用 v2/v3 旧代码**：扫描并删除 27 个文件（`ui/main_window.py`、`services/app_context.py`、`agent_engine/classifier.py` 等），移除双轨维护成本。

### fix
- **用户停止任务后状态正确收敛**：`_on_user_stop` 更新任务状态为 `CANCELLED`，并发射 `WorkerDestroyEvent` 终止 Worker，避免 phase 事件覆盖取消状态。
- **测试 StubWorkerManager 注入**：`tests/test_v4_integration.py` 在创建窗口前解绑默认 WorkerManager，避免真实 V4Worker 干扰集成测试。

### test
- 新增 `smoke_craft_deepseek.py`：craft 模式端到端冒烟测试，验证 analyze→confirm→execute→verify→archive 完整流程。
- 全量 193 项测试通过，零回归。

## v4.0.2-alpha (2026-06-30) — v4原生Worker八引擎推理

### feat
- **新建 `v4/worker.py` — V4Worker**：以八引擎（PromptEngine/ContextEngine/ToolEngine/PolicyEngine/MetricsEngine）原生驱动 ReAct 推理循环。
  - 零绞杀者依赖：不禁旧 AgentWorker / AgentOrchestrator / AgentSession。
  - 直接通过 `LLMRegistry.get_llm()` + `bind_tools()` 调用 LLM，自行检测 `tool_calls` 并执行工具循环。
  - 通过 `ToolEngine.call()` 执行工具，支持 Phase 白名单校验。
  - QThread + asyncio 事件循环架构，`submit(user_text)` 外部注入任务。
  - 信号兼容旧 AgentWorker：`chunk_ready` / `result_ready` / `error_occurred`。

### refactor
- **`v4/worker_manager.py`**：`_create_worker` 改用 `V4Worker` 替代 `EngineWorker`；移除 `engines`/`llm_registry` 构造参数（Worker 自行初始化引擎）；`worker.submit(user_text)` 启动任务。
- **`v4/orchestrator.py`**：`_on_queue_task_ready` 从队列获取 `QueuedTask.user_text` 并传入 `WorkerCreateEvent`。
- **`v4/events.py`**：`WorkerCreateEvent` 新增 `user_text: str = ""`。
- **`v4/main_window.py`**：修 `config.load()`→`config.config`；移除 WorkerManager 多余参数。

### test
- 全量 193 项测试通过，零回归。

## v4.0.1-alpha (2026-06-30) — v4 Solo极简UI重构与主题切换

### feat
- **Solo极简两栏UI重构**：重写 `v4/main_window.py` 与 `v4/conversation_list.py`，固定两栏布局（左 280px + 右填充）；移除 IDE 元素（三栏布局/状态栏/容量标签/Phase-工具按钮/资源管理器/终端/文档编辑器）。
  - 左栏：Agent 标题 + 模型下拉 + 主题切换按钮（🌙/☀️）+ 「+ 新任务」按钮 + 极简会话列表（标题 + 预览 + 时间）。
  - 右栏：SimpleChatArea 含会话标题/环境、消息流（用户/AI气泡 + 系统卡片）、多行输入框（Enter发送/Shift+Enter换行）。
- **主题切换系统**：定义 dark/light 两套 `THEMES` 配色字典；左栏顶部 🌙/☀️ 按钮即时切换主题，同步更新左栏/聊天区/输入区所有控件样式；主题状态持久化到 `config.yaml` 的 `app.theme`。
- **延迟创建会话**：点击「+ 新任务」仅重置为草稿窗口（不写 DB），用户发送首条消息后由 `SessionOrchestrator._on_user_send` 创建会话并刷新列表，消除空会话条目。

### test
- 新增 `tests/test_v4_gui_smoke.py::test_theme_toggle_button_switches_and_persists`：验证按钮 emoji 初始值、点击切换后按钮与配置变更、左右栏样式差异化。
- 适配 `tests/test_v4_integration.py` 所有用例：`chat_view` → `chat_area`、`_btn_chat` / `_btn_work` → `new_task_btn`，移除会话图标断言。
- 全量 193 项测试通过。

## v4.0.0-alpha (2026-06-30) — v4 单轨架构：MessageBus + SessionRuntime + 薄 MainWindow

### feat
- **v4 单轨事件总线架构**：新增 `v4/` 目录，实现基于 PySide6 Signal 的强类型 MessageBus，统一跨组件通信。
  - `v4/models.py`：不可变数据模型 `SessionMetadata` / `Message` / `Environment` / `TaskState`。
  - `v4/event_bus.py`：`MessageBus` 支持 namespace / name / session_id 订阅与全量分发。
  - `v4/events.py`：44+ 个事件类，覆盖 user / session / queue / phase / worker / ui 六大命名空间。
  - `v4/repository.py`：基于 SQLite 的会话仓库，消息唯一权威来源；支持置顶排序、环境持久化、任务状态快照。
  - `v4/queue.py`：会话级双槽位 `QueueManager`，控制消息并发，支持取消、自动出队、状态广播。
  - `v4/runtime.py`：`SessionRuntime` 聚合根，内聚本会话队列、Worker 引用、Phase 状态、环境上下文。
  - `v4/worker_manager.py`：系统级 Worker 管理，最多 5 个并发 Worker，超出排队；Worker 绑定会话与项目环境。
  - `v4/orchestrator.py`：`SessionOrchestrator` 统一协调会话生命周期、消息持久化、事件路由。
  - `v4/ui_renderer.py`：唯一 UI 更新者，订阅 `ui.*` 事件驱动 `ChatView`、状态栏、会话列表。
  - `v4/conversation_list.py`：数据驱动会话列表，支持 Chat/Work 类型、置顶、重名、状态徽章。
  - `v4/main_window.py`：薄编排层，只负责 UI 构建与信号路由，所有业务状态委托给 v4 核心。
- **main.py 接入 v4**：入口直接实例化 `v4.main_window.MainWindow`，移除对旧 v2/v3 全局服务的依赖。

### refactor
- **清理 v2/v3 残留**：删除 `ui/managers/*` 下的 `phase_coordinator.py`、`queue_manager.py`、`session_manager.py`、`session_registry.py`、`signal_adapter.py`、`ui_renderer.py`、`worker_manager.py` 及对应测试，避免双轨维护成本。

### test
- 新增 `tests/test_v4_basics.py`、`tests/test_v4_gui_smoke.py`、`tests/test_v4_integration.py` 共 17 个测试，覆盖会话创建、消息持久化、会话切换、队列满/自动出队、停止任务、置顶、重名、并发槽位、重启恢复。
- 全量 192 项测试中 191 项通过；剩余 1 项 `tests/test_explorer_model.py::test_delete_non_empty_folder_fails` 与 v4 无关，系 Python 3.14 / Windows 环境下 `os.rmdir` 对非空目录返回成功但不删除的异常行为，已单独记录待跟进。

## v3.12.0 (2026-06-30) — AI Engine 架构升级：八引擎模块化 + Prompt 增强 + 记忆系统重构

### feat
- **八引擎模块化架构**：`agent_engine/engines/` 下新增 ContextEngine / PromptEngine / InferenceEngine / ToolEngine / PhaseEngine / MemoryEngine / MetricsEngine / PolicyEngine，每个引擎单一职责，通过 `interfaces.py` 抽象接口交互。
  - **ContextEngine**: 上下文组装、4 种压缩策略（滑动窗口/语义/实体保留/混合）、token 估算。
  - **PromptEngine**: System prompt 分层构建（基础+Phase+画像），支持 Analyze/Verify 追加而非覆盖。
  - **InferenceEngine**: LLM 调用、指数退避重试、模型降级（fallback_map）、指标反馈闭环。
  - **ToolEngine**: Phase 级工具白名单、敏感操作确认回调、超时与结果截断。
  - **PhaseEngine**: Mode-Phase 矩阵、插件扩展、硬 checkpoint 校验。
  - **MemoryEngine**: 三层记忆（会话/画像/项目），读取 app_root/.memory/ 注入 prompt。
  - **MetricsEngine**: 指标采集与聚合（avg/sum/max/min）、阈值告警。
  - **PolicyEngine**: dot-path 配置查询、模型选择决策、压缩触发判断。
- **绞杀者模式集成**：`AgentOrchestrator` 新增 `engines` 可选参数，有引擎则委托，无引擎回退旧逻辑。旧代码全部保留，零破坏。

### refactor
- **System prompt 增强**：三模式 prompt 加入角色定位、回复深度、推理链、语气风格要求，从 2-5 行扩展为结构化中文提示。
- **LLM 参数可配置化**：`llm_registry.py` 从 config 读取 temperature/top_p/max_tokens/request_timeout，替代硬编码。
- **User rules 增强**：从 2 条扩展为 6 条，含专业风格 + 项目规范约束。

### fix
- **记忆路径修正**：`SelfContext._build_memory_context()` 改用 `app_root/.memory/` 替代 `project_root/.workbuddy/memory/`。
- **Analyze 阶段不再覆盖基础 prompt**：`set_phase()` 中 analyze/verify 阶段在 base_system_prompt 后追加，不再替换。

### docs
- 新建 `.memory/` 目录（项目级记忆系统），含 MEMORY.md + 每日日志，已加入 `.gitignore`。
- `config.yaml` 新增 `ai_engine` 配置节（context/prompt/inference/tool/phase/memory/metrics）。
- 同步更新 `tests/test_self_context.py` 适配新路径。

## v3.11.4 (2026-06-29) — MainWindow 架构收敛与 UI 修复

### fix
- **新会话按钮只能添加一个标签**：`ui/main_window.py` 的 `_new_conversation` 彻底移除空会话守卫，每次点击都创建新会话，支持无限添加。
- **会话标签名均为"新对话"**：`_send_message_v3` 在首条用户消息后将会话标题与列表项文本更新为消息内容前 20 字；`ui/managers/session_manager.py` 的 `update_title` 补充 `Qt` 导入，修复 `Qt.UserRole` 未定义导致的标题不刷新。
- **Enter 键首次失效**：`_new_conversation`、`_on_session_switch`、`_switch_project` 在切换/新建完成后调用新增的 `_focus_input_field()`，通过 `activateWindow()` + `raise_()` + `QTimer.singleShot(0, setFocus(Qt.OtherFocusReason))` 强制输入框获得焦点，解决首次 Enter 被其他控件吞掉的问题。
- **项目新对话按钮触发 AttributeError**：`ui/widgets/sidebar.py` 补充 `FileTreeWidget.get_root_path()`，修复 `_on_new_conversation_requested` 中诊断日志调用不存在方法导致的崩溃。
- **切换新会话显示无意义接替上下文**：`services/self_context.py` 的 `build_handoff` 增加 `task.phase == "idle"` 守卫，避免任务刚创建、PhaseManager 尚未推进时切换会话显示"🔄 此会话中有未完成的任务 / 当前阶段: idle"。

### refactor
- **MainWindow 架构收敛**：移除 `_pending_queue`、`_worker`、`_workers`、`_phase_manager` 等旧全局状态的活跃使用，统一委托给 `SessionOrchestrator` / `WorkerManager` / `SessionRuntime` 的 v3 事件路径；保留兼容属性供测试引用。

### test
- 全量 214 个单元/集成测试通过。
- 新增 `tests/test_main_window_ui_automation.py` 覆盖三个 UI 修复点。

## v3.11.3 (2026-06-29) — 修复真实运行时 v3 Worker 无响应与状态卡死

### fix
- **WorkerManager 无法解析真实 LLM 导致任务永远卡住**：`ui/managers/worker_manager.py` 的 `_resolve_llm` 之前调用 LLMRegistry 不存在的 `has_provider` / `get`，真实运行时永远返回 `None`，Worker 创建失败、analyze 不执行、队列槽位不释放。现兼容测试 stub（`has_provider` / `get`）与真实注册表（`list_providers` / `get_llm`），并支持首个 provider 回退。
- **Phase 错误后状态机未 reset 导致后续消息 PHASE_BUSY**：`ui/managers/phase_coordinator.py` 错误路径补充 `self._phase_manager.reset()`；`services/session_orchestrator.py` 在 `PhaseFlowCompletedEvent` 处理后统一 reset，确保同一会话可继续发送新消息。
- **空对话守卫导致项目会话永远只有一个"新对话"标签**：`ui/main_window.py` 的 `_new_conversation_requested` 将守卫条件改为"已有空会话且不是当前选中"才复用，否则新建，使每次点击"+ 新对话"都能看到新标签。
- **新建会话后 Orchestrator 当前会话不同步**：`ui/main_window.py` 在创建新会话后调用 `self._orchestrator.switch_session(session_id)`，保证 `SessionOrchestrator._current_session_id` 与 `SessionManager` 一致，避免 UI 过滤与暂停/恢复逻辑错乱。
- **SessionManager 标题更新失效**：`ui/managers/session_manager.py` 的 `update_title` 改为使用 `Qt.UserRole` 获取 session_id，修复会话重命名/首条消息生成标题后 UI 不更新。

### chore
- 新增 `pytest.ini`，将 `testpaths` 限定为 `tests/`，排除 `scripts/test_llm_direct.py` 被 pytest 误识别导致的 fixture 错误。

### test
- 全量 210 个单元/集成测试通过。

## v3.11.2 (2026-06-29) — 修复 v3 Worker 重复创建与文档规范化

### fix
- **Worker 被重复创建导致 analyze 无法触发**：`services/session_orchestrator.py` 移除对 `worker.created` / `worker.execute_required` / `worker.verify_required` 的重复订阅，仅由 `WorkerManager` 统一处理 Worker 输入侧事件，避免 Worker 被覆盖后 `request_analyze` 丢失、消息发送无响应。
- **新 runtime 创建后 UI 状态未同步**：`SessionOrchestrator.create_runtime` 结束处调用 `_emit_queue_ui_state`，确保新会话发送按钮与队列条立即处于正确状态。

### docs
- **README 补全开发环境指引**：明确工作目录 `F:\Agent\agent_workbench`、venv 激活方式、`start.bat` 一键启动、`rebuild.ps1` 打包 + 桌面快捷方式。
- **定位语修正**：MT5 从头版标题移除，聚焦事件总线 + Phase-Driven Workflow + 多会话运行时隔离。
- **新增「AI 进入本工作区须知」**：声明不得盲目运行系统 Python/pip install，文档由存档流程统一维护。
- **同步修正 `docs/getting-started.md`**：对齐 Python 版本（3.14）、补全 cd + venv + activate 步骤、移除不存在的依赖（pandas/numpy）。
- **`PROJECT_BLUEPRINT.md` 存档流程规则对齐**：`git add` 扩展为全文档目录（git add -u + 显式新文档），标签推送改为单标签（禁 --tags）。

### test
- 新增 `tests/integration/test_v3_flow.py::test_worker_created_only_once`：验证 `UserSendEvent` → `WorkerCreatedEvent` 链路中 `AgentWorker` 只实例化一次且 `request_analyze` 只调用一次。
- 全量 210 个单元/集成测试通过。

## v3.11.1 (2026-06-29) — v3 事件流与会话切换修复

### fix
- **Worker 创建后未触发 analyze**：`core/events.py` 的 `WorkerCreatedEvent` 新增 `user_text` 字段；`ui/managers/worker_manager.py` 在 Worker 创建后立即调用 `request_analyze(event.user_text, event.context)`，解决消息发送后无响应。
- **会话切换后输入框/队列条状态未同步**：`services/session_orchestrator.py` 新增 `_emit_queue_ui_state`，在 `switch_session` 时向当前会话发射 `UISetSendEnabledEvent` 与 `UIUpdateQueueBarEvent`。
- **历史会话缺少 runtime**：`services/session_orchestrator.py` 与 `ui/main_window.py` 在切换历史会话时自动创建缺失的 `SessionRuntime`。
- **v3 切换会话误杀后台任务**：`ui/main_window.py` 的 `_abort_current_session_task` 在 v3 路径下仅停止旧路径 Worker，不再调用 `cancel_task`，避免 completed 任务被错误改回 failed。

### refactor
- 移除 `ui/managers/session_manager.py` 中 `current_session` setter 的 `traceback.print_stack` 调试输出。

### docs
- 恢复并完善 `README.md`，补充 v3 文件地图、快速启动、运行测试与 AI 认知加载路径。

### test
- 全量 209 个单元/集成测试通过。

## v3.11.0 (2026-06-29) — v3 架构重构：事件总线、会话运行时与统一协调器

### feat
- **事件总线（MessageBus）**：
  - `core/event_bus.py` 实现基于 Qt Signal 的强类型事件总线，支持 namespace/name 订阅与全量订阅。
  - `core/events.py` 定义全量跨组件事件（user.*、session.*、queue.*、phase.*、worker.*、ui.*）。
- **会话运行时聚合根（SessionRuntime）**：
  - `services/session_runtime.py` 每个会话拥有独立的 `PendingQueue`、`QueueManager`、`PhaseManager`、`PhaseCoordinator`。
  - 支持 Worker / Task 引用绑定、phase_state 快照、流式 chunk 标记。
- **统一协调器（SessionOrchestrator）**：
  - `services/session_orchestrator.py` 作为 v3 单一协调权威，持有所有 `SessionRuntime`。
  - 订阅 MessageBus 事件并路由到正确的运行时，保证任务完成路径唯一、会话切换状态不被覆盖。
- **PhaseCoordinator 解耦**：
  - `ui/managers/phase_coordinator.py` 将 `PhaseManager` 的 Qt 信号转换为带 `session_id` 的 Bus 事件。
  - 错误路径只发送一次系统消息，避免重复；`flow_finished.emit()` 在 `reset()` 之后执行，防止状态机重入。
- **WorkerManager 事件驱动化**：
  - `ui/managers/worker_manager.py` 订阅 `worker.*` 事件，统一创建/停止/复用 Worker，支持 pause/resume。
- **UI 渲染器（UIRenderer）**：
  - `ui/managers/ui_renderer.py` 统一订阅 `ui.*` 事件，按当前会话 ID 过滤并更新 `ChatView`、状态栏、会话列表、队列条等。
- **双槽位队列会话级化**：
  - `services/pending_queue.py` `PendingTask` 新增 `session_id` 字段。
  - `ui/managers/queue_manager.py` 封装会话级队列状态机，支持 `mark_current_done()` 唯一完成路径。
- **TaskService 终态保护**：
  - `services/task_service.py` 的 `complete_task`、`fail_task`、`cancel_task` 均跳过已到达终态的任务，避免覆盖 completed/failed。
  - `_drain_queue` 跳过 stale 队列项，不重新激活终端任务。

### refactor
- **MainWindow 绞杀者瘦身**：
  - `ui/main_window.py` 引入 `UIRenderer`，将用户操作转换为事件发射。
  - 新增 `_send_message_v3()` 路径，通过 `MessageBus` 委托给 `SessionOrchestrator`。
- **AppContext 延迟导入**：
  - `services/app_context.py` 延迟导入 `WorkerManager`，消除 `AppContext -> WorkerManager -> MainWindow -> AppContext` 循环依赖。

### test
- 新增 `tests/integration/test_v3_flow.py`：验证 `UserSendEvent` → `QueueStateChangedEvent` → `PhaseAnalyzeRequiredEvent` → `WorkerCreatedEvent` 完整事件链路。
- 新增 `tests/test_phase_coordinator.py`：`start_flow`、阶段变化、确认、完成、错误路径全覆盖。
- 新增 `tests/test_ui_renderer.py`：当前会话事件透传、非当前会话事件过滤、流式 finalize、Phase UI 事件处理。
- 新增 `tests/test_session_orchestrator.py` 与 `tests/test_session_runtime.py`：运行时生命周期、会话切换不覆盖终态、Phase 完成后状态清理。
- 全部 209 个单元/集成测试通过。

## v3.9.1 (2026-06-29) — 修复 Phase 状态机重入与任务状态回收

### fix
- **Phase 状态机重入**：`agent_engine/phase_manager.py` 中 `flow_finished.emit()` 在 `reset()` 之前执行，导致新任务启动时 PhaseManager 仍处于 ARCHIVE 状态而被 PHASE_BUSY 拦截。已调整为先 `reset()` 再 `emit()`。
- **任务状态未回收**：`MainWindow` 各完成/错误路径改为统一调用 `TaskService.complete_task()`，确保 `task_status_changed` / `task_completed` / `capacity_changed` 信号发射，UI 状态正确刷新。
- **会话切换覆盖已完成状态**：`_abort_current_session_task()` 原本无条件 `cancel_task()`，会把 completed 任务改回 failed。改为仅对 active 状态任务取消，保留已完成状态。
- **会话列表 completed 图标缺失**：`ui/widgets/conversation.py` 的 `update_task_status()` 增加 `"completed": "✅ "`，已完成的任务显示绿色。
- **SessionManager 标题更新失效**：`ui/managers/session_manager.py` 中 `item.data(1)` 改为 `item.data(Qt.UserRole)`，会话重命名后 UI 正确更新。

### refactor
- **Worker/任务资源回收闭路**：`_on_phase_flow_finished`、`_on_phase_error`、`_on_worker_error`、`_on_result`（空结果）路径统一清理 `_workers` 字典和 `WorkerPool` 资源。
- **Managers 模块化准备**：完善 `ui/managers/session_registry.py`、`worker_manager.py`、`phase_coordinator.py`、`queue_manager.py`，为后续 MainWindow 绞杀者模式接入做准备。

### test
- `tests/test_pending_queue.py`：更新 `mark_task_completed` 相关测试用例。
- `tests/test_self_context.py`：补充任务状态上下文测试。

## HANDOFF (2026-06-27) — v3.9.0 模型交接
- 移交模型: Kimi-K2.7-Code
- 交接内容: TaskService + WorkerPool 多任务管理、Session-as-Room 会话隔离、Trae 暗黑主题、底栏状态条、会话状态图标
- 状态: 全部单元测试通过，已推送 origin/main + tag v3.9.0

## v3.9.0 (2026-06-27) — 多任务管理系统 + Trae 暗黑主题

### feat
- **多任务管理系统（TaskService + WorkerPool）**：
  - `services/task_service.py`：任务生命周期管理，`submit_task()` / `on_phase_change()` / `on_tool_start()` / `on_tool_end()` / `mark_completed()`
  - `workers/task_capacity.py`：资源容量控制，最大并发任务/排队任务/工具数
  - `workers/task_queue.py`：FIFO 排队与超时驱逐
  - `workers/worker_pool.py`：Worker 实例池管理
  - `workers/session_task.py`：会话级任务状态跟踪（analyzing → executing → verifying → confirm → completed/failed）
  - `workers/task_worker_adapter.py`：TaskService 与 AgentWorker 之间的适配桥接
  - 相关信号：`task_status_changed` / `capacity_changed` / `task_progress` / `tool_usage_changed` / `task_completed`

- **Session-as-Room (v3.9.0 会话隔离)**：
  - `_on_session_switch()` 实现完整 AB 切换协议：detach(旧) → save phase → switch → clear → load(新) → render → reattach(新)
  - `_make_current_only_guard()` 信号路由守卫：同时校验 Worker 实例和当前会话 ID，防止跨会话消息泄漏
  - `_detach_ui_signals()` / `_attach_ui_signals()` 信号解绑/重绑，Worker 后台继续运行
  - `_save_phase_state()` / `_restore_confirm_ui()` 跨会话保存/恢复 confirm 阶段状态
  - `_append_ai_message()` 按 session_id 独立落盘，后台 Worker 完成时无条件写入 SQLite

- **Trae 暗黑主题**：
  - `resources/themes/trae_dark.qss`：637 行 QSS，覆盖 QMainWindow / QListWidget / QTreeWidget / QTextEdit / QLineEdit / QPushButton / QLabel / QStatusBar / QScrollBar
  - 色值基于 Trae IDE 暗黑风格（深紫灰 #1e1e2e、选中指示器 #89b4fa、绿色 #a6e3a1、黄色 #f9e2af、红色 #f38ba8）
  - `ThemeService` 支持 frozen exe 路径解析（`sys._MEIPASS`），`trae_dark` 设为默认主题

- **底栏容量状态条**：
  - `QLabel` 永久控件显示：🟢 任务:0/3 | ⏳ 排队:0/5 | 🔧 工具:0/12
  - 实时响应 `capacity_changed` / `tool_usage_changed` 信号刷新

- **会话列表状态图标**：
  - `ConversationItem.set_task_status()` 方法，emoji 图标：🟢(运 行) / 🟡(确认) / ⏳(排队) / 🔴(失败)

### fix
- **信号调试管道**：添加 `_log_signal` 装饰器在 emit 端记录信号轨迹，`[RECV]` 日志在 recv 端确认到达
- **ThemeService 路径修复**：exe 环境下 `get_qss()` 使用 `_MEIPASS` 解析相对路径
- **AgentWorkbench.spec**：补充 `trae_dark.qss` 到 PyInstaller datas

### test
- `tests/test_agent_session_integration.py`：Analyze → Execute → Verify 全链路状态隔离 + phase_messages 滑动窗口
- `tests/test_main_window_session_isolation.py`：会话切换信号守卫 / 同 session ID 放行 / 切回非当前会话丢弃

## v3.8.1 (2026-06-27) — 填充架构占位 + 对话气泡与活动面板交互优化

### feat
- **填充 4 个架构占位文件**：
  - `tools/screen.py`：基于 ctypes + gdi32 的屏幕截图与显示器信息，无 Pillow 外部依赖。
  - `ui/overlay.py`：`OverlayWidget` 全局半透明遮罩层，支持淡入淡出动画与进度条。
  - `ui/settings.py`：`SettingsPage` 嵌入式设置页，含 LLM 提供商 / 用户规则 / 界面日志三栏。
  - `ui/tools_panel.py`：`ToolsPanel` 工具开关面板，按分类展示并允许启用/禁用。
- **屏幕工具注册**：`tools/__init__.py` 与 `workers/agent_worker.py` 的 `TOOL_DEFINITIONS` 已注册 `screen_capture`、`screen_info`。
- **活动面板多选增强**：右侧「当前项目 / 全局」列表开启 `ExtendedSelection`，支持 Ctrl+A 全选、Ctrl/Shift 连选、右键「复制选中项」。

### fix
- **对话气泡排版**：`ui/chat_view.py` 改为圆角矩形气泡，用户气泡右对齐、文本统一左对齐，最大宽度 85%，解决多行文本边缘不齐问题。
- **确认卡片排版**：系统/确认消息改为居中卡片样式，任务清单与操作提示使用有序/无序列表工整呈现。

## v3.8.0 (2026-06-27) — MVC 资源管理器、持久化服务与生产修复

### feat
- **MVC 资源管理器**：新增 `ui/models/explorer_tree_model.py`（QAbstractItemModel）、`ui/widgets/explorer_view.py`（QTreeView + emoji 委托），重构 `ui/widgets/explorer.py` 为 Controller，支持懒加载与过滤。
- **PersistenceService**：新增 `services/persistence_service.py`，集中处理 mode/model/UI 状态持久化，替换 `MainWindow` 中分散的 `config_service` 直接访问。
- **MemoryManager 画像 schema**：`config.yaml` 新增 `memory.user_profile_defaults`（含 `schema_version`）；`agent_engine/memory_manager.py` 实现双边版本判断、安全合并与迁移钩子，运行时画像仅补齐缺失字段，不覆盖用户已有值。
- **模式/模型持久化边界测试**：新增空模型列表、损坏 mode 配置自动修复、跨 mode 隔离、空 config 文件启动回退等 4 个高/中高风险边界 case。

### fix
- **依赖补全**：`requirements.txt` 补充 `python-dotenv`，避免新环境 `ModuleNotFoundError`。
- **PyInstaller hiddenimports 对齐**：`AgentWorkbench.spec` 补充 `services.persistence_service`、`services.mcp_service`、`ui.models.explorer_tree_model`、`ui.widgets.explorer_view`、`ui.widgets.explorer`，并修正版本注释为 v3.8。
- **工具定义对齐**：`workers/agent_worker.py` 的 `TOOL_DEFINITIONS` 补齐 `run_python`、`run_powershell`、`run_bash`，与 `tools/__init__.py` 的 `TOOL_MAP` 一一对应，确保 LLM 可见。

### test
- 新增 `tests/test_memory_manager.py`，覆盖默认值初始化、缺失字段补齐、嵌套 dict 不覆盖、版本迁移触发、`schema_version` 防覆盖。
- 补充 `tests/test_persistence_service.py` 4 个模式/模型持久化边界 case。

## v3.7.4 (2026-06-27) — Analyze 阶段强制只读工具

### feat
- **Analyze 阶段强制收集信息**：在 Plan/Craft 模式的 `_build_analyze_prompt` 中新增"工具调用要求"，要求 LLM 在输出 JSON 任务清单前，必须先调用 `read_file`、`list_dir`、`web_fetch` 等只读工具收集必需信息。
- **工具结果截断对齐**：`AgentOrchestrator.TOOL_RESULT_MAX_LEN` 从 3000 调整为 5000，与 `read_file` 工具声明的 "first 5000 chars" 保持一致。

### fix
- **Analyze 摘要保留长度不足**：`AgentSession.run_analyze` 中 `phase_messages` 的 AI 摘要从 800 字符提升到 1500 字符，减少 Verify 阶段信息丢失。

## v3.7.3 (2026-06-26) — 分级超时与持久化路径修复

### feat
- **分级超时控制**：`AgentOrchestrator` 内 LLM 调用与单轮工具调用分别使用 `asyncio.wait_for` 控制，错误码区分为 `LLM_TIMEOUT` / `TOOL_TIMEOUT`，任务总超时仍为 `TASK_TIMEOUT`。
- **模型/模式持久化**：`config.yaml` 新增 `app.last_mode` / `app.last_model`；切换模式时保留当前选择的模型；启动时自动恢复上次模式/模型。

### fix
- **统一持久化路径**：`MainWindow` 统一计算 `_app_storage_dir`，`SessionService`、`MemoryManager`、`ActivityService` 均使用同一目录，避免开发与打包后数据库位置漂移。
- **本地验证使用 venv Python**：`MainWindow._run_local_verification()` 优先通过 `InterpreterService` 选择项目 venv Python 执行语法检查与单元测试。
- **隐藏系统工具控制台窗口**：`tools/system.py` 所有 `subprocess.run/Popen` 统一添加 `CREATE_NO_WINDOW`，避免 AI 调用工具时闪烁 PowerShell/CMD 黑窗。

## v3.7.2 (2026-06-26) — 修复 v3.7.1 打包启动崩溃

### fix
- **窗口标题初始化顺序**：将动态读取 `app.version` 的代码移到 `config_service` 初始化之后，修复 PyInstaller 打包后启动报 `AttributeError: 'MainWindow' object has no attribute 'config_service'`。

## v3.7.1 (2026-06-26) — 修复启动弹窗、历史会话与终端输入

### fix
- **启动隐藏控制台窗口**：`InterpreterService` 解释器版本检测使用 `CREATE_NO_WINDOW`，避免启动时闪烁 PowerShell/CMD 黑窗。
- **历史会话 AI 回复丢失**：在 `_on_phase_result` 中统一持久化 analyze/verify 阶段的 AI 完整回复，重开程序后对话历史完整可读。
- **终端输入框无法编辑**：重构 `TerminalWidget`，使用 `TerminalInput(QLineEdit)` 子类重写 `keyPressEvent`，恢复默认文本编辑并保留 ↑↓ 历史切换。

### feat
- **窗口可持续迭代**：`config.yaml` 新增 `app.version`，主窗口标题动态读取，后续升级无需改代码。
- **活动面板增强**：增加「当前项目 / 全局」说明文字；系统级活动（模式/模型切换、设置更新、解释器切换等）归入全局；列表与详情区右键支持「复制」「全选」。

## v3.7 (2026-06-26) — 终端解释器管理与 AI 上下文感知

### feat
- **终端解释器管理**：新增 `InterpreterService`，自动发现 Python(venv/系统)/PowerShell/CMD/Git Bash，支持手动下拉切换与持久化。
- **终端 UI 增强**：`TerminalWidget` 顶部新增解释器选择下拉框，切换时自动清空终端。
- **解释器上下文注入**：`ContextService` 将当前终端解释器信息注入 prompt，Agent 可知悉可用解释器。
- **解释器专用工具**：`tools/system.py` 新增 `run_python` / `run_powershell` / `run_bash`，AI 可直接调用指定解释器执行命令。

### refactor
- `TerminalWorker` 同时支持 str（shell=True）与 list（shell=False）命令执行。

### fix
- 修复 `workers/terminal_worker.py` 缩进错误导致的模块无法导入问题。
- 修复 `MainWindow` 中 `_project_root` 未初始化就传给 `InterpreterService` 的顺序错误。
- 修复 `TerminalWidget` 创建时未传入 `interpreter_service` 导致下拉框为空的问题。

### test
- 新增 `tests/test_interpreter_service.py`，覆盖解释器发现、选择、命令构造。

## v3.6 (2026-06-26) — Phase-Driven Workflow Engine

### feat
- **阶段驱动工作流**：新增 `PhaseManager`，将每次请求按 Mode 切分为 Analyze → Confirm → Execute → Verify → Archive。
- **Mode × Phase 矩阵**：Ask 只分析/归档；Plan 分析+确认+归档；Craft 完整五阶段。
- **任务清单驱动**：Analyze 阶段让 LLM 输出结构化任务清单，经用户确认后进入 Execute。
- **软硬 Checkpoint 分离**：用户确认、危险命令等为硬门控；语法检查、单元测试为可跳过软提示。
- **Phase 上下文切换**：`ContextService.get_phase_context()` 按阶段注入不同上下文。
- **UI 阶段指示器**：底部状态栏显示 `[分析中]` `[等待确认]` `[执行中 N/M]` `[验证中]` 等阶段标签。
- **确认门控**：对话区显示任务清单 + 「确认执行」/「重新分析」按钮，防止 AI 直接写错代码。
- **Orchestrator.run_phase()**：新增 phase-aware 入口，Analyze/Verify 阶段不绑定工具，输出结构化结果。

### refactor
- `AgentWorker` 增加 `phase` 参数，复用同一 worker 完成不同阶段调用。
- `MainWindow._send_message()` 改为启动 `PhaseManager` 工作流，而非直接创建 worker。

### fix
- 修复 `AgentWorkbench.spec` 文件头 BOM/零宽字符污染。

### test
- 新增 `tests/test_phase_manager.py`，覆盖 Mode×Phase 矩阵、软硬 checkpoint、阶段流转、任务解析。

## v3.5 (2026-06-26) — 推理指标：Token 与响应时间可视化

### feat
- **单轮指标收集**：新增 `MetricsCollector`，基于 `time.perf_counter()` 在 `AgentWorker` 线程内零额外线程地记录 TTFT、总耗时、input/output tokens。
- **AI 气泡指标 footer**：每次 AI 回复气泡右下角显示 `33546tok/34ms` 格式。
- **Orchestrator metrics callback**：`metrics_start` / `metrics_first_token` / `token_usage` 三个 callback 接入指标采集。

### refactor
- `BaseWorker` 新增 `turn_metrics_ready` 信号，将 `TurnMetrics` 从 worker 线程传回主线程。
- `AgentWorker` 转发 chunk 时自动标记首 token 时间；最终 usage_metadata 提取后统一 emit `token_used` + `turn_metrics_ready`。
- `MainWindow._on_token_used` 仅保留持久化，UI 展示与详细日志由 `_on_turn_metrics_ready` 统一处理，状态栏不再显示 token。

### chore
- 新增 `services/metrics_collector.py` 单元测试与 DeepSeek 集成测试。
- 更新 `AgentWorkbench.spec` hiddenimports。

## v3.4 (2026-06-26) — 工作空间上下文感知

### feat
- **项目目录自动检测**：启动时基于当前工作目录或最近活动自动检测 Project Root。
- **右侧文件上下文注入**：活动文件自动提取前 500 字符摘要，随 prompt 注入 Agent。
- **文件工具相对路径解析**：新增 `PathResolver`，基于项目根目录解析相对路径。
- **工作空间上下文服务**：新增 `ContextService`，统一管理项目根目录、活动文档、打开文档、选中项。
- **资源管理器最近项目**：顶部新增「打开文件夹」按钮 + 最近项目下拉切换。

### refactor
- `tools/system.py` 文件工具接入项目根目录解析。
- `AgentWorker` 向系统工具注入当前项目根目录。
- `orchestrator` system prompt 接入 workspace_context。

### chore
- 新增 `tests/test_context_service.py` 单元测试。
- 更新 `AgentWorkbench.spec` hiddenimports。

## v3.3 (2026-06-25) — 精细化：文件预览、纯对话、分栏与活动面板

### feat
- **任意格式文件预览**：文档编辑器支持文本、图片、二进制文件预览；二进制文件显示 MIME、大小、十六进制预览。
- **双击编辑**：文本文件双击编辑区自动进入编辑模式；工具栏显示 编辑 / 取消 / 保存 按钮。
- **纯对话**：新建对话支持「项目新对话」与「纯对话」两种类型；纯对话不绑定任何目录。
- **对话列表分栏**：左侧对话 Tab 分为「当前项目」与「全局」两栏。
- **活动面板**：右侧工作区「日志」标签改为「活动」标签，以中文标题 + 类别 + 时间展示事件；分「当前项目 / 全局」两栏，点击展开详情。
- **结构化活动记录**：新增 `ActivityService`，持久化活动到 JSON。

### refactor
- `WorkspaceWidget` 用 `ActivityWidget` 替换原有日志 QTextEdit。
- `DocumentEditor` 重写文件类型检测与展示逻辑，支持取消编辑恢复原始内容。
- `ConversationListWidget` 重构为双列表分栏结构。

### fix
- 修复模型切换后 `current_model` 未正确持久化到 `config.yaml` 的问题。
- 修复文件打开时产生重复活动记录的问题，并在活动详情中显示文件大小。
- 修复对话列表「当前项目」标题在多次切换目录后无法更新的问题。

### chore
- 文档编辑器新增 `Ctrl+S` 保存、`Esc` 取消编辑快捷键。

## v3.2 (2026-06-25) — 项目目录与对话上下文

### feat
- **项目目录管理**：新增 `ProjectService`，支持按项目目录组织会话，当前目录持久化到 `config.yaml`。
- **资源管理器增强**：文件树顶部新增「打开文件夹」「刷新」按钮、当前路径显示、Ctrl+O 快捷键。
- **目录右键菜单**：树视图右键支持「在当前目录开启新对话」「切换到该文件夹」「在该文件夹下开启新对话」「在右侧打开」。
- **目录下新对话**：新建对话自动关联当前项目目录；切换目录时自动加载该目录下的历史会话。

### refactor
- `SessionService` 新增 `project_path` 字段，支持按目录过滤与会话迁移。
- `MainWindow` 会话初始化改为按当前项目目录加载；移除固定 `default` 会话概念。
- `FileTreeWidget` 支持动态 `set_root_path` 与文件夹/文件点击区分。

## v3.1 (2026-06-25) — 右侧工作区重构

### feat
- **右侧工作区标签页**：新增 `WorkspaceWidget`，顶部集成“终端 / 日志 / 文档”三标签切换。
- **文档编辑器**：新增 `DocumentEditor`，支持文本文件预览、只读/编辑模式切换、保存、二进制文件检测、大文件提示。
- **文件树联动**：左侧资源管理器选中文件后，右侧自动切换到“文档”标签并显示内容。
- **日志自动截断**：日志面板迁移到工作区，保留最大行数限制与自动清理。

### refactor
- `ui/main_window.py` 中央区域仅保留 `ChatView`，底部终端移除，右侧改为 `WorkspaceWidget`。
- 侧边栏“终端”按钮改为聚焦右侧工作区终端标签。
- 日志面板显隐开关改为控制整个右侧工作区可见性。

### fix
- 样式表补充工作区、标签栏、文档编辑器样式，保持 GitHub Dark 主题一致。

## v3 (2026-06-25) — 生产级工具编排、身份系统、UI/UX 全栈修复

### feat
- **工具层级编排**: 17 个工具按 [PRIORITY-1/2/3] 分级，web_fetch 优先于 MT5
- **工具按模式分配**: Ask=11 个(无MT5/破坏性)，Plan=13个(+回测)，Craft=17个(全量)
- **AI 身份声明**: system_prompt 注入 "YOUR IDENTITY"，不再冒充 Claude/GPT
- **系统工具库扩展**: +9个工具(read_file/write_file/list_dir/web_fetch/clipboard/clipboard_write/send_notification/list_processes/kill_process)
- **用户规则系统**: config.yaml user_rules + SettingsDialog 规则编辑标签页
- **桌面快捷方式**: .lnk + app.ico 图标，rebuild.ps1 自动刷新
- **用户画像注入**: user_profile.json → system_prompt 自动合并
- **工具描述标准化**: 全部 17 个工具 description 带 [PRIORITY-X] + 触发词约束

### fix
- **工具调用不执行**: astream() → ainvoke()，tool_calls 正确检测和执行
- **<tool_calls> XML 泄露**: response.content 归零 + 历史消息渲染过滤
- **API Key 回写泄露**: LLMRegistry._save() 自动替换为 ${VAR} 占位符
- **SSL 证书缺失**: certifi/cacert.pem 嵌入 + runtime_hook.py 自动设置
- **Ollama 内存溢出**: OLLAMA_CONTEXT_LENGTH=4096 环境变量
- **gemma2 工具调用异常**: AgentWorker 跳过 bind_tools
- **会话记忆丢失**: LangChain 历史注入(切换/发送/回复三处)
- **中文编码损坏**: sidebar.py QLabel 重写

### refactor
- Act → Craft 重命名(main.py/chat_view/status_indicator/PROJECT_BLUEPRINT)
- ChatView 布局重构: 底部控件栏(模式按钮左/发送右) + 多行输入
- system_prompt 英文化 + 精简(3种模式各 ≤6行)
- PyInstaller excludes: 排除20+未用Qt模块(setuptools/QtWebEngine等)

### chore
- Ollama 环境: OLLAMA_CONTEXT_LENGTH=4096, OLLAMA_NUM_PARALLEL=1
- rebuild.ps1 自动刷新桌面 .lnk 快捷方式

## v0.3 (2026-06-25) — v2生产级重构：模块化架构、8工具实现、流式UI

### feat
- **模块化架构重构**: main.py 从 1546 行拆分为 45 行入口 + 18 个模块文件（ui/widgets/, ui/dialogs/, workers/, services/）
- **流式输出**: AgentWorker 基于 astream() 逐 token 渲染，打字机效果
- **停止生成**: 新增 Stop 按钮 + Escape 快捷键
- **键盘快捷键**: Ctrl+Enter 发送 / Ctrl+L 清空 / Escape 停止
- **外部 QSS 主题**: resources/themes/dark_github.qss，GitHub Dark 深色风格
- **对话持久化**: SQLite 三表（conversations/messages/token_usage），重启不丢失
- **Token 追踪**: 按 provider/model 统计用量，状态栏实时显示
- **终端命令历史**: TerminalWidget 支持 ↑↓ 导航历史命令
- **状态指示器**: StatusIndicator 显示连接状态、当前模式、Token 计数
- **新增工具**: fetch_financial_news（全球财经快讯）、fetch_macro_data（CPI/GDP/PMI）
- **工具升级**: fetch_stock_data（akshare A股/港股/美股）、run_backtest（backtrader 均线策略）、mt5_get_price/place_order（MT5 + Forex API 双通道）
- **模型选择**: QComboBox 下拉 + ⚙ 齿轮按钮进入 SettingsDialog

### refactor
- AgentWorker → workers/agent_worker.py（流式 + 工具调用）
- TerminalWorker → workers/terminal_worker.py
- ChatView → ui/chat_view.py（流式渲染 + 模型下拉 + 快捷键）
- SettingsDialog / ProviderFormDialog → ui/dialogs/settings.py
- SidebarButton / FileTreeWidget → ui/widgets/sidebar.py
- ConversationListWidget → ui/widgets/conversation.py
- TaskListWidget → ui/widgets/tasks.py
- TerminalWidget → ui/widgets/terminal.py
- MainWindow → ui/main_window.py

### chore
- .env 密钥管理：API Keys 从 config.yaml 移至 .env（加入 .gitignore）
- ConfigService：.env 优先 → config.yaml 回退的统一配置层
- SessionService：SQLite 对话持久化服务
- ThemeService：QSS 主题加载与切换服务
- PyInstaller spec 更新：新增 hiddenimports 和 datas 路径

## v0.2 (2026-06-25) — DeepSeek密钥修复与模型选择下拉功能
### fix
- 修复 DeepSeek API key 为占位符导致的 401 认证失败
- 更新 model 名称 deepseek-chat → deepseek-v4-flash（旧名 2026/07/24 废弃）

### feat
- 新增 deepseek-pro provider，支持 V4 Pro 旗舰模型
- 工具栏新增模型下拉选择器（QComboBox），实时切换 LLM 提供商
- 新增模型设置对话框（SettingsDialog），支持添加/编辑/删除提供商
- 新增 ProviderFormDialog，支持填写 name/base_url/api_key/model 并测试连接
- llm_registry 重构：支持运行时增删改查并持久化到 config.yaml
- 模型切换自动持久化到当前模式的 current_model 字段

### refactor
- default_llm → current_model 配置项重命名
- LLMRegistry 支持可写路径，打包模式下写入 exe 同目录 config.yaml

## v0.1 (2026-06-24) — 初始提交AI工作台项目
### feat
- 手动模式切换（Ask / Plan / Act），所有模式共享完整工具权限
- 集成系统命令、管理员提权、股票数据、回测、MT5 等工具
- Trae 风格深色 UI：资源管理器、对话列表、任务列表、终端控制台、Agent 日志
- 敏感操作二次确认机制
- PyInstaller 一键打包脚本 rebuild.ps1
- 配置驱动：config.yaml 管理模式、模型、工具与记忆
