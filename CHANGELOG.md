# Changelog

## v5.0.2-alpha (2026-07-06) — P3 UIRenderer 与新 UI 控件桥接完成

### feat/bridge/ui
- `ChatArea` 实现真实消息渲染：用户气泡、系统卡片、AI 文本块、思考折叠块、工具执行折叠块
- `ChatArea` 支持流式输出：`append_chunk` 累积、`finalize_stream` 收尾
- `ChatArea` 新增标题栏状态标签：显示“回答中...”与阶段/任务数
- `ChatArea` 新增任务确认条（确认/取消按钮），发出 `confirmation_clicked(bool)` 信号
- `LeftPanel` 实现 `refresh(sessions)`：按 `project_path` 分组重建会话列表
- `LeftPanel` 实现 `set_active_session(session_id)` 与 `update_badge(session_id, phase)`
- 修复 `SessionGroup` 右键动作信号转发，重命名/删除菜单可正确触发

### test
- `python -m py_compile v4/main_window.py` 通过
- `pytest tests/test_v4_gui_smoke.py -v` 4/4 全绿

## v5.0.1-alpha (2026-07-05) — 备份 v4 旧 UI 组件并标记 v5-dev 线路

### chore/backup
- 将 v4 旧 UI 组件（`conversation_list.py`、`input_area.py`、`right_panel.py`、`chat_scene.py`、`chat_items.py`、`icons.py`、`main_window_legacy.py`）备份至 `v4/legacy/`
- 原始组件保留在 `v4/` 根目录，待 P10 阶段确认无引用后清理
- `PROJECT_BLUEPRINT.md` 更新目录结构与版本标记，明确 v5-dev 为独立新 UI 线路

## v5.0.0-alpha (2026-07-05) — v5-dev 线路起点：新 UI 注入后端核心

### feat/refactor
- 从 `v4-refactor` 切出独立 `v5-dev` 线路，与 v3/v4 并行开发
- 将新三栏 UI 模板迁移至 `v4/main_window.py`，注入后端核心组件：`ConfigService`、`SessionRepository`、`MessageBus`、八引擎、`WorkerManager`、`SessionOrchestrator`、`UIRenderer`
- 保留核心基座不变：引擎层、v4 事件总线、异步 Worker 调度、会话编排
- 窗口基础参数调整：默认 1400×900、最小 1200、标题从配置动态读取

### test
- `python -m py_compile v4/main_window.py` 通过

## v4.0.8-alpha (2026-07-01) — 最终发布版三栏 UI 全量重制

### feat/ui
- 主窗口从两栏升级为 QSplitter 三栏布局：左栏 220px + 中栏伸缩 + 右栏 400px
- 新增 `v4/input_area.py`：底部输入区含圆形发送按钮、技能按钮、mode/model 标签，Enter 发送 / Shift+Enter 换行
- 新增 `v4/right_panel.py`：右栏四标签页（v4 架构 / 终端 / 文件编辑器 / 浏览器），支持命令执行、文件读取、网页浏览
- 重构 `v4/conversation_list.py`：左栏「功能/会话」Tab、搜索/+新会话/更多工具行、按项目路径分组的折叠会话列表
- 扩展 `v4/events.py`：新增 `UIOpenFileEvent`、`UIUpdateTerminalEvent`、`UIRightPanelTabEvent`、`UIAnalyzeProjectEvent`、`UILoadUrlEvent`、`UIUpdateFileReaderEvent` 等右栏交互事件
- 扩展主题令牌：新增 `card_analyze_*`、`card_execute_*`、`card_verify_*`、`card_archive_*`、`card_tool_*`、`card_output_*` 等卡片配色

### fix/ui
- `v4/ui_renderer.py` 接收 `right_panel` 参数并统一处理右栏事件，移除硬编码颜色
- `v4/conversation_list.py` 修复取消置顶后会话未按更新时间倒序排列的问题
- 新增/更新测试：`test_v4_input_area.py`、`test_v4_right_panel.py`、`test_v4_gui_smoke.py`、`test_v4_integration.py`，全量 204 项通过

## v4.0.7-alpha (2026-07-01) — 标题栏三键 + execute 步骤条

### feat/ui
- SimpleChatArea 标题栏从 QLabel 升级为 HeaderToolbar（搜索/更多/展开三键）
- 搜索键（Ctrl+F）弹出搜索条，在当前会话文本中高亮跳转
- 更多键弹出上下文菜单（导出当前会话 / 复制会话内容 / 打开设置）
- 展开键（Ctrl+B）联动 MainWindow.toggle_panels() 收起/展开左面板
- ui_renderer.py 新增 _parse_execute_steps 方法，execute 阶段自动解析步骤条（done/running/pending/fail）

### fix/ui
- 标题栏三键图标从 Unicode 字符替换为 SVG path 矢量图标，避免字体缺失导致显示异常
- AgentWorkbench.spec 增加 `PySide6.QtSvg` hiddenimports，确保打包后 SVG 图标正常渲染
- execute 阶段步骤分隔线颜色改用主题变量，适配深色/浅色主题

### docs
- docs/ui/ 归档 6 张 SVG + 2 篇 UI spec（ui-fold-design / ui-header-buttons）

## v4.0.6-alpha (2026-07-01) — 补齐目录标准化遗漏

### fix/build
- `AgentWorkbench.spec` 的 `datas` 加入 `assets/app.ico`，打包后图标资源可正常读取
- `services/project_service.py` 改用 `_get_app_root()` 定位 `storage/activities.json`，避免 exe 在 CWD 创建 storage
