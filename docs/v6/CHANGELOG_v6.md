# V6 变更日志

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
