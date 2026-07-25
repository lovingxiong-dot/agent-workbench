# API Ownership Model — 能力所有权与审计规则

> **创建日期**: 2026-07-24
> **状态**: Active
> **适用范围**: 所有 Phase 所有 Step 的 API 审计
> **优先级**: 最高 — 与 [architecture-context.md](./architecture-context.md) 同级，Agent 执行任何操作前必须读取

---

## 0. 为什么需要这个文档

2026-07-24 Step 2 审计暴露了一个关键问题：**Agent 使用 Widget 级方法 grep 判定能力缺失，但实际能力通过 Adapter/Renderer 层提供。**

这是典型的"实现层扫描"误当"Contract 审计"。根本原因不是 Agent 能力不足，而是缺少一个明确的 **API 所有权模型**文档。

本文档定义：
- 每种能力属于哪一层
- 各层的验证顺序
- 能力闭环的判定标准

---

## 1. 核心原则

```
Capability Requirement
          ↓
Contract Definition (SPEC.md)
          ↓
    ┌─────┴─────┐
    ↓           ↓
Renderer API  Adapter API
    ↓           ↓
    └─────┬─────┘
          ↓
     Widget API
```

**审计应该问**："这个能力是否存在于 Contract Chain？"

**审计不应该问**："这个类有没有这个函数？"

---

## 2. API 所有权分层

### 2.1 层定义

| 层 | 职责 | 文件位置 | 调用方向 |
|----|------|----------|----------|
| **Contract** | 定义能力需求与接口契约 | `SPEC.md`, `product-contract.md` | 被引用 |
| **Renderer API** | InteractionEvent → UI 方法调用 | `presentation/renderers/v6_ui/event_renderer.py` | 读 Runtime 事件，写 Widget |
| **Adapter API** | ShellContract 状态 → UI 方法调用 | `presentation/renderers/v6_ui/shell_adapter.py` | 读 Shell 状态，写 Widget |
| **Widget API** | 直接暴露给 Adapter/Renderer 的公共方法 | `v6/ui/chat_area.py`, `left_panel.py`, `right_panel.py` | 被 Adapter/Renderer 调用 |
| **Service API** | 外部注入（Controller 直接调用 Widget 方法） | `controller.py` → `InputArea.set_model()` | 读 Controller，写 Widget |

### 2.2 层所有权规则

```
规则 1: Widget 方法名与 Contract 能力名不需要一一对应。
规则 2: 一个 Contract 能力可能由多个 Widget 方法组合实现。
规则 3: 部分能力完全由 Adapter/Renderer 层实现，Widget 不暴露同名方法。
规则 4: 部分能力由 Controller 通过 ControlBar 直接注入 Widget。
```

---

## 3. 能力所有权清单

### 3.1 ChatArea 相关能力

| 能力 | Contract 定义 | 所有权 | 实现路径 | 最终 Widget 方法 |
|------|-------------|--------|----------|-----------------|
| 用户消息追加 | `append_user` | **Widget API** | 直接调用 | `ChatArea.append_user()` |
| AI 消息追加 | `append_ai` | **Widget API** | 直接调用 | `ChatArea.append_ai()` |
| 流式输出 | `stream_chunk` / `stream_end` | **Widget API** | 直接调用 | `ChatArea.stream_chunk()` / `stream_end()` |
| 流式状态控制 | `set_streaming` | **Widget API** | 直接调用 | `ChatArea.set_streaming()` |
| 工具执行展示 | `tool_executed` | **Widget API** | 直接调用 | `ChatArea.tool_executed()` |
| 工作区重置 | `reset_workspace` | **Widget API** | 直接调用 | `ChatArea.reset_workspace()` |
| 标题设置 | `set_title` | **Widget API** | 直接调用 | `ChatArea.set_title()` |
| **消息历史恢复** | `load_messages` | **Adapter API** | `V6UIShellAdapter.update_workspace()` → | `ChatArea.reset_workspace()` + `append_user()` / `append_ai()` 逐条 |
| **模型列表更新** | `load_models` | **Service API** | `Controller` → `ControlBar` → | `InputArea.set_model()` |

### 3.2 LeftPanel 相关能力

| 能力 | Contract 定义 | 所有权 | 实现路径 | 最终 Widget 方法 |
|------|-------------|--------|----------|-----------------|
| 会话列表更新 | `update_sessions` | **Widget API** | 直接调用 | `LeftPanel.update_sessions()` |
| 激活会话设置 | `set_active_session` | **Widget API** | 直接调用 | `LeftPanel.set_active_session()` |
| **会话列表加载** | `load_sessions` | **Adapter API** | `V6UIShellAdapter.update_navigation()` → | `LeftPanel.update_sessions()` |
| **Agent 列表加载** | `load_agents` | **Service API** | `Controller` → `ControlBar` → | 不经过 LeftPanel |

### 3.3 RightPanel 相关能力

| 能力 | Contract 定义 | 所有权 | 实现路径 | 最终 Widget 方法 |
|------|-------------|--------|----------|-----------------|
| 文件展示 | `show_file` | **Widget API** | 直接调用 | `RightPanel.show_file()` |
| 终端输出 | `append_terminal` | **Widget API** | 直接调用 | `RightPanel.append_terminal()` |
| 窗口按钮 | `set_window_buttons` | **Widget API** | 直接调用 | `RightPanel.set_window_buttons()` |

