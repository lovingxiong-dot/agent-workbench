# Architecture Context — 长期架构知识

> **创建日期**: 2026-07-24
> **状态**: Active
> **适用范围**: v6.14 ~ v7.x 全部开发
> **优先级**: 最高 — Agent 执行任何操作前必须读取本文档
> **升级自**: `phase3-context.md`（Phase 3 临时上下文 → 长期架构知识）

---

## 0. 为什么需要这个文档

Agent 上下文压缩后，会丢失架构解释层，导致：
- 把"Contract 级能力要求"误读为"Widget 级方法要求"
- 重新从代码 grep 开始，而不是从已有的设计文档开始
- 清单执行变成机械扫描，而非能力闭环验证

本文档是项目架构的"单一事实源（Single Source of Truth）"，优先级高于任何临时任务清单。

---

## 1. Boundary Map（边界地图）

```
┌─────────────────────────────────────────────────────┐
│                   FROZEN ZONE                        │
│                                                     │
│  Runtime Kernel (v6/runtime/, 19 files)              │
│  Decision Layer (decision_manager.py)                │
│  Interaction Protocol (request.py, event.py)         │
│  Interaction Layer (layer.py)                        │
│  Controller Contract (controller.py, 27 methods)     │
│                                                     │
│  → 零修改。任何 Phase 任何 Step 不可触碰。            │
├─────────────────────────────────────────────────────┤
│                   EVOLUTION ZONE                     │
│                                                     │
│  V6UIEventRenderer (event_renderer.py)               │
│  V6UIShellAdapter (shell_adapter.py)                 │
│                                                     │
│  → 可修改，但必须保持 Contract 兼容。                  │
├─────────────────────────────────────────────────────┤
│                   IMPLEMENTATION ZONE                │
│                                                     │
│  v6/ui/ (22 files, Pure UI Foundation)               │
│  agent_workbench/ui/workbench/ (32 files)            │
│                                                     │
│  → 条件修改：审计时可读，修复时需 Review Gate。         │
└─────────────────────────────────────────────────────┘
```

---

## 2. Change Permission Matrix（变更权限矩阵）

| Layer | Phase 3 | 说明 |
|-------|---------|------|
| Runtime Kernel | ❌ | Frozen — 零修改 |
| Decision Layer | ❌ | Frozen — 零修改 |
| Interaction Protocol | ❌ | Frozen — 零修改 |
| Controller Contract | ❌ | Frozen — 可新增方法，不可修改签名 |
| V6UIEventRenderer | ✅ | 可修改，保持 InteractionEvent 映射 |
| V6UIShellAdapter | ✅ | 可修改，保持 ShellContract 兼容 |
| v6/ui Widgets | ⚠️ | 条件修改 — 审计只读，修复需 Review Gate |
| agent_workbench/ui/workbench/ | ⚠️ | 条件修改 — 非当前 Phase 核心 |

---

## 3. 数据流全貌

```
Runtime (agent_workbench/runtime/)
    ↓ RuntimeRequest
InteractionLayer (runtime/interaction/layer.py)
    ↓ InteractionEvent
Presentation Layer (agent_workbench/presentation/)
    ├── V6UIEventRenderer (renderers/v6_ui/event_renderer.py)
    │   └── InteractionEvent → ChatArea 方法调用（10 种事件类型）
    └── V6UIShellAdapter (renderers/v6_ui/shell_adapter.py)
        └── ShellContract → LeftPanel/ChatArea/RightPanel 方法调用
            ↓
v6/ui/ (Pure UI Foundation, 22 files)
    ↓ Qt
Display
```

### 3.1 架构禁止项

| # | 禁止 |
|---|------|
| C1 | v6/ui 不引用 `agent_workbench/` 包 |
| C2 | UI 层不负责数据 |
| C3 | Runtime 层不感知 UI |
| C4 | Presentation Layer 是唯一翻译层 |
| C5 | 不修改 Frozen Boundary |

---

## 4. API Audit Rule（审计规则 — 强制）

### 4.1 错误方式

```
grep ChatArea.load_messages → 不存在 → 判定 Missing
```

### 4.2 正确方式

```
验证顺序（必须严格遵守）：

1. Contract     — 能力在 SPEC.md / product-contract.md 中是否定义？
2. Adapter      — 能力是否通过 V6UIShellAdapter 映射？
3. Renderer     — 能力是否通过 V6UIEventRenderer 映射？
4. Widget       — 能力最终在哪个 Widget 方法落地？

只有 4 层全部检查后，才能判定能力是否存在。
Widget 方法名与 Contract 能力名不需要一一对应。
```

### 4.3 能力闭环验证模板

```
能力: [名称]
Contract 定义: [SPEC.md 位置]
  ↓
Adapter 映射: [V6UIShellAdapter 方法]
  ↓
Renderer 映射: [V6UIEventRenderer 方法]（如适用）
  ↓
Widget 落地: [v6/ui 组件方法]
  ↓
结论: PASS / NEED TRACE / GAP
```

### 4.4 Provider 审计规则（强制）

```
Provider 能力审计遵循 Contract → Registry → Factory → Runtime 链：

验证顺序（必须严格遵守）：

1. Contract     — Provider Interface 是否定义？ProviderEndpoint 契约是否完整？
2. Registry     — Provider 类型是否在 ProviderRegistry 中注册？
3. Factory      — 是否可通过 Provider 类型 + config 实例化？
4. Config       — 配置注入路径是否完整？环境变量展开链是否正常？
5. Runtime      — switch_provider() / chat_stream() 链路是否可达？

默认配置中不存在 ≠ 能力缺失。
禁止以 default.yaml 中的 Provider 列表作为能力存在性判定依据。
```

---

## 5. API 所有权模型

详见 [api-ownership-model.md](./api-ownership-model.md)。

核心原则：

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

### 5.1 当前能力分布

| 能力 | 所有权 | 实现路径 |
|------|--------|----------|
| 用户消息追加 | Widget API | `ChatArea.append_user()` |
| AI 消息追加 | Widget API | `ChatArea.append_ai()` |
| 流式输出 | Widget API | `ChatArea.stream_chunk()` / `stream_end()` |
| 流式状态控制 | Widget API | `ChatArea.set_streaming()` |
| 工具执行展示 | Widget API | `ChatArea.tool_executed()` |
| 工作区重置 | Widget API | `ChatArea.reset_workspace()` |
| 标题设置 | Widget API | `ChatArea.set_title()` |
| 会话列表更新 | Adapter API | `V6UIShellAdapter.update_navigation()` → `LeftPanel.update_sessions()` |
| 消息历史恢复 | Adapter API | `V6UIShellAdapter.update_workspace()` → `ChatArea.reset_workspace()` + 逐消息渲染 |
| 模型列表更新 | Service API | `InputArea.set_model()` 通过 ControlBar/Controller 注入 |
| Agent 列表更新 | Service API | 通过 ControlBar 注入，不经过 LeftPanel |

---

## 6. Frozen Boundary 详细清单

| 范围 | 文件数 | 说明 |
|------|--------|------|
| `v6/runtime/` | 19 | Runtime Kernel — Frozen |
| `runtime/interaction/request.py` | 1 | RuntimeRequest Protocol — Frozen |
| `runtime/interaction/event.py` | 1 | InteractionEvent Protocol — Frozen |
| `runtime/interaction/layer.py` | 1 | WorkbenchInteractionLayer — Frozen |
| `runtime/manager/decision_manager.py` | 1 | Decision Layer — Frozen |
| `controller.py` (public API) | 27 methods | Controller Contract — Frozen (add only) |
| `v6/ui/` (core files) | 22 files | Pure UI Foundation — 审计对象，不修改 |

---

## 7. Provider 配置

### 7.1 已注册 Provider

| Provider | 状态 | 配置来源 |
|----------|------|----------|
| agnes | 已注册 | 环境变量 |
| minimax-m3 | 已注册 | 环境变量 |
| deepseek-v4-pro | 已注册 | 当前 Agent 使用中 |

### 7.2 Provider 配置规则

- **API Key 存储**: 环境变量或 `.env` 文件（不进入 Git）
- **Model 参数**: 在 `config/` 目录下配置
- **文档引用**: 本文档只记录 Provider ID 和配置来源，不记录 Key

### 7.3 MiniMax-M3 参数

