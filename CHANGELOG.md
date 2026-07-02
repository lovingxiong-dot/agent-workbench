# Changelog

## v0.4-alpha (2026-07-02) — UI 模板图标 SVG 化 + 标签背景框恢复 + 输入区拖拽 + 防抖 + 交接

### feat/ui
- 左栏功能/会话 Tab 按钮恢复 SVG 设计稿 rx=6 圆角背景框（accent 选中态 / btn_bg 未选中态）
- 聊天区与输入区之间添加 _ResizeHandle 可拖拽分隔条（4px，50~300px 范围）
- 中间/右侧分割线添加 80ms 防抖 QTimer，拖动停止后才重建内容，避免撕裂
- 标题栏搜索/更多/还原/折叠图标 SVG 化
- Enter 发送按钮 SVG 化（圆形背景 + 箭头）

### fix/ui
- Tab 按钮主题切换时同步刷新背景色 + 文字色 + 字重
- 字体恢复 Segoe UI / Cascadia Code point-size 渲染
- 窗口边缘 resize 分析：确认根因为 MainWindow.mouseEvent 被子控件遮挡，eventFilter/QSplitter 方案均不可行，暂搁置

### docs
- 新增 .handoff/HANDOFF.md 交接文档（窗口边缘 resize 失败分析 + 决策日志）
- 新增 .handoff/CONVERSATION_LOG.md 完整会话记录
- PROJECT_BLUEPRINT.md 同步更新至 v0.4-alpha

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
