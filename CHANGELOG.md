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
- 修复活动记录存储路径未兼容 PyInstaller 打包环境的问题。

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
- **外部 QSS 主题**: resources/themes/dark_github.qss，GitHub 深色风格
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
