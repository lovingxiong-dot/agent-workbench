# v4 归档区（只读）

本目录为 AI Agent Workbench **旧 UI 完整版**的归档备份，自 `v5.0.0-alpha` 起已停止维护。

## 状态

- **v4 线路已冻结**：Git 分支 `v4-refactor` 最终归档标签为 `v4.0.11-alpha`，不再接受新功能开发与 bug 修复。
- **只读留存**：保留原始代码、spec 与测试依赖，用于历史对照与回滚参考。
- **独立打包入口**：本目录提供 `v4/v4_main.py` + `v4/AgentWorkbenchV4.spec` + `v4/scripts/rebuild_v4.ps1`，可生成 `dist/AgentWorkbenchV4/` 并创建桌面快捷方式「AI Agent Workbench V4」。
- **新开发主线**：`v5/` 目录，入口为根目录 `main.py`，打包配置为根目录 `AgentWorkbenchV5.spec`。

## 包含内容

- `v4/main_window.py`：旧 UI 主窗口（含完整业务实现）。
- `v4/widgets/`：旧 UI 控件库。
- `v4/legacy/`：更早版本 UI 组件备份。
- `v4/repository.py`、`v4/orchestrator.py`、`v4/worker_manager.py` 等：旧后端骨架。

## 注意

请勿在 v4 目录内继续修改或提交新功能。所有后续迭代请在 `v5/` 目录内进行，并同步更新 `docs/README.md`、`docs/PROJECT_BLUEPRINT.md`、`docs/CHANGELOG.md`。
