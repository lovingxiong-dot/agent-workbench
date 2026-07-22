# v6/UI Foundation Contract

> **Status**: FROZEN FOUNDATION — Phase 2-B.1
> **Freeze Date**: 2026-07-22
> **Scope**: `v6/ui/` (22 files, ~2,800+ lines)
> **Role**: Canonical Presentation Foundation for Agent Workbench OS
> **Priority**: 最高 — 高于 Spec、高于 Task List、高于 CHANGELOG

---

## Origin

`v6/ui` originates from the **Pure UI branch** (Git tag: `v6-ui-complete`, commit `8f7b049`).
Design reference: `experiments/ui_template.py` (Git tag `v0.6-alpha`).

It is **independent** from:
- The deprecated `v6-agent` branch (`UI → Controller → Agent Runtime → LLM`)
- The `agent_workbench/ui/workbench/` legacy validation UI
- Any Runtime-specific code

---

## Responsibility

`v6/ui` provides the **Presentation Foundation** — the visual and interaction baseline:

- **Visual System**: dual-theme color palette, fonts, SVG icons
- **Layout System**: three-panel QSplitter, collapse/expand control
- **Interaction Component System**: LeftPanel, ChatArea, RightPanel, InputArea, HeaderBar, FunctionPage
- **Theme System**: dark/light instant toggle
- **UX Specification**: spacing, border-radius, hover states, drag zones

`v6/ui` is **not** a UI component library. It is the **design baseline** against which all Renderers adapt.

---

## Architecture Role

```
             Runtime
                |
                v
       Interaction Boundary
                |
                v
       Presentation Renderer
                |
                v
             v6/ui          ← Presentation Foundation
                |
                v
             Qt
```

**Dependency direction**: only downward. Never upward.

---

## Forbidden Dependencies

`v6/ui` MUST NOT depend on:

- Runtime (`agent_workbench.runtime.*`)
- Agent (`agent_workbench.agent.*`)
- Model Provider (`agent_workbench.provider.*`)
- Session (`agent_workbench.session.*`)
- Tool Execution (`agent_workbench.tool.*`)
- Memory System (`agent_workbench.memory.*`)
- WorkbenchUIController (`agent_workbench.ui.*`)
- Any `agent_workbench/` package

**Verification**: `grep -r "from agent_workbench" v6/ui/` must return empty.

---

## Modification Policy

### Allowed Changes

- Visual refinement: colors, spacing, border-radius, font sizing, accessibility
- UI Capability API additions required by Presentation Contract
  - Example: `ChatArea.reset_workspace()` — exposes existing `ChatScene.clear_chat()` to ShellAdapter
  - Example: `ChatArea.add_capability_step(index, step)` — exposes `ChatScene.add_step()` to EventRenderer
  - Rule: expose existing capabilities, don't add Runtime concepts

### Forbidden Changes

- Runtime-driven UI redesign (e.g., "add a new widget for Agent status")
- Business logic inside widgets (e.g., "ChatArea decides which Agent to use")
- Runtime imports (e.g., `from agent_workbench.runtime import ...`)
- Changing layout, visual design, or component structure to accommodate Renderer needs
- Creating new widgets that don't belong to the Presentation Foundation
- Adding Runtime-concept methods (e.g., `update_agent()`, `update_model()`, `update_session()`)

### UI Capability vs Runtime Concept

```
Allowed (UI Capability):          Forbidden (Runtime Concept):
  append_user()                     update_agent()
  append_ai()                       update_model()
  stream_chunk()                    update_session()
  reset_workspace()                 show_agent_status()
  add_capability_step()             render_tool_call()
                                    refresh_memory()
```

UI Capability describes what the UI can do.
Runtime Concept belongs to the Presentation Adapter, not v6/ui.

---

## Component Inventory (Frozen)