---

## 4. 审计规则（强制）

### 4.1 验证顺序

```
验证顺序（必须严格遵守，不可跳过任何步骤）：

1. Contract     — 能力在 SPEC.md / product-contract.md 中是否定义？
2. Adapter      — 能力是否通过 V6UIShellAdapter 映射？
3. Renderer     — 能力是否通过 V6UIEventRenderer 映射？
4. Widget       — 能力最终在哪个 Widget 方法落地？

只有 4 层全部检查后，才能判定能力是否存在。
```

### 4.2 错误方式

```
❌ 错误审计模型：

grep ChatArea.load_messages
  → 没有方法
  → 判定 Missing

原因：把"Widget 方法名 = Contract 能力名"当成了前提。
实际：V6 架构中，能力可能通过 Adapter/Renderer 层组合实现。
```

### 4.3 正确方式

```
✅ 正确审计模型：

能力: 消息历史恢复

Step 1 — Contract:
  SPEC.md 定义: "ChatArea 必须支持消息历史恢复"
  → 能力已定义

Step 2 — Adapter:
  V6UIShellAdapter.update_workspace() 负责将 ShellContract 状态同步到 UI
  → 存在映射

Step 3 — Renderer:
  V6UIEventRenderer 处理 MESSAGE_COMPLETE / MESSAGE_USER 等事件
  → 存在事件映射

Step 4 — Widget:
  ChatArea.reset_workspace() + append_user() + append_ai() 组合提供恢复能力
  → 能力闭环完整

结论: PASS
```

### 4.4 能力闭环验证模板

```
┌─────────────────────────────────────────┐
│ 能力: [能力名称]                          │
├─────────────────────────────────────────┤
│ Contract 定义: [SPEC.md 位置]             │
│ Adapter 映射:  [V6UIShellAdapter 方法]    │
│ Renderer 映射: [V6UIEventRenderer 方法]   │
│ Widget 落地:   [v6/ui 组件方法]           │
├─────────────────────────────────────────┤
│ 结论: PASS / NEED TRACE / GAP            │
└─────────────────────────────────────────┘
```

---

## 5. 审计结果判定标准

| 判定 | 含义 | 示例 |
|------|------|------|
| **PASS** | 4 层验证全部通过，能力闭环完整 | 消息恢复：Adapter→Widget 组合 |
| **NEED TRACE** | 能力存在但需要实际数据流验证 | 跨 Step 依赖的能力（如 Session 持久化） |
| **GAP** | 4 层验证后确认能力不存在 | 真正的缺失，需要记录为 Debt |

### 5.1 非 GAP 的情况

以下情况 **不应判定为 GAP**：

- Widget 方法名与 Contract 能力名不同（如 `load_messages` → `reset_workspace` + 逐条渲染）
- 能力由 Adapter 层实现，Widget 不暴露同名方法（如 `load_sessions` → `update_sessions`）
- 能力由 Controller 直接注入 Widget（如 `load_models` → `InputArea.set_model()`）
- 能力由多个 Widget 方法组合实现（如消息恢复 = `reset_workspace` + `append_user` + `append_ai`）

---

## 6. 与 architecture-context.md 的关系

| 文档 | 职责 |
|------|------|
| [architecture-context.md](./architecture-context.md) | 长期架构知识：Boundary Map、Change Permission Matrix、Frozen Zone、数据流全貌 |
| **api-ownership-model.md**（本文档） | API 所有权模型：每项能力的所属层、验证顺序、审计规则 |

两者互补：
- `architecture-context.md` 回答"架构边界在哪里"
- `api-ownership-model.md` 回答"能力属于哪一层，如何验证"

Agent 执行任何审计前，必须同时读取这两个文档。

---

## 7. Step 2 审计修正记录

### 7.1 原始错误判定

```
ChatArea API: 8/10 (Missing: load_messages, load_models)
LeftPanel:    2/4  (Missing: load_sessions, load_agents)
```

### 7.2 修正后判定

```
Widget Surface Audit:
  ChatArea:  8 Widget methods — PASS
  LeftPanel: 2 Widget methods — partial (remaining via Adapter/Service)

Capability Contract Audit:
  消息恢复: PASS (Adapter API: V6UIShellAdapter.update_workspace)
  模型加载: PASS (Service API: Controller → InputArea.set_model)
  会话加载: PASS (Adapter API: V6UIShellAdapter.update_navigation)
  Agent 加载: PASS (Service API: Controller → ControlBar)

Final: PASS WITH FINDINGS
  Finding: 4 项能力不在 Widget 层直接暴露，通过 Adapter/Service 层实现
  Impact: 无 — 不阻塞任何 Step
  Verified: Step 4 (Provider), Step 6 (Session)
```

---

## 8. 执行规则

1. 任何 API 审计必须使用 4 层验证顺序，禁止 Widget 级 grep 判定
2. 发现能力不在 Widget 层时，必须追踪 Adapter → Renderer → Service 层
3. 只有 4 层全部检查后确认不存在，才能判定为 GAP
4. 判定为 GAP 的能力必须记录为 Debt，并标注影响范围
5. 审计结果必须区分：Widget Surface Audit 和 Capability Contract Audit