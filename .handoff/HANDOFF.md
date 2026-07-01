---
generated: 2026-07-01T19:30:00+08:00
agent: Trae-CN
schema_version: 3.1

## Mission
将 agent_workbench 的 PySide6 UI 模板（ui_template.py）按 SVG 设计稿精确还原，实现全局自适应拖拽、主题切换、图标 SVG 化。

## Progress
- 左栏：功能/会话 Tab 按钮恢复 SVG 设计稿的 rx=6 圆角背景框（#007acc 选中态 / btn_bg 未选中态）
- 左栏：功能/会话 Tab 主题切换时同步刷新背景+文字+字重
- 聊天区：ChatScene 支持 set_width() 动态调整内容宽度
- 聊天区：折叠/展开右侧面板时内容自动延伸/收缩
- 输入区：输入框与聊天区之间添加 _ResizeHandle 可拖拽分隔条（4px，50~300px 范围）
- 中部/右侧分割线：添加 80ms 防抖 QTimer，拖动停止后才重建内容，避免撕裂
- 图标：搜索/更多/还原/折叠/Enter 按钮已 SVG 化
- 字体：恢复 Segoe UI/Cascadia Code point-size 渲染，移除中文字体回退

## Blocker
symptom: 窗口边缘 resize（上下/右/右下角拖拽缩放窗口大小）无法生效
failed_attempts:
  1. QSplitter handleWidth=1 → 视觉上可选中但无法拖拽（1px 交互区域太窄，鼠标命中率极低）
  2. QSplitter handleWidth=3 → 可拖拽但用户要求回到原始参数 handleWidth=1
  3. MainWindow.mousePressEvent + _edge_at → 无效。根本原因：MainWindow 的 mouseMoveEvent 只在其自身未被子控件覆盖的区域触发，而窗口边缘（右/下）被 RightPanel/ChatArea 等子控件完全遮挡，事件从不到达 MainWindow
  4. QApplication.installEventFilter + eventFilter 全局捕获 → 语法通过但用户要求回退（后续未测试）

## Decision Log
1. 决策：聊天区内容宽度改为 ChatScene 类属性而非布局驱动
   排除：用 QHBoxLayout stretch 自动扩展 — QGraphicsScene 的坐标系不支持 layout，必须显式设置宽度
   状态：已执行，验证通过（折叠面板后内容正确延伸）

2. 决策：输入区保持 SVG 叠加风格（按钮在输入框内部）而非 layout 化
   排除：QHBoxLayout 将按钮放在输入框外面 — 与设计稿不一致
   状态：已执行

3. 决策：防抖用 QTimer.setSingleShot(True) + 80ms 间隔
   排除：手动在 resizeEvent 中节流 — QTimer 更可靠，不丢最后的 resize 事件
   状态：已执行

4. 决策：_toggle_right_panel 直接调 _rebuild_content()，不走防抖
   排除：统一用防抖 — 用户主动折叠/展开应即时生效
   状态：已执行

5. 决策：窗口边缘 resize 回退，暂不实现
   排除：eventFilter 方案 — 用户要求回退，且全局事件过滤器有性能/维护隐患
   状态：搁置

## Key Files
- `ui_template.py` — 主 UI 模板，~2100 行，包含三栏布局 + 主题系统 + 所有自定义控件
- `.reference/agent-workbench-ui/ui-full-dark.svg` — 深色主题设计稿 1024×720
- `.reference/agent-workbench-ui/ui-full-light.svg` — 浅色主题设计稿

## Error Log
```
Error calling Python override of QGraphicsItem::boundingRect():
  File "ui_template.py", line 1006, in boundingRect
KeyboardInterrupt
```
原因：进程被 Ctrl+C 中断时，Qt 正在重绘 QGraphicsItem，boundingRect 被调用但场景已被销毁。

## Environment Snapshot
branch: ui-template
python: 3.14.6
venv: none
last_commit: cd93b14 style(ui): icon SVGs + tab transparency + font restore + dynamic chat width

## Working State
### Dirty Files
 M ui_template.py

### Uncommitted Changes Summary
 ui_template.py | 106 ++++++++++++++++++++++++++++++++++++----------
 1 file changed, 88 insertions(+), 18 deletions(-)
未提交内容：Tab 背景框恢复 + _ResizeHandle 输入区拖拽 + 防抖 QTimer

### Recent Conversation
- 用户要求恢复功能/会话 Tab 的背景框（之前迭代误删）
- 用户要求添加输入区上边框可拖拽（调整输入区高度）和工作区分割线平滑移动+防抖
- 终端启动命令每次需 AI 直接执行而非给文本

## Next Steps (AI-Inferred)
1. 提交当前未提交改动（Tab 背景框 + _ResizeHandle + 防抖）
2. 存档打标签
3. 支线 push
4. 窗口边缘 resize（下个迭代）：考虑用原生 Windows 消息钩子或 setSizeGripEnabled(True) 替代 eventFilter

## Test Status
latest: [test:py_compile] — 语法编译通过
command: python -m py_compile ui_template.py

## Notes
- 窗口边缘 resize 的可靠方案可能是启用 SizeGrip（右下角小三角）作为最低可行方案
- QSplitter 分割线拖拽可考虑用 CSS margin 扩展 hit area 而非增大 handleWidth