```
Provider ID: minimax-m3
Vendor: MiniMax
Max Input: 1,000,000 tokens
Max Output: 128,000 tokens
Features: tool call, images, reasoning
Endpoints: openai-compatible + anthropic-compatible (custom protocol)
API Key: 环境变量 MINIMAX_API_KEY
```

---

## 8. 已知状态

### 8.1 测试基线

```
362 passed, 12 failed (all pre-existing)

Known Existing Issues:
- host_contract x4: NavigatorHost/InspectorHost/StatusBarHost in Workbench OS layer
- external provider credential x8: @_skip_no_openai 不再跳过，API key 为空
```

### 8.2 已记录债务

| ID | 描述 | 严重度 | 状态 |
|----|------|--------|------|
| ADR-010 | `execute_agent_action` 绕过 Runtime | — | 已知，不阻塞 |
| ADR-011 | Controller API Surface Freeze | — | 已冻结 |
| Debt-001 | `@_skip_no_openai` 语义不准确 | Low | 后续统一处理 |
| UI-CONTRACT-001 | API 所有权需 Contract 级验证 | Low | 已记录，非阻塞 |
| **DEBT-002** | Status Update Rendering Gap：`STATUS_UPDATE` handler 为 no-op，Protocol 已存在但 Widget 未实现 | Low | 不阻塞，Phase 2-C 预留 |
| **DEBT-003** | Provider UI 动态切换能力未覆盖验证：`switch_provider()` 逻辑正确但未端到端验证 UI 切换流程 | R2 | 可在 Step 5 LLM 闭环验证中覆盖 |

### 8.3 Observation Registry（架构观察）

| ID | 描述 | 严重度 | 建议 |
|----|------|--------|------|
| **OBS-003** | Workspace Recovery Bypass Observation：`_on_session_selected()` 通过 `Controller.get_state()` 读取消息，绕过 Interaction Protocol 的 WorkspaceState 恢复路径 | Medium | 当前允许（Controller-as-Facade），未来迁移至 Query Capability → Interaction Protocol → WorkspaceState 标准路径 |
| **OBS-004** | MiniMax 未作为 default provider 启用：`default.yaml` 仅配置了 agnes，MiniMax 需手动添加 config 条目 | R1 | 配置选择，非能力缺失。Provider Contract → Registry → Factory 链路完整 |
| **OBS-005** | Preflight Check 环境变量展开路径不一致：`preflight_check()` 通过 `api_key_env` 字段展开，`OpenAIProvider._expand()` 通过 `${...}` 语法展开，两路径不同导致 preflight 误报 | R1 | 诊断缺口，不影响实际 API 调用。建议 preflight_check 复用 `_expand()` 逻辑 |

### 8.4 Phase 3.9 Frozen Contracts（Presentation Layer 冻结边界）

> **FROZEN_SINCE**: v6.14-phase3.9
> **冻结范围**: `v6/presentation/contracts/` 下的三层契约

| 契约 | 文件 | 冻结内容 |
|------|------|---------|
| Model Contract | `contracts/model_contract.py` | `BasePresentationModel`: model_id, timestamp, metadata, model_type |
| Renderer Contract | `contracts/renderer_contract.py` | `Renderer`: initialize, render, dispose, supported_models |
| Adapter Contract | `contracts/adapter_contract.py` | `Adapter`: set_callback, reset; `EventAdapterContract`: render; `StateAdapterContract`: adapt |

**冻结规则**:
- 新增方法：允许（向后兼容）
- 修改签名：禁止（Breaking Change）
- 删除方法：禁止（Breaking Change）
- 新增 Model 字段：允许（需提供默认值）
- 修改 Model 字段类型：禁止（Breaking Change）

### 8.5 Phase 3.9 Architecture Debt（Presentation 架构演进债）

| ID | 描述 | 严重度 | 建议 |
|----|------|--------|------|
| **DEBT-004** | Renderer 直接依赖 chat_items：当前 Renderer 函数（render_user_message 等）直接 import `v6.ui.chat_items`，导致 Console/Web/CLI Renderer 无法复用 | Medium | Phase 4 迁移到 `QtRendererBase` 子类，通过 `render_to_widget` 抽象隔离 |
| **DEBT-005** | Legacy design_tokens compatibility layer：`design_tokens.py` 与 `design/` 包并行存在（Parallel Migration Structure），非硬编码问题。`design/` 已正确拆分 tokens/layouts/themes，legacy 文件保留向后兼容 | Low | Phase 4 移除 legacy 兼容层，统一使用 `design/` 包 |
| **DEBT-006** | MessageViewModel 未继承 BasePresentationModel：`models.py` 中的 `MessageViewModel` 等基类未继承 Frozen Contract 的 `BasePresentationModel` | Low | Phase 4 统一迁移 |

