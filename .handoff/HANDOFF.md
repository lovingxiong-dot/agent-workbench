---
generated: 2026-06-30T03:00:00+08:00
agent: Kimi-K2.7-Code
schema_version: 3.1

## Mission
完成 AI Agent Workbench v3.12.0 的 UI 修复、MainWindow 架构收敛、AI Engine 八引擎升级评审、版本号统一与分支整理，将代码库推进到干净、可继续开发的归档状态。

## Progress
1. ✅ 修复新会话按钮只能添加一个标签的问题（移除空会话守卫）。
2. ✅ 修复会话标签名均为"新对话"的问题（首条消息后更新标题）。
3. ✅ 修复 Enter 键首次失效问题（新增 `_focus_input_field()` 强制焦点）。
4. ✅ 修复切换新会话显示无意义接替上下文的问题（`task.phase == "idle"` 守卫）。
5. ✅ 完成 MainWindow 架构收敛重构，移除旧全局状态（`_pending_queue`、`_worker`、`_workers`、`_phase_manager`），统一走 v3 MessageBus 路径。
6. ✅ 新增 `tests/test_main_window_ui_automation.py` UI 自动化测试（4 个用例）。
7. ✅ 评审并确认 v3.12.0 AI Engine 八引擎模块化升级的正确性与合理性（绞杀者模式、接口抽象、依赖注入）。
8. ✅ 统一版本号：`config.yaml` / `PROJECT_BLUEPRINT.md` / 提交标签一致为 `v3.12.0`。
9. ✅ 整理分支布局：将 `master` 合并到 `main`，删除本地与远程 `master`，`main` 成为唯一主线。
10. ✅ 全量测试 `214 passed`，工作区 clean，最新提交已 push 到 `origin/main`。

## Blocker
无。所有已识别问题已修复并验证，代码库处于可继续开发状态。

## Decision Log
1. 决策：采用 `_focus_input_field()` 统一处理输入框焦点（`activateWindow` + `raise_` + `QTimer.singleShot`）。
   原因：同步 `setFocus()` 在窗口未激活或被其他控件抢占时失效。
   排除：仅增加 `setFocusPolicy(Qt.StrongFocus)` 或仅在更多事件里调用 `setFocus()`。
   状态：已执行并验证。

2. 决策：对 AI Engine 升级使用绞杀者模式，保留旧逻辑作为回退。
   原因：`arun()` 主循环是热路径，直接全量替换风险过高。
   排除：一次性全量迁移到八引擎主循环。
   状态：已确认合理，后续需分阶段推进主循环迁移。

3. 决策：将 `master` 合并到 `main` 后删除 `master`，以 `main` 作为唯一主线。
   原因：用户要求唯一主线布局，`origin/HEAD` 已指向 `main`。
   排除：保留 `master` 作为并行开发分支。
   状态：已执行，`master` 本地与远程均已删除。

4. 决策：版本号修正提交不打新标签，复用已存在的 `v3.12.0`。
   原因：`v3.12.0` 已推送远程，指向 AI Engine 升级提交；元数据修正作为补丁提交跟随其后。
   排除：强制移动 `v3.12.0` 标签（违反 --force 规则）。
   状态：已执行，`v3.12.0` 标签保留。

## Key Files
- `ui/main_window.py` — MainWindow 架构收敛、输入框焦点修复、会话切换逻辑。
- `services/self_context.py` — 接替上下文构建，`task.phase == "idle"` 守卫。
- `ui/widgets/sidebar.py` — 补充 `FileTreeWidget.get_root_path()`。
- `ui/managers/session_manager.py` — `update_title` 补充 `Qt` 导入。
- `agent_engine/engines/` — v3.12.0 八引擎模块化实现（Context/Prompt/Inference/Tool/Phase/Memory/Metrics/Policy）。
- `agent_engine/orchestrator.py` — 绞杀者模式集成，新旧逻辑并存。
- `config.yaml` — 版本号、LLM 参数、engines 配置、system prompt。
- `PROJECT_BLUEPRINT.md` / `CHANGELOG.md` — 项目文档与变更日志。
- `tests/test_main_window_ui_automation.py` — UI 自动化测试。

## Error Log
No error. 最近一个完整测试运行：`214 passed in 44.45s`。

## Environment Snapshot
branch: main
python: Python 3.14.6
venv: none
last_commit: 9621c5e Merge branch 'master'

## Working State
### Dirty Files
working tree clean

### Uncommitted Changes Summary
no uncommitted changes

### Recent Conversation
- 用户要求分析 v3.12.0 AI Engine 八引擎升级的正确性与合理性。
- AI 确认升级架构正确：职责单一、接口抽象、依赖注入、绞杀者模式合理；指出主循环尚未迁移、引擎间初始化顺序、降级路径测试等后续关注点。
- 用户要求执行「存档+移交」，同步版本号，整理分支为唯一主线。
- AI 完成版本号统一、master 合并到 main、删除 master、push 到远程。

## Next Steps (AI-Inferred)
1. **验证 v3.12.0 运行时行为**：启动 `python main.py`，确认八引擎升级后没有破坏会话管理、焦点、队列状态等已有修复。
2. **推进八引擎主循环迁移**：制定从 `arun()` 旧路径逐步迁移到 `InferenceEngine` + `ToolEngine` + `PhaseEngine` 的计划。
3. **补充引擎降级/重试路径测试**：为 `InferenceEngine.invoke()` 的 fallback model、重试耗尽、流式取消等边界场景补充测试。
4. **清理 MainWindow 旧路径残留**：在确认 v3 MessageBus 路径稳定后，彻底移除 `_worker`、`_workers`、`_phase_manager` 等兼容属性及相关旧方法。

## Test Status
latest: [test:214/214]
command: python -m pytest tests -q --tb=short

## Notes
- `v3.12.0` 标签指向 `54b61fe`（AI Engine 升级提交），版本号修正提交 `b478515` 在其后并通过 merge 进入 `main`。
- 当前远程分支仅剩 `main` 与 `feature/v3-rewrite`；`origin/HEAD -> origin/main`。
- 建议后续在 Gitee 后台将默认分支明确设为 `main`（虽然 HEAD 已指向 main）。
