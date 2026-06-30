# Changelog

## v4.0.6-alpha (2026-07-01) — 补齐目录标准化遗漏

### fix/build
- `AgentWorkbench.spec` 的 `datas` 加入 `assets/app.ico`，打包后图标资源可正常读取
- `services/project_service.py` 改用 `_get_app_root()` 定位 `storage/activities.json`，避免 exe 在 CWD 创建 storage