### 8.6 Phase 3.9 Runtime Event Boundary Golden Path

验证链路（InteractionEvent 层面，非 Real Runtime Task 层面）：

```
GoldenPathDemo
    ↓ 产出 InteractionEvent（Simulated Event Boundary）
EventAdapter
    ↓ 转换
PresentationModel
    ↓
RendererRegistry
    ↓
ChatScene (QGraphicsWidget)
```

与 DemoProvider 的区别：
- **DemoProvider**: 创建 fake PresentationModel → 直接渲染（绕过 EventAdapter）
- **GoldenPathDemo**: 创建 InteractionEvent → EventAdapter → PresentationModel → Renderer → UI（验证 Presentation Pipeline 在 Event Boundary 层面的正确性）

已验证：
- ✅ Event Boundary 正确
- ✅ Presentation Pipeline 完整
- ✅ 多 Renderer 输出一致

未验证（Phase 3.10）：
- ❌ Real Task Execution（DecisionManager → Capability → Task）
- ❌ Capability Chain
- ❌ Provider Execution

### 8.7 Phase 3.9 Close Status

| 项目 | 状态 |
|------|------|
| Demo Provider isolation | Complete |
| Frozen Contracts | Complete |
| Renderer Interface | Foundation Complete |
| Renderer Migration | Deferred to Phase 4 |
| Design Structure | Complete |
| Golden Path | Verified at Interaction Boundary level |
| Real Runtime Task | Future Phase 3.10 |

**关闭状态**: Presentation Contract Stabilization Complete. Presentation Runtime Boundary Verified. Renderer Backend Migration Deferred to Phase 4. Golden Path validated at Interaction Boundary level.

### 8.8 Phase 3.10 — Runtime Presentation Integration（Next）

```
Phase 3.9 验证: Event Boundary ✓
Phase 3.10 目标: Real Runtime Task Execution

User Request → RuntimeRequest → DecisionManager → Capability → Task
    → RuntimeEvent → InteractionLayer → EventAdapter → PresentationModel → UI
```

详见 [phase3-execution-plan.md#phase-310](./phase3-execution-plan.md) 中的 Phase 3.10 计划。

---

## 9. 文档引用链

```
architecture-context.md       ← 本文档（长期架构知识，Agent 执行前必读）
api-ownership-model.md        ← API 所有权模型
phase3-execution-plan.md      ← Phase 3 执行清单（Step 1-10 子任务）
phase3-validation-plan.md     ← Phase 3 验证框架（Gate 定义 + 风险评估）
phase3-step-2-report.md       ← Step 2 独立审计报告
phase3-step-3-report.md       ← Step 3 数据链路验证报告
cross-comparison-report.md    ← UI 设计基线 vs 当前实现
architecture-boundaries.md    ← Frozen Zone 定义
SPEC.md                       ← V6 接口与信号契约
product-contract.md           ← Workbench OS 产品契约
product-shell-phase-report.md ← Phase 2-D Closure Report
```

### 9.1 Agent 执行前读取顺序

```
1. architecture-context.md     ← 架构语义（长期）
2. api-ownership-model.md      ← API 所有权
3. phase3-execution-plan.md    ← 执行清单
4. 执行当前 Step
5. 输出 Step Report
6. 等待 Review
```

---

## 10. 执行规则

1. 读取本文档 → 理解架构语义和 Boundary Map
2. 读取 `api-ownership-model.md` → 理解 API 所有权
3. 读取 `phase3-execution-plan.md` → 找到第一个 PENDING Step
4. 执行该 Step → 按子任务顺序
5. 验证 → 使用能力闭环验证，禁止 Widget 级 grep 判定
6. 报告 → 更新执行计划，输出 Step Report
7. 等待 Review → 不自动进入下一 Step
8. 发现问题 → 记录，不扩大修改范围
9. 禁止修改 Frozen Zone
10. 禁止将 API Key 写入任何 Git 追踪文件