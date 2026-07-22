# Phase 2-D.0 — UI Migration Audit

> **Status**: GATE CHECK — 通过后方可进入 v6/ui Renderer Migration
> **Date**: 2026-07-22
> **Precedes**: v6/ui Renderer Migration (Phase 2-D.1)

---

## 1. UI Source Map

### 1.1 Legacy Workbench UI（旧 UI，当前 active）

| 文件 | 组件 | 来源 | 状态 |
|------|------|------|------|
| [ui/workbench/workbench.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/workbench.py) | Workbench 三栏布局 | 旧 Workbench | **待替换** |
| [ui/workbench/navigator.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/navigator.py) | 导航栏 | 旧 | **待替换** |
| [ui/workbench/command_bar.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/command_bar.py) | 命令栏 | 旧 | **待替换** |
| [ui/workbench/inspector.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/inspector.py) | 属性面板 | 旧 | **待替换** |
| [ui/workbench/status_bar.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/status_bar.py) | 状态栏 | 旧 | **待替换** |
| [ui/workbench/chat_workspace.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench/chat_workspace.py) | 聊天工作区 | 旧 | **待替换** |
| [ui/workbench_ui_controller.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/workbench_ui_controller.py) | UI Controller（God Object） | 旧 | **待替换** |
| [ui/main_window.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/ui/main_window.py) | 主窗口 | 旧 | **待替换** |
| 其余 24 文件 | Host/Provider/Trace/等 | 旧 | **待替换** |

**总计：32 文件，当前运行入口 `run_gui()`**

### 1.2 v6/ui Pure UI Foundation（新 UI，未激活）

