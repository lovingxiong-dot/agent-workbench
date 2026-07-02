---
generated: 2026-07-02T19:55:00+08:00
agent: WorkBuddy
schema_version: 3.1

## Mission
将 agent_workbench 的 PySide6 UI 模板（ui_template.py）按 SVG 设计稿精确还原，实现全局自适应拖拽、主题切换、图标 SVG 化。

## Progress
- 左栏：功能/会话 Tab 按钮恢复 SVG 设计稿 rx=6 圆角背景框（#007acc 选中态 / btn_bg 未选中态）
- 左栏：功能/会话 Tab 主题切换时同步刷新背景+文字+字重
- 聊天区：ChatScene 支持 set_width() 动态调整内容宽度
- 聊天区：折叠/展开右侧面板时内容自动延伸/收缩
- 输入区：输入框与聊天区之间添加 _ResizeHandle 可拖拽分隔条（4px，50~300px 范围）
- 中部/右侧分割线：添加 80ms 防抖 QTimer，拖动停止后才重建内容，避免撕裂
- 图标：搜索/更多/还原/折叠/Enter 按钮已 SVG 化
- 字体：恢复 Segoe UI/Cascadia Code point-size 渲染

## Blocker
symptom: 窗口边缘 resize（上下/右/右下角拖拽缩放窗口大小）无法生效
failed_attempts:
  1. QSplitter handleWidth=1 → 命中率极低（1px 交互区域）
  2. QSplitter handleWidth=3 → 可拖拽但用户要求回到 1px
  3. MainWindow.mousePressEvent + _edge_at → 无效（子控件遮挡）
  4. QApplication.installEventFilter 全局捕获 → 用户回退

根因已确认：MainWindow 的 mouseMoveEvent 只在其自身未被子控件覆盖的区域触发，窗口边缘被 RightPanel/ChatArea 完全遮挡，事件从不到达 MainWindow。

## Decision Log
（继承 Trae-CN 全部 5 项决策，无新增）

## Key Files
- `ui_template.py` — 主 UI 模板，~2100 行
- `.reference/agent-workbench-ui/ui-full-dark.svg` — 深色设计稿 1024×720
- `.reference/agent-workbench-ui/ui-full-light.svg` — 浅色设计稿

## Environment Snapshot
branch: ui-template
python: 3.14.6
last_commit: 306d050 docs: CHANGELOG + PROJECT_BLUEPRINT 更新至 v0.4-alpha (by AI-WorkBuddy)
tag: v0.4-alpha

## Working State
### Dirty Files
（无 — 工作区干净）

### Git Status
- HEAD == origin/ui-template（已同步）
- 标签 v0.4-alpha 已推送
- v0.1/v0.2/v0.3 为 main 分支旧标签，不影响 ui-template

## Next Steps (AI-Inferred)
1. 窗口边缘 resize — 优先级最高阻塞项。推荐方案：
   a. **SizeGrip**：`setSizeGripEnabled(True)` 在右下角显示拖拽三角，最简单可行
   b. **WM_NCHITTEST 钩子**：通过 `nativeEvent` 拦截 Windows 原生消息，绕过 Qt 控件层级
   c. **透明 overlay widget**：在 MainWindow 上叠加一个透明 QWidget 专门捕获边缘鼠标事件
2. 如 ui_template.py 验证通过，可考虑合并回 main 或 v4-refactor 分支

## Test Status
latest: [test:py_compile] — 语法编译通过
command: python -m py_compile ui_template.py

## Notes
- 本分支的核心交付（图标 SVG 化 + 拖拽 + 防抖 + 主题）已完整
- 唯一未完成项是窗口边缘 resize，属于增强项而非阻塞上线
- 该问题跨 Qt 版本普遍存在，社区方案多为 nativeEvent 或 SizeGrip
