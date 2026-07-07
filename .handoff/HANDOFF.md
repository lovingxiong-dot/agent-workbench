---
generated: 2026-07-08T02:00:00+08:00
agent: Kimi-K2.7-Code
schema_version: 3.1

## Mission
基于 `v6.8.0-alpha` Framework Core Foundation Baseline，在 `v6-agent` 分支构建 V6 框架内第一个真实 Agent 产品实例 **AI Agent Workbench V6**，实现 10 个 RuntimeModule 的运行时可统一配置能力，并通过 UI 配置面板支持 Runtime 热更新。目标不是功能做全，而是把所有可调能力统一管理。

## Progress
- [x] 10 个 RuntimeModule 落地：Runtime / Session / Config / Profile / Prompt / Model / Tool / Memory / Strategy / Trace。
- [x] `ConfigStore` YAML 唯一配置源 + 内存缓存 + 点分路径 get/set/delete + namespace 变更通知。
- [x] `ProfileManager` 独立管理 Profile 切换 / 导入 / 导出 / 合并。
- [x] `ModuleRegistry` 统一注册与生命周期管理。
- [x] `AgentWorkbenchRuntime` 组合 ConfigStore/ProfileManager/ModuleRegistry/CoreAgentRuntime，注册 WorkbenchLLMEngine / WorkbenchToolEngine。
- [x] `WorkbenchController` 作为 Application Layer 唯一入口，UI 不直接持有 Module。
- [x] v6 三栏 UI 扩展：WorkbenchLeftPanel「设置」按钮、WorkbenchRightPanel「配置」标签页、AgentConfigPanel JSON 编辑器。
- [x] `WorkbenchUIController` 继承 v6 UIController，聊天请求转发给 WorkbenchController。
- [x] 7 个 Workbench 端到端测试 + 175 个 V6 核心测试，合计 182/182 通过。
- [x] PyInstaller 打包验证通过，`dist/AgentWorkbenchV6.exe` CLI/GUI 均可独立启动。
- [x] Git 归档完成：commit `d02d5a2`，tag `v6.9.0-alpha`，已推送 `v6-agent` 分支与标签到 origin。

## Blocker
无。

## Decision Log
1. **决策**：配置/Prompt/Memory 工程先下放到 Agent 层，不在 v6-core/v6-service 中实现。
   - 排除：在 Core 中提前实现完整 Memory/Prompt 服务——会过早绑定具体实现，且第一版目标是验证「可配置」而非「真实能力」。
   - 状态：已执行。

2. **决策**：ConfigStore 使用 YAML 唯一源 + 内存缓存，不把配置写入 SQLite。
   - 排除：YAML + SQLite 双存储——会带来同步问题，且配置本质是资源文件，应支持 Git diff。
   - 状态：已执行。

3. **决策**：ProfileManager 独立于 ConfigStore。
   - 排除：把 Profile 逻辑合并进 ConfigStore——两者职责不同（ConfigStore 管当前配置读写通知，ProfileManager 管 Profile 切换/导入/导出/合并）。
   - 状态：已执行。

4. **决策**：热更新直接走 ConfigStore → EventBus → Module.apply_config()，不引入独立 HotReloadManager。
   - 排除：第一版引入 HotReloadScheduler / debounce——属于优化而非架构，后续需要时再抽。
   - 状态：已执行。

5. **决策**：模块基类命名为 `BaseRuntimeModule`，不叫 `RuntimeModule`。
   - 排除：`RuntimeModule` 会与具体 Runtime 模块类名冲突，且模块未来会承担生命周期/初始化/释放，基类名应更准确。
   - 状态：已执行。

6. **决策**：Prompt 使用 `PromptRenderer` 统一接口，第一版实现 `PythonRenderer`（`str.format()`），不用 `string.Template`。
   - 排除：直接上 Jinja2 或 string.Template——前者引入外部依赖，后者未来一定会换，会产生过渡性 Registry 改动。
   - 状态：已执行。

7. **决策**：Memory 第一版只提供 SQLite CRUD + namespace，不引入 Embedding / 向量搜索 / RAG。
   - 排除：第一版做向量召回——超出「可配置」目标，且需外部依赖。
   - 状态：已执行。

8. **决策**：模型 Provider 统一接口，EchoProvider 只是众多 Provider 之一，不做特殊处理。
   - 排除：Workbench 内部硬编码 Echo 逻辑——未来替换 OpenAI/Gemini/Claude 时需要改 Workbench。
   - 状态：已执行。

9. **决策**：UI 配置面板使用通用 JSON 编辑器，第一版不为每个模块定制表单。
   - 排除：为 10 个模块各自写专用表单——开发量大，且第一版重点是验证「查看/修改/保存/热更新」四件事。
   - 状态：已执行。

10. **决策**：Workbench UI 完全基于 v6 三栏高级 UI 扩展，不做老 UI 兼容。
    - 排除：混合老 UI 布局或保留旧代码路径——会破坏 v6 UI 设计一致性。
    - 状态：已执行。

11. **决策**：`main.py` 切换到 `agent_workbench.app` 入口，作为 V6 Workbench 主入口。
    - 排除：保留 `main.py` 指向 v5——v5-dev 已冻结，当前主线是 v6-agent。
    - 状态：已执行。

