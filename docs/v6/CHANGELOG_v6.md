# V6 变更日志

## v6.0.0-alpha (2026-07-07) — 项目启动与架构规格
- 建立 V6 独立目录 `v6/`，与 V5 完全隔离。
- 编写 `PROJECT_BLUEPRINT_v6.md`、`SPEC.md`、`ROADMAP.md`。
- 明确分层架构：MainWindow → UIController → Manager → AgentRuntime → Engines。
- 确立专业 Agent 协作流程：UI Agent / Runtime Agent / Review Agent。
- 确立每阶段 Review + Smoke + Git 存档的验收标准。