| 文件 | 组件 | 来源 | 状态 |
|------|------|------|------|
| [v6/ui/chat_area.py](file:///e:/Development/workbench/agent_workbench/v6/ui/chat_area.py) | 聊天区域 | v6-ui-complete | **目标 Renderer** |
| [v6/ui/left_panel.py](file:///e:/Development/workbench/agent_workbench/v6/ui/left_panel.py) | 左侧面板 | v6-ui-complete | **目标 Renderer** |
| [v6/ui/right_panel.py](file:///e:/Development/workbench/agent_workbench/v6/ui/right_panel.py) | 右侧面板 | v6-ui-complete | **目标 Renderer** |
| [v6/ui/input_area.py](file:///e:/Development/workbench/agent_workbench/v6/ui/input_area.py) | 输入区域 | v6-ui-complete | **目标 Renderer** |
| [v6/ui/header_bar.py](file:///e:/Development/workbench/agent_workbench/v6/ui/header_bar.py) | 标题栏 | v6-ui-complete | **目标 Renderer** |
| [v6/ui/chat_scene.py](file:///e:/Development/workbench/agent_workbench/v6/ui/chat_scene.py) | 聊天场景 | v6-ui-complete | **目标 Renderer** |
| 其余 16 文件 | 辅助组件 | v6-ui-complete | **目标 Renderer** |

**总计：22 文件，当前仅在 `run_gui_v6()` 中创建但未接入 Runtime**

### 1.3 Presentation Renderers（桥接层）

| 文件 | 组件 | 来源 | 状态 |
|------|------|------|------|
| [v6_ui/event_renderer.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/presentation/renderers/v6_ui/event_renderer.py) | V6UIEventRenderer | Phase 2-B | **目标** |
| [v6_ui/shell_adapter.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/presentation/renderers/v6_ui/shell_adapter.py) | V6UIShellAdapter | Phase 2-B | **目标** |
| [cli_renderer.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/presentation/renderers/cli_renderer.py) | CLIRenderer | Phase 2-C.4 | Proof only |
| [registry.py](file:///e:/Development/workbench/agent_workbench/agent_workbench/presentation/renderers/registry.py) | RendererRegistry | Phase 2-C.3 | **目标** |

---

## 2. Dependency Graph

### 2.1 当前运行路径（旧架构）

```
app.py: run_gui()
    │
    ├── PySide6.QtWidgets
    │
    └── WorkbenchMainWindow
            │
            └── WorkbenchUIController (God Object)
                    │
                    ├── WorkbenchController        ← Runtime
                    ├── v6.runtime.adapter          ← 旧 v6-agent
                    ├── v6.runtime.context           ← 旧 v6-agent
                    ├── v6.runtime.event_bus          ← 旧 v6-agent
                    ├── v6.ui_controller              ← 旧 v6-agent
                    ├── PresentationPipeline          ← 静态调用
                    ├── model_module / conversation
                    └── ui/workbench/workbench.py
                            │
                            ├── v6.ui.base.C         ← 主题常量（唯一 v6/ui 引用）
                            └── PySide6 widgets
```

**违规点**：
| # | 违规 | 严重程度 |
|---|------|---------|
| 1 | `WorkbenchUIController` import `v6.runtime.*` | 高 — 旧 v6-agent 已废弃 |
| 2 | `WorkbenchUIController` import `v6.ui_controller` | 高 — 旧 v6-agent 已废弃 |
| 3 | `workbench.py` import `v6.ui.base.C` | 低 — 仅主题常量，但方向错误 |
| 4 | `WorkbenchUIController` 直接创建 `PresentationPipeline()` | 中 — 应通过 PresentationRuntime |

### 2.2 新架构路径（Phase 2-B 原型，`run_gui_v6`）

```
app.py: run_gui_v6()
    │
    ├── PySide6.QtWidgets
    ├── v6.ui (LeftPanel, ChatArea, RightPanel)     ← Pure UI Foundation
    ├── v6.layout_manager                            ← 布局管理
    │
    └── V6UIApplication
            │
            ├── WorkbenchController                  ← Runtime
            ├── V6UIEventRenderer                    ← Renderer
            ├── V6UIShellAdapter                     ← Shell Adapter
            └── PresentationPipeline                 ← 静态调用
```

**问题**：
| # | 问题 | 严重程度 |
|---|------|---------|
| 1 | `run_gui_v6()` 未在 `main()` 中处理 `--mode gui-v6` | 中 — 入口点未连接 |
| 2 | `V6UIApplication` 仍直接创建 `PresentationPipeline()` | 中 — 应使用 `PresentationRuntime` |
| 3 | `V6UIApplication` 未使用 `RendererRegistry` | 中 — 仍手动注册 Renderer |
| 4 | `V6UIApplication` 未使用 `PresentationRuntime` | 中 — 仍为 Phase 2-B 原型 |

### 2.3 目标架构路径（Phase 2-D 目标）

```
app.py: run_gui_v6()
    │
    ├── PySide6.QtWidgets
    ├── v6/ui (Pure UI Foundation)   ← 22 files, zero agent_workbench import
    │
    └── V6UIApplication (精简)
            │
            └── PresentationRuntime
                    │
                    ├── RendererRegistry
                    │       │
                    │       └── V6UIRenderer
                    │               │
                    │               ├── V6UIEventRenderer  → v6/ui public API
                    │               └── V6UIShellAdapter   → v6/ui public API
                    │
                    └── PresentationPipeline (owned)
```

### 2.4 依赖方向验证

```
✅ 合规：
  v6/ui → PySide6                     (Pure UI Foundation)
  v6/ui → v6.ui.*                     (内部依赖)
  V6UIEventRenderer → v6/ui ChatArea  (Renderer → UI public API)
  V6UIShellAdapter → v6/ui            (Shell Adapter → UI public API)
  PresentationRuntime → RendererProtocol (own protocol)
  RendererRegistry → RendererProtocol (own protocol)

❌ 违规（旧架构）：
  WorkbenchUIController → v6.runtime.*   (旧 v6-agent，已废弃)
  WorkbenchUIController → v6.ui_controller (旧 v6-agent，已废弃)

⚠️ 待修正：
  V6UIApplication → PresentationPipeline (应为 PresentationRuntime)
  run_gui_v6 → 未连接 main() 入口
```

---

## 3. Frozen Zone Rules

### 3.1 禁止修改

| Zone | Files | 原因 |
|------|-------|------|
| Runtime Kernel | `runtime/` 19 files | Frozen |
| v6/ui Foundation | `v6/ui/` 22 files | Pure UI Foundation，仅允许新增 Public API |
| Shell Contract | `presentation/shell/protocol.py` | Frozen |
| Shell Transformers | `presentation/shell/transformers/` | Frozen |
| Interaction Protocol | `presentation/protocols/` | Frozen (Phase 2-C.1) |

### 3.2 允许修改

| Zone | Files | 操作 |
|------|-------|------|
| Application | `application/v6_ui_application.py` | 适配 PresentationRuntime |
| Entry Point | `app.py` | 连接 `--mode gui-v6` |
| Renderer | `presentation/renderers/v6_ui/` | 适配 RendererRegistry |
| Presentation Runtime | `presentation/runtime.py` | 不修改 |

### 3.3 谨慎修改

| Zone | Files | 原因 |
|------|-------|------|
| v6/ui | `v6/ui/chat_area.py` | 仅允许新增 Public API（如 `reset_workspace()`） |

---

## 4. Migration Readiness Checklist

### 4.1 架构就绪

| 检查项 | 状态 |
|--------|------|
| RendererRegistry 已实现 | ✅ Phase 2-C.3 |
| Single Active Rule 已强制 | ✅ Phase 2-C.3 |
| PresentationRuntime 已实现 | ✅ Phase 2-C.2 |
| Interaction Protocol 已提取 | ✅ Phase 2-C.1 |
| Multi Renderer Proof 已通过 | ✅ Phase 2-C.4 |
| v6/ui 零 agent_workbench import | ✅ 已验证 |
| Renderer 层零 Runtime Implementation import | ✅ 已验证 |
| Renderer 层零 PySide6 import | ✅ 已验证 |

### 4.2 迁移前必须修正

| # | 修正项 | 优先级 |
|---|--------|--------|
| 1 | `app.py` 的 `main()` 连接 `--mode gui-v6` | 高 |
| 2 | `V6UIApplication` 改用 `PresentationRuntime` | 高 |
| 3 | `V6UIApplication` 改用 `RendererRegistry` | 高 |
| 4 | `V6UIApplication` 移除直接 `PresentationPipeline()` 调用 | 中 |
| 5 | `run_gui_v6()` 精简 UI 创建逻辑（委托给 Application） | 低 |

### 4.3 迁移风险

| 风险 | 等级 | 缓解措施 |
|------|------|---------|
| v6/ui 被 Runtime 概念污染 | 高 | 严格审查每个 import |
| 旧 `WorkbenchUIController` 代码残留 | 中 | 迁移后禁用 `run_gui()` |
| V6UIApplication 重新膨胀 | 高 | 保持职责：create/bind/start/shutdown |
| 双 UI 体系并存导致混乱 | 中 | `run_gui()` 标记为 deprecated |

---

## 5. Gate Decision

### 当前状态：可以进入 Phase 2-D.1

**条件**：先修正 4.2 节中的 3 个高优先级项目。

**不通过的话**：
- `V6UIApplication` 将绕过 `PresentationRuntime` 和 `RendererRegistry`
- 等于 Phase 2-C 全部白做
- 迁移将变成"把旧 UI 代码换到新目录"，而不是架构升级

---

## 6. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | 初始创建。Phase 2-D.0 Gate Check。 |