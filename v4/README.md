# v4 归档区（只读）

本目录为 AI Agent Workbench **旧 UI 完整版**的归档备份，自 `v5.0.0-alpha` 起已停止维护。

## 状态

- **v4 线路已冻结**：不再接受新功能开发与 bug 修复。
- **只读留存**：保留原始代码、spec 与测试依赖，用于历史对照与回滚参考。
- **新开发主线**：`v5/` 目录，入口为根目录 `main.py`，打包配置为根目录 `AgentWorkbench.spec` / `AgentWorkbenchV5.spec`。

## 包含内容

- `v4/main_window.py`：旧 UI 主窗口（含完整业务实现）。
- `v4/widgets/`：旧 UI 控件库。
- `v4/legacy/`：更早版本 UI 组件备份。
- `v4/repository.py`、`v4/orchestrator.py`、`v4/worker_manager.py` 等：旧后端骨架。

## 注意

请勿在 v4 目录内继续修改或提交新功能。所有后续迭代请在 `v5/` 目录内进行，并同步更新 `docs/README.md`、`docs/PROJECT_BLUEPRINT.md`、`docs/CHANGELOG.md`。