## Key Files
- `agent_workbench/runtime/agent_runtime.py` — `AgentWorkbenchRuntime`，组合所有模块与 CoreRuntime。
- `agent_workbench/runtime/config_store.py` — YAML 唯一配置源 + namespace 通知。
- `agent_workbench/runtime/profile_manager.py` — Profile 切换/导入/导出/合并。
- `agent_workbench/runtime/module_registry.py` — 10 个模块注册与生命周期。
- `agent_workbench/runtime/modules/base.py` — `BaseRuntimeModule` 抽象基类。
- `agent_workbench/runtime/modules/{runtime,session,config,profile,prompt,model,tool,memory,strategy,trace}_module.py` — 10 个模块。
- `agent_workbench/controller.py` — `WorkbenchController`，Application Layer 唯一入口。
- `agent_workbench/engines/workbench_llm_engine.py` / `workbench_tool_engine.py` — Workbench 专用 Engine。
- `agent_workbench/services/{model_provider,echo_provider,prompt_renderer,python_renderer,tool_registry,memory_service}.py` — 能力服务。
- `agent_workbench/ui/main_window.py` — `WorkbenchMainWindow` 三栏主窗口。
- `agent_workbench/ui/left_panel.py` — 左栏新增「设置」按钮。
- `agent_workbench/ui/right_panel.py` — 右栏新增「配置」标签页。
- `agent_workbench/ui/config_panel.py` — `AgentConfigPanel` 配置面板。
- `agent_workbench/ui/workbench_ui_controller.py` — UI 与 Workbench Runtime 桥接。
- `agent_workbench/app.py` — CLI/GUI 双入口。
- `agent_workbench/config/default.yaml` — 完整 10 模块默认配置。
- `agent_workbench/tests/test_agent_workbench.py` — 7 个端到端测试。
- `agent_workbench.spec` — PyInstaller 打包配置。
- `main.py` — 已切换为 V6 入口。
- `v6/runtime/planner_loop.py` — 补充 `set_policy()` 公共方法，支持运行时切换策略。

## Error Log
No error.

## Environment Snapshot
- branch: v6-agent
- python: Python 3.14.6
- venv: none
- last_commit: d02d5a2 feat(agent): 实现 Agent Workbench V6 单一实例与运行时配置面板 [test:182/182] [hint:v6.9.0-alpha workbench config ui] (by AI-Kimi-K2.7-Code)

## Working State
### Dirty Files
working tree clean

### Uncommitted Changes Summary
no uncommitted changes

### Recent Conversation
- 用户确认将 `demo_agent` 升级为 **AI Agent Workbench V6**，去掉 demo 命名，作为迭代多次的最高级 workbench。
- 用户要求 UI 中左下角主题和设置两个按钮直接赋值定义，实现 Agent Configuration 面板。
- 用户强调 UI 工作要做完整仔细全面，完全用新 UI 设计思路，不得改变。
- 用户确认方案后要求全面实施；实施完成后要求存档 push 移交，任务分几个推进写清楚，然后进行下一步。

## Next Steps (AI-Inferred)
1. **切换到 `v6-service` 分支，推进 V6 Runtime Service Architecture**（最高优先级）
   - 基于 `v6.8.0-alpha` Framework Core Foundation Baseline 与 `v6.9.0-alpha` Agent Workbench 产品实例经验。
   - 候选服务：Memory Service、Prompt Service、Model Adapter、Tool Adapter、Knowledge Adapter。
   - 原则：Service 属于 Runtime 能力接入层，不是 Engine 业务逻辑；保持 `RuntimeContext` 作为唯一 Public Protocol；`v6-core` 只接受 bug fix。
2. **细化 Service 层接口设计**
   - Memory Service：Backend 抽象（SQLite/Remote/LAN），基础 CRUD + namespace，不引入 embedding/向量搜索。
   - Prompt Service：Prompt 管理 + Renderer 抽象，支持本地文件 provider。
   - Model Adapter：统一 Provider 接口，接入真实 LLM（OpenAI/Claude/Gemini/DeepSeek/Ollama）。
   - Tool Adapter：Tool 执行沙箱与外部工具调用协议。
   - Knowledge Adapter：知识库接入（未来）。
3. **保持 v6-agent 可运行**
   - v6-service 的新能力通过单向合并进入 v6-agent，确保 Agent Workbench 持续可用。
4. **未来：自治 Agent 循环（更远期）**
   - 待 Service Architecture 与真实 Adapter 稳定后再评估多轮决策循环。

## Test Status
- latest: [test:182/182]
- command: `python -m pytest agent_workbench/tests/ tests/v6/ -q --tb=short`

## Notes
- `v6.9.0-alpha` 已归档并推送，tag 为 `v6.9.0-alpha`。
- 三条垂直支线保持不变：`v6-core`（冻结）→ `v6-service`（当前下一步）→ `v6-agent`（当前分支）。
- 禁止反向合并：`v6-agent`、`v6-service` 不得反向合并入 `v6-core`；`v6-agent` 不得反向合并入 `v6-service`。
- `v6.8.0-alpha` 是 Framework Core Foundation Baseline，`v6.9.0-alpha` 是 Agent Workbench Single Instance 产品实例里程碑。