| Component | File | Lines | Purpose |
|-----------|------|-------|---------|
| `base.py` | `v6/ui/base.py` | 357 | ThemeManager, 双主题色板, 字体, SVG图标, InvisibleResizeHandle, EdgeResizeWidget |
| `LeftPanel` | `v6/ui/left_panel.py` | 168 | 会话分组 + 功能页 + 文件 + 搜索 + 主题切换 |
| `ChatArea` | `v6/ui/chat_area.py` | 286 | HeaderBar + ChatScene + SearchBar + InputArea + AnalyzeButton |
| `RightPanel` | `v6/ui/right_panel.py` | 238 | 文件/终端/浏览器 标签页 + 窗口控制 |
| `InputArea` | `v6/ui/input_area.py` | 162 | 技能按钮 + 模式/模型标签 + 文本框 + 发送/停止 |
| `HeaderBar` | `v6/ui/header_bar.py` | 141 | 双行标题 + 折叠/搜索/更多 + 拖拽 + 双击最大化 |
| `FunctionPage` | `v6/ui/function_page.py` | 165 | 工具/MCP/技能/自动化 4 分类 |
| `ChatScene` | `v6/ui/chat_scene.py` | 144 | QGraphicsScene 聊天消息渲染引擎 |
| `ChatItems` | `v6/ui/chat_items.py` | 277 | 8 种 QGraphicsWidget 子类（UserBubble, TextItem, ToolEntry, etc.） |
| `SessionGroup` | `v6/ui/session_group.py` | 134 | 可折叠会话分组 |
| `SessionItem` | `v6/ui/session_item.py` | 131 | 会话列表项（标题/预览/时间/active/hover） |
| `TabButton` | `v6/ui/tab_button.py` | 93 | Tab 切换按钮（左栏/右栏两种模式） |
| `WindowFrame` | `v6/ui/window_frame.py` | 265 | AppleMenu, FramelessWindowHelper, 圆角遮罩 |
| `MoreDropdown` | `v6/ui/more_dropdown.py` | 59 | 标题栏「更多」下拉菜单 |
| `AppleMenu` | `v6/ui/apple_menu.py` | 8 | 重导出 |
| `RecentFiles` | `v6/ui/recent_files.py` | 85 | 最近文件列表 |
| `TerminalWidget` | `v6/ui/terminal_widget.py` | 85 | 终端面板 |
| `FileReaderWidget` | `v6/ui/file_reader_widget.py` | 73 | 文件阅读器 |
| `BrowserWidget` | `v6/ui/browser_widget.py` | 81 | 浏览器占位 |
| `SettingsDialog` | `v6/ui/settings_dialog.py` | — | 设置对话框 |
| `SettingsPanel` | `v6/ui/settings_panel.py` | — | 设置面板 |
| `__init__.py` | `v6/ui/__init__.py` | 17 | 模块导出 |

**Total**: 22 files, ~2,800+ lines

---

## Lineage & Distinction

`v6/ui` is the **Pure UI Foundation** — an independent Presentation Design System.
It does **not** inherit from the deprecated `v6-agent` application architecture.

| Artifact | Role | Status |
|----------|------|--------|
| `v6/ui/` (22 files) | Pure UI Foundation — Visual System, Layout, Interaction Components | **ACTIVE** — Phase 2-B Renderer target |
| `agent_workbench/ui/workbench/` (32 files) | Legacy architecture validation UI | **PRESERVED** — not the main UI |
| `v6-agent` branch | Deprecated application-centric architecture | **ARCHIVED** — not used in Phase 2-B |

The `v6-agent` architecture was:

```
UI → Controller → Agent Runtime → LLM
```

This was **application-centric**: UI directly bound to Agent.

The current architecture is:

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

This is **Runtime-first, Presentation-agnostic**: UI is a Shell Renderer, not an application.

`v6/ui` was extracted from the early Workbench as an independent Pure UI Foundation.
Phase 2-B does not restore the old `v6-agent` path — it connects the existing
Pure UI Foundation to the new Runtime through the Renderer layer.

---

## Multi-Runtime Target

As a Presentation Foundation, `v6/ui` can serve as the Renderer target for any Runtime:

```
CENTRE Runtime → Renderer Adapter → v6/ui
OpenAI Runtime → Renderer Adapter → v6/ui
Claude Runtime  → Renderer Adapter → v6/ui
```

This is the meaning of **Presentation-agnostic**: the UI knows nothing about which Runtime produces the data.

---

## Validation

Any Renderer implementation must pass:

1. **Zero Runtime imports** in `v6/ui/`
2. **No layout changes** compared to `v6-ui-complete` tag (except allowed Public API additions)
3. **No visual design changes** — colors, spacing, fonts, radii preserved
4. **No component structure changes** — LeftPanel/ChatArea/RightPanel hierarchy preserved
5. **Dependency direction**: `v6/ui` imports nothing from `agent_workbench/`

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | 初始冻结。Phase 2-B.1 Presentation Foundation Freeze。 |
| v1.1 | 2026-07-22 | 新增 Lineage & Distinction、Multi-Runtime Target、UI Capability vs Runtime Concept 边界。 |