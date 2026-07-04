---
generated: 2026-07-04T21:50:00+08:00
agent: WorkBuddy
schema_version: 3.1
---

## Mission
将 agent_workbench 的 PySide6 UI 模板（experiments/ui_template.py）按 SVG 设计稿精确还原，实现 Apple 风格全局自适应。

## Progress v0.5-alpha

### 已完成
- **InvisibleResizeHandle 补丁注入**：QSplitter handleWidth=1，4px 透明叠加热区
- **EdgeResizeWidget 窗口边缘 resize**：8 个边角手柄，`startSystemResize()` 驱动，替代失效的 nativeEvent
- **HeaderBar 左折叠按钮**：标题栏最左侧，对称于右侧折叠键
- **HeaderBar 双击最大化**：`mouseDoubleClickEvent` → `_toggle_maximize`
- **HeaderBar 窗口拖动**：从 MainWindow 父控件移至 HeaderBar 子控件
- **_toggle_left_panel**：隐藏/显示 LeftPanel，中栏自动延伸/收缩
- **InputArea 响应式**：`QHBoxLayout` + stretch=1 替代 `setGeometry(0,0,362,56)`
- **QSplitter 拖拽联动**：`splitterMoved` → `_on_splitter_moved` → 聊天内容重绘
- **InputArea 最小高度保护**：`setMinimumHeight(104)`，标签行 + 发送按钮不压缩
- **发送按钮位置**：移到输入框外右下角，与标签行合并为 bottom_row
- **SessionItem 选中框**：自定义 `paintEvent` + `QPainter.drawRoundedRect`，单个圆角矩形统一包围

### 已清理
- 移除失效 nativeEvent+WM_NCHITTEST（FramelessWindowHint → 无 WS_THICKFRAME）
- 移除 QSizeGrip、ctypes import、_edge_mode、BORDER_WIDTH

## Blocker
（无阻塞项。窗口边缘 resize 已解决。）

## Reflection

### 问题 1：左侧选中框（SessionItem）

**演进过程**：
1. **QSS 类选择器** `SessionItem { background-color: ...; border: ...; }` — PySide6 类名解析不稳定，有时不生效
2. **去选择器直设样式** `background-color: {bg}; border: ...;` — 生效但 `border-radius` 不裁剪子 QLabel，导致外观像"三个分开的文本框"而非"一张统一的圆角卡片"
3. **最终方案** `paintEvent` + `QPainter.drawRoundedRect` — 用 QPainter 直接绘制填充 + 边框，子 QLabel 设透明背景。选中/悬停/普通三态均正确，单一圆角矩形包裹全部内容。

**反思**：QSS 的 `border-radius` 在 PySide6 中仅影响 widget 自身的边框圆角，不裁剪子 widget。对于需要统一圆角卡片的场景，`paintEvent` 是更可靠的选择。

### 问题 2：字体与 SVG 效果图的差异

**根因**：
- SVG 设计稿使用 CSS 像素：`font-size="12"` → 12px
- PySide6 `QFont("Segoe UI", 12)` 将 `12` 解释为 point size（12pt）
- 在 96 DPI 下：12pt ≈ 16px，偏移约 33%

**已尝试的修复**：
- `QFont("Segoe UI"); f.setPixelSize(12)` — 字体精确对齐 12px，但与用户预期的效果图缩小约 25%
- 用户倾向于保留 `QFont(family, pointSize)` 的呈现效果（更易阅读），已回退

**差异量化**：

| 设计字号 | SVG (px) | 代码 (pt) | 实际渲染 (~px) | 偏差 |
|----------|----------|-----------|----------------|------|
| 12 | 12px | 12pt | ~16px | +33% |
| 11 | 11px | 11pt | ~15px | +36% |
| 10 | 10px | 10pt | ~13px | +33% |
| 9  | 9px  | 9pt  | ~12px | +33% |

**潜在方案**（未执行）：
- 使用 DPI 缩放因子 `pixelSize = int(pointSize * 0.75)` 近似映射
- 用 `QFontMetrics` 测量实际渲染尺寸，动态校准
- 保持 point size 不变，确认设计验收标准后再决定

## Decision Log

| # | 决策 | 排除方案 | 日期 |
|---|------|----------|------|
| 6 | EdgeResizeWidget + startSystemResize | nativeEvent/WM_NCHITTEST | 2026-07-04 |
| 7 | HeaderBar 窗口拖动 | MainWindow 父控件 | 2026-07-04 |
| 8 | paintEvent 绘制选中框 | QSS class-selector / direct style | 2026-07-04 |
| 9 | QFont pointSize（恢复） | setPixelSize | 2026-07-04 |

## Key Files
- `experiments/ui_template.py` — 主 UI 模板，~2300 行
- `experiments/ui_template_with_handle.py` — 含 InvisibleResizeHandle 补丁的分支版本
- `.reference/agent-workbench-ui/ui-full-dark.svg` — 深色设计稿
- `.reference/agent-workbench-ui/ui-full-light.svg` — 浅色设计稿
- `.reference/agent-workbench-ui/specs/ui-header-buttons.md` — 三键施工规范

## Environment Snapshot
```
branch: ui-template
python: 3.14.6
last_commit: ee3c6d6 feat(ui): ... v0.5-alpha
tag: v0.5-alpha
HEAD == origin/ui-template（已同步）
```

## Working State
### Dirty Files
- `.workbuddy/memory/2026-07-04.md`（工作日志，可忽略）

## Next Steps (AI-Inferred)
1. 字体对齐：与用户确认最终验收标准（point size vs pixel size），必要时统一调整
2. ChatArea 聊天气泡/面板响应式：随窗口宽度自动适配（`_rebuild_content` 已就绪）
3. 右栏真实数据接入：替换 Demo 硬编码为实际文件列表、终端输出等
4. 合并回主分支：ui-template 验证通过后可考虑 merge 到 main/ v4-refactor

## Test Status
latest: [test:py_compile] — 语法编译通过
command: python -m py_compile experiments/ui_template.py
