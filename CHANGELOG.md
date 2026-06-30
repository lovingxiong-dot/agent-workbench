# Changelog

## v4.0.7-alpha (2026-07-01) — 标题栏三键 + execute 步骤条

### feat/ui
- SimpleChatArea 标题栏从 QLabel 升级为 HeaderToolbar（搜索/更多/展开三键）
- 搜索键（🔍 Ctrl+F）弹出搜索条，实时高亮跳转
- 更多键（⋯）预留上下文菜单接口
- 展开键（⇱ Ctrl+B）联动 MainWindow.toggle_panels() 收起/展开左面板
- ui_renderer.py 新增 _parse_execute_steps 方法，execute 阶段自动解析步骤条（done/running/pending/fail）

### docs
- docs/ui/ 归档 6 张 SVG + 2 篇 UI spec（ui-fold-design / ui-header-buttons）

## v4.0.6-alpha (2026-07-01) — 补齐目录标准化遗漏

### fix/build
- `AgentWorkbench.spec` 的 `datas` 加入 `assets/app.ico`，打包后图标资源可正常读取
- `services/project_service.py` 改用 `_get_app_root()` 定位 `storage/activities.json`，避免 exe 在 CWD 创建 storage
