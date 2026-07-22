---
# Project Blueprint
## 元信息
| 项目名称 | AI Agent 工作台 | 当前版本 | v6.14.0-alpha | 公开立项标签 | v6.0.0-alpha | 内部迁移标签 | v6.5.8-alpha | 存档次数 | 61 |

## Current Development Authority

> **The active development line is `v6-agent` based on `v6.8.0-alpha` (V6 Framework Core Foundation Baseline).**
> **Public baseline: `v6.0.0-alpha`.**
> **Framework Core baseline: `v6.8.0-alpha`.**
> **V6 Runtime Foundation Baseline: `v6.9.6-foundation` — frozen at 2026-07-09. The Runtime Kernel is complete. The next era is the Agent Workbench Ecosystem.**
> **From v6.11 onward, Runtime is considered stable infrastructure. The primary evolution target becomes the Workbench Layer, where Metadata, Schema, Plugins, and Digital Identity form the long-term product differentiation.**
> **自 v6.11 起，Runtime 视为稳定基础设施，后续主要演进对象转为 Workbench Layer；Metadata、Schema、Plugin 与 Digital Identity 将成为产品长期演进方向。**

| Item | Value |
|---|---|
| Active branch | `v6-agent` |
| Framework Core baseline | `v6.8.0-alpha` |
| Frozen foundation branch | `v6-core` |
| Service extension branch | `v6-service` |
| Public baseline | `v6.0.0-alpha` |
| Internal migration checkpoint | `v6.5.8-alpha` (historical, not public) |
| Frozen archive | `v5-dev` |
| Rule | Do not modify `v5-dev`. Framework Core (`v6-core`) only accepts bug fixes. Service work goes to `v6-service`. Agent work goes to `v6-agent`. |

See also [`PROJECT_LINEAGE.md`](./PROJECT_LINEAGE.md) for the complete V5 / V6 identity map.

For governance rules, see [`AGENT_ENTRY.md`](./AGENT_ENTRY.md), [`PROJECT_DECLARATION.md`](./PROJECT_DECLARATION.md), and [`PROJECT_STATE.md`](./PROJECT_STATE.md).

## Product Contract — Workbench OS 1.0

> 产品契约已冻结于 [`docs/v6/product-contract.md`](./docs/v6/product-contract.md)。
>
> 该文档以产品词典风格定义 Workbench OS 1.0 的核心概念，是 Qt / Web / CLI / Remote 所有前端与后端必须共同遵守的产品定义。
>
> 新增概念或更改核心命名前，必须先更新 Product Contract 并通过架构评审。

## 产品定位

**Agent Workbench is the Official Product Validation Platform of the V6 Runtime.**

**Workbench Constitution — No-Code Registration Principle**

除 Runtime Kernel 和内置核心能力外，所有 Provider、LLM、MCP、Skill、Tool、Workflow、Prompt、Memory 等扩展对象，都应支持通过 Workbench UI 注册、配置和管理。开发者不应为了新增一个实例而修改源码。

流程：UI → ConfigManager → Registry Reload → Capability Update → Agent Ready

反模式：UI → 修改代码 → 重新编译 → 重新启动

这意味着：
- 新增一个 OpenAI 兼容模型 → 点 "AI Models → +"
- 接入一个 MCP Server → 点 "MCP → +"
- 写了一个 Python 技能 → 点 "Skills → +"，选择脚本即可
- 换模型、改 API 地址、调整权限、禁用某个工具 → 全部在 Workbench 完成

这句话决定以后所有开发行为：

- **任何 Provider**，只有能安装到 Workbench 并跑通，才算完成。
- **任何 Tool**，只有能在 Workbench 中注册、执行、观测，才算完成。
- **任何 Skill**，只有能在 Workbench 中安装、发现、调用，才算完成。
- **任何 Workflow**，只有能在 Workbench 中编排、运行、调试，才算完成。
- **任何 Memory / Knowledge / Agent Identity**，只有能在 Workbench 中验证体验，才算完成。

Workbench 不是 Demo，不是临时演示程序，不是「先放这里之后重构」的妥协。它是所有新能力的集成验证平台与产品化门槛。任何在 Workbench 中无法以 Composable 方式集成的新能力，都不应进入框架核心。

## Cross-Layer Contract — Metadata First

> **Metadata 不属于任何单一 Layer，它是跨层契约（Cross-layer Contract）。**

```text
Runtime
   │
   │ exposes via metadata()
   ▼
Metadata Contract  ←  agent_workbench/metadata/
   │
   │ adapts via MetadataAdapter
   ▼
Workbench
```

- Runtime 不拥有 Metadata；Workbench 也不拥有 Metadata。
- 双方只是共同遵守同一套 `MetadataDefinition` 契约。
- 未来 Remote Agent、Gateway、Plugin、Marketplace、CLI、Web 都可以直接读取 Metadata，而无需依赖 Runtime 或 UI 的具体实现。
- Metadata 必须平台无关：不包含 Qt 控件、Web 组件、CLI 命令等任何具体消费端的假设。
- **铁律：Metadata 永远不能依赖 Runtime。依赖方向只能是 `Runtime → Metadata`，绝不能反向。**

这一契约是 v6.11 之后所有模块的默认假设。任何 Runtime Module 暴露给 Workbench 的对象，都必须通过 Metadata 描述；任何 UI 消费 Runtime 对象，都必须通过 `MetadataAdapter` 翻译为 `PresentationModel`。

### Description-Driven Development

> **Everything is described before it is implemented.**

新增任何能力的标准顺序：

```text
Identity → Metadata → Schema → Runtime → Execution
```

1. **Identity**：它是什么（AI / Agent / Persona）。
2. **Metadata**：描述它（Definition / Property / Action / Statistics）。
3. **Schema**：如何配置它（字段类型、验证、默认值）。
4. **Runtime**：如何执行它（Engine / Provider / Resource binding）。
5. **Execution**：真正运行。

从 v6.11 开始，Workbench 从「代码驱动」转向「描述驱动」。

### Metadata Contract 长期冻结（v6.11.0-beta.4 起）

从 v6.11.0-beta.4 开始，以下核心 Metadata 对象进入**长期冻结**状态：

```text
MetadataDefinition
MetadataProperty
MetadataAction
MetadataStatistics
ValueType
MetadataType
ResourceDefinition
ResourceConnection
ResourceType
```

**冻结规则：**

1. **只允许 Additive Change（新增字段）**，禁止 Breaking Change（改结构、删字段、改字段语义、改枚举值含义）。
2. 新增字段必须提供默认值，保证旧消费端无需修改即可反序列化。
3. 所有字段语义必须在 `agent_workbench/metadata/` 中以文档或单测形式固定，不得依赖 Runtime 或 UI 的隐式约定。

**受影响消费端（任何结构变更都会级联到这些 Layer）：**

```text
Navigator
Inspector
Marketplace
CLI
Gateway
Remote Agent
Web Plugin
Extension Host
```

**变更流程：**

- 如需新增字段 → 直接提 PR，补充单测与文档。
- 如需修改现有字段 → 必须走架构审查，优先通过新增字段 + deprecation 标记解决，而不是直接改结构。

这条规则保证：v6.12 及以后的所有功能扩展，都能在不变更 Metadata Contract 的前提下完成。

### Capability vs Resource

| 维度 | Capability | Resource |
|---|---|---|
| 问题 | **What I can do**（我会什么） | **What I can use**（我可以支配什么） |
| 示例 | Coding、Research、Trading、Vision、Planning | Python Env、Chrome、VS Code、Cursor、Claude Code、Docker、WSL |
| 语义 | 能力类型 | 执行目标或工具库存 |
| 配置位置 | Capability Registry | Resource Registry |

**Capability 永远是能力类型，Resource 永远是可使用的工具或环境。** Python、Chrome、VS Code、Claude Code 都是 Resource，不是 Capability。

## V6 Runtime Foundation Baseline (Frozen)

> **Status: `v6.9.6-foundation` — V6 Runtime Foundation Baseline Frozen.**

The v6.9.x series is complete. The following layers of the Runtime Kernel are now frozen:

| Layer | Freeze Commit | Contract Document |
|---|---|---|
| Task | v6.9.2-alpha | `docs/v6/runtime-kernel-spec.md` |
| Manager / Capability Tree | v6.9.3-alpha | `docs/v6/runtime-kernel-spec.md` |
| Decision Layer | v6.9.4-alpha | `docs/v6/runtime-kernel-spec.md` |
| Interaction Boundary | v6.9.5-alpha | `docs/v6/runtime-kernel-spec.md` |
| Capability Runtime Contract | v6.9.6-alpha | `docs/v6/runtime-kernel-spec.md` |
| Repository Governance | v6.9.6-hygiene | `docs/v6/repository-governance.md` |
| Foundation Baseline | v6.9.6-foundation | This document + `CHANGELOG.md` |

From this point forward:

- **No new Runtime-level modules** may be added without architecture review.
- **All new capabilities** must enter through the frozen Capability Runtime Contract.
- **All GUI, Provider, Tool, Skill, Workflow, Memory, and Knowledge work** branches from `v6.9.6-foundation`.
- **Repository hygiene** is enforced by `scripts/audit_repository.py` and `scripts/verify_repository.py`.

## Agent Workbench 定位

> **Agent Workbench 是 Personal Agent Workbench / Agent IDE 的第一个参考实现，也是 V6 Runtime 的官方产品化验证平台（Official Product Validation Platform）。**

它不是 Demo，也不是一个聊天机器人。它是一个可以不断安装能力、工具、Provider、Workflow 的 AI 工作台。Runtime、UI、Engine、Service、Module 等全部能力首先在 Workbench 中完成集成验证，证明其体验、边界、异常、性能均达到产品化标准后，再决定是否进入 `v6-core` / `v6-service` 框架核心。

这一句话决定以下行为：

- 禁止为 Demo 快速写特殊逻辑或临时分支。
- 禁止「先放这里，之后再重构」的折中方案。
- Workbench 自然成为所有新能力的集成验证平台与产品化门槛。
- 任何在 Workbench 中无法以 Composable 方式集成的新能力，都不应进入框架核心。

## Runtime Decision Layer Contract Boundary (v6.9.4-alpha)

> **v6.9.4-alpha introduces the Runtime Decision Layer.**

### Frozen Control Plane Contracts

以下对象在 v6.9.4-alpha 冻结，作为 Runtime Control Plane 与 Execution Plane 之间的稳定 ABI（Application Binary Interface）边界：

| Contract | Location | Status |
|---|---|---|
| `RuntimeMode` | `agent_workbench/runtime/decision/schema.py` | Frozen |
| `Intent` / `IntentType` | `agent_workbench/runtime/decision/schema.py` | Frozen |
| `RuntimeDecision` | `agent_workbench/runtime/decision/schema.py` | Frozen |
| `RuntimeDecision → Orchestrator` boundary | `Orchestrator.dispatch(decision)` | Frozen |

### What RuntimeDecision Is NOT

- **Not a UI Model**：UI 不允许直接构造 `RuntimeDecision`；UI 必须生成 `RuntimeRequest`，由 Decision Layer 转换为 `RuntimeDecision`。
- **Not an API Request Model**：MCP / Gateway / Remote Agent 入口同样必须先转换为 `RuntimeRequest`，再进入 Decision Layer。
- **Not a Capability Model**：`RuntimeDecision` 不持有 `CapabilityChain` / `CapabilityDefinition` 对象，只保存字符串引用与序列化后的基础数据。
- **Not a Task Model**：`Task` 是 Execution Plane 内部状态；`RuntimeDecision` 是 Control Plane 输出。

### Dependency Direction

```
User / UI / MCP / Local Agent / Remote Agent
                |
                ↓
        RuntimeRequest
                |
                ↓
        Decision Layer (ManagerAI → Interpreter → Resolver → Policy)
                |
                ↓
        RuntimeDecision  ←── frozen contract
                |
                ↓
    Orchestrator / Execution Layer
```

### Forbidden Patterns

- UI 直接调用 Capability / Provider / Service。
- LLM 直接选择 Tool（由 `Interpreter` 拒绝 tool/function calling）。
- `decision` 包反向依赖 `capability` / `planner` / `service` / `orchestrator` 实现。
- 任何入口绕过 `RuntimeDecision` 直接操作 `Task` 内部状态。

## Workbench Interaction Boundary Layer (v6.9.5-alpha)

> **v6.9.5-alpha introduces the Workbench Interaction Boundary Layer.**

### Goal

将 Workbench 从 Runtime Owner 改造为 Runtime Client。所有外部入口统一通过 `RuntimeRequest` 进入 Runtime，Runtime 通过 `InteractionEvent` 流输出状态。

```
User / UI / MCP / Local Agent / Remote Agent
                |
                ↓
        RuntimeRequest  (external input protocol)
                |
                ↓
    WorkbenchInteractionLayer  (boundary, no business logic)
                |
                ↓
        AgentWorkbenchRuntime
                |
                +---- DecisionManager  (Runtime internal)
                |           |
                |           ↓
                |   RuntimeDecision  (frozen ABI)
                |           |
                |           ↓
                +---- Orchestrator / Execution Layer
                |
                ↓
        RuntimeEvent Stream
                |
                ↓
        RuntimeEventMapper  (Runtime language → UI language)
                |
                ↓
        InteractionEvent
                |
                ↓
        UIEventRenderer  (protocol)
                |
                ↓
        Qt / Web / CLI
```

### Key Contracts

| Contract | Location | Responsibility |
|---|---|---|
| `RuntimeRequest` | `agent_workbench/runtime/interaction/request.py` | 外部输入协议；不表达 capability 路由意图 |
| `InteractionEvent` | `agent_workbench/runtime/interaction/event.py` | UI 事件协议；含 `source` 字段追踪多入口 |
| `RuntimeEventMapper` | `agent_workbench/runtime/interaction/mapper.py` | `RuntimeEvent → InteractionEvent`，不依赖 Renderer |
| `UIEventRenderer` | `agent_workbench/runtime/interaction/renderer.py` | 消费 `InteractionEvent` 的协议 |
| `WorkbenchInteractionLayer` | `agent_workbench/runtime/interaction/layer.py` | 边界层；不持有 `DecisionManager` |

### Rules

- `RuntimeRequest.source` 是环境上下文边界（`global_chat` / `workspace_session` / `command_bar` / `mcp` 等），不是 capability 路由指令。
- `RuntimeRequest.action_id` 表示用户动作（如 `"format_current_file"`），不是 Runtime capability。
- `WorkbenchInteractionLayer` 只调用 `AgentWorkbenchRuntime.submit_request()`；`DecisionManager` 保持在 Runtime 内部。
- `AgentWorkbenchRuntime.submit_request()` 是纯入口，不增加 session / identity / memory / queue / remote agent 等业务判断。
- CHAT 路径不伪造 `TASK_STARTED` / `TASK_FINISHED`。

## Presentation Architecture (v6.14.0-alpha — Phase 2-B Freeze)

> **v6.14.0-alpha introduces the Presentation Boundary — the formal separation of UI from Runtime.**

### Architecture

```
Runtime
    |
    | Interaction Contract
    |
Presentation Runtime
    |
    | Renderer Adapter
    |
Pure UI Foundation
```

### Layer Ownership

| Layer | Owns | Does NOT Own |
|-------|------|-------------|
| **Application** (`application/`) | startup, dependency wiring, lifecycle | UI behavior, Renderer logic |
| **Runtime** (`runtime/`) | execution, agent lifecycle, capability | UI, v6/ui, Widget |
| **Protocol** (`runtime/interaction/`) | communication contracts | UI implementation |
| **Renderer** (`presentation/renderers/`) | data→UI mapping, event→UI method | Runtime Implementation, Widget internals |
| **v6/ui Foundation** (`v6/ui/`) | visual system, layout, interaction widgets | Runtime, Agent, Session, Model, LLM, Tool |

### v6/ui Positioning

`v6/ui` is the **frozen Pure UI Foundation** — the canonical Presentation Foundation for Agent Workbench OS.

It is NOT:
- The deprecated `v6-agent` application architecture
- `WorkbenchUIController` layer
- A "UI component library" that can be redesigned per Renderer
- Runtime presentation logic

It IS:
- Visual System (dual-theme color palette, fonts, icons)
- Layout System (three-panel QSplitter, collapse/expand)
- Interaction Component System (LeftPanel, ChatArea, RightPanel, InputArea, HeaderBar, FunctionPage)
- Theme System (dark/light instant toggle)
- UX Specification (spacing, border-radius, hover states, drag)

### Renderer Constraints

```
Allowed:
  ✓ Interaction Contract imports (runtime.interaction.event)
  ✓ v6/ui Public API calls

Forbidden:
  ✗ Runtime Implementation imports (engine, executor, session, llm, tool)
  ✗ v6/ui private member access (._scene, ._stream, ._input)
  ✗ WorkbenchUIController imports
  ✗ v6/ui layout/visual/component structure changes
```

### Dependency Direction

```
Runtime → Interaction Contract → Renderer → v6/ui → Qt
```

Only downward. Never upward. Runtime does not know v6/ui exists.

### Artifacts

| Artifact | Lineage | Status |
|----------|---------|--------|
| `v6/ui/` (22 files) | Pure UI Foundation — extracted from early Workbench | **ACTIVE** — Phase 2-B Renderer target |
| `agent_workbench/ui/workbench/` (32 files) | Legacy architecture validation UI | **PRESERVED** |
| `v6-agent` branch | Deprecated application-centric architecture | **ARCHIVED** |

### Lineage Distinction

`v6/ui` is the **Pure UI Foundation** — an independent Presentation Design System.
It does **not** inherit from the deprecated `v6-agent` (`UI → Controller → Agent Runtime → LLM`).

The current architecture is:

```
CENTRE Runtime → Interaction Boundary → Presentation Renderer → v6/ui → Qt
```

This is **Runtime-first, Presentation-agnostic**: UI is a Shell Renderer, not an application.

### Frozen Foundation Status

`v6/ui` is now a **Frozen Foundation**. Changes allowed:
- Visual refinement (colors, spacing, accessibility)
- UI Capability API additions (e.g., `ChatArea.reset_workspace()`)

Changes forbidden:
- Runtime dependency, Agent lifecycle, Session ownership, Model ownership
- Business logic inside widgets
- Layout/component structure changes per Renderer need

### Related Documents

- [v6/UI_FOUNDATION.md](./v6/UI_FOUNDATION.md) — Formal freeze contract
- [ARCHITECTURE_BOUNDARY.md](./ARCHITECTURE_BOUNDARY.md) — Agent construction rules
- [docs/v6/architecture-boundaries.md](./docs/v6/architecture-boundaries.md) — Architecture boundary spec
- [.project/decisions/ADR-001-shell-contract-freeze.md](./.project/decisions/ADR-001-shell-contract-freeze.md) — Shell Contract ADR
- [.project/decisions/ADR-002-phase-2c-presentation-rfc.md](./.project/decisions/ADR-002-phase-2c-presentation-rfc.md) — Phase 2-C Presentation RFC

## V6 Framework Core Foundation Baseline

> **`v6.8.0-alpha` is the V6 Framework Core Foundation Baseline** — a shared, frozen core for the V6 Runtime platform, not a regular feature release or archive.

```
v6-dev
  |
  v6.8.0-alpha  ← Framework Core Foundation Baseline
      |
      +---- v6-core   (Runtime Kernel — bug fixes only)
      |
      +---- v6-service (Runtime Service Architecture)
      |
      +---- v6-agent   (Agent Application — current active)
```

| 分支 | 定位 | 允许变更 |
|---|---|---|
| `v6-core` | Framework Core Foundation | 只修 bug，不增加功能；冻结 RuntimeContext、Engine Protocol、EventBus、CapabilityRegistry、Trace、Replay、Orchestrator、PlannerLoop。 |
| `v6-service` | Runtime Service Architecture | Memory、Prompt、Model Adapter、Tool Adapter、Knowledge Adapter 等能力层。 |
| `v6-agent` | Agent Application | Coding / Research / Trading / Desktop / Workflow 等具体 Agent 类型、Persona、Policy、Workflow、UI、MCP 入口。 |

**合并方向（强制单向）**：

```
v6-core  ──merge──►  v6-service  ──merge──►  v6-agent
```

- `v6-core` 的 bug fix 向下合并到 `v6-service` 和 `v6-agent`。
- `v6-service` 的能力向下合并到 `v6-agent`。
- **禁止反向合并**：`v6-agent`、`v6-service` 不得反向合并入 `v6-core`；`v6-agent` 不得反向合并入 `v6-service`。

## V6 Runtime Kernel Freeze Series

> **v6.9.x collectively forms the V6 Runtime Kernel Freeze Series.**

这一系列版本的目标不是提供新能力，而是在集成生产级 Provider、真实 LLM、MCP、Workflow Runtime 之前，把 Runtime 内核的**协议、边界和职责彻底冻结**。进入 v6.10 及以后，所有 AI 能力都将建立在这套已经稳定的 Runtime Kernel 之上，而不是一边扩展功能、一边反复修改底层协议。

### 六层 Runtime Kernel

```text
Request
    ↓
Planning
    ↓
Task
    ↓
Capability
    ↓
Engine
    ↓
Provider
```

层级说明见 [`docs/v6/runtime-kernel-spec.md`](./docs/v6/runtime-kernel-spec.md)。

### v6.9.x 历史定位

| 版本 | 冻结的契约 |
|---|---|
| v6.9.2-alpha | Task Contract — `Task` 五字段固定，`submit_task(Task)` 成为唯一入口。 |
| v6.9.3-alpha | Manager / Capability Tree Boundary — Capability 从 metadata 提升为 Runtime 一级对象。 |
| v6.9.4-alpha | Runtime Decision Layer Contract — `RuntimeDecision` 成为 Runtime Control Plane 稳定 ABI。 |
| v6.9.5-alpha | Interaction Boundary Layer Contract — `RuntimeRequest` / `InteractionEvent` 统一入口与输出协议。 |
| v6.9.6-alpha | Capability Runtime Contract — `CapabilityDefinition` / `CapabilityContext` / `CapabilityState` / `CapabilityRegistry` 运行时索引冻结。 |

### 后续路线：Agent Workbench 生态

```text
Foundation Runtime      ← v6.9.6-foundation 已冻结
        ↓
Agent Workbench         ← v6.10.x 当前阶段：GUI / Provider / Tool / Skill
        ↓
Provider Ecosystem
        ↓
Tool Ecosystem
        ↓
Skill Ecosystem
        ↓
Workflow Ecosystem
        ↓
Knowledge & Memory
        ↓
Digital Identity
        ↓
   （未来）
    Gateway             ← 最后才做，管理多个成熟 Agent
```

优先级：

| 梯队 | 优先级 | 内容 |
|---|---|---|
| 第一梯队 | ⭐⭐⭐⭐⭐ | GUI、Provider、Tool Runtime、Skill Registry |
| 第二梯队 | ⭐⭐⭐⭐ | Workflow、Memory、Knowledge |
| 第三梯队 | ⭐⭐⭐ | MCP、Browser、External Service、Plugin Marketplace |
| 第四梯队 | ⭐⭐ | Gateway、Distributed、Remote Runtime |

## V6 全新主线声明

> **V6.0.0-alpha marks the beginning of the independent V6 Runtime architecture line.**

- V6 为从零重写的 Agent Runtime 平台，与 V5、V4 在代码层面完全隔离，仅在经验和设计思路上提取可复用部分。
- **`v6.0.0-alpha` 是 V6 独立产品线的公开立项标签**，代表 V6 作为第二代独立架构线正式对外发布。
- **`v6.5.8-alpha` 保留为内部迁移标签**，记录 Step 4 在 `v5-dev` 上的最终技术成果；它不参与 V6 产品线后续演进，仅作为历史追溯参考。
- **`v5-dev` 已冻结归档**：`v6.5.8-alpha`（Step 4）为 `v5-dev` 上最后一个 V6 相关提交。
- **禁止反向合并**：不允许将 V5 / V4 / `v6-agent` 代码合并入 `v6-core`；`v6-core` 的修复向下合并到 `v6-service` 和 `v6-agent`。
- **版本号规则**：V6 版本号独立演进，格式为 `v6.x.y-alpha`，与 V5 的 `v5.x.y-alpha` 互不干扰。
- **设计铁律**：
  1. `RuntimeContext` 是 Runtime 唯一公共协议（Public Runtime Protocol）。
  2. Engine、Service、Controller、Gateway 的公共接口统一接收 `RuntimeContext`。
  3. Adapter 属于 Application Layer，不保存状态、不做业务，只做 `Input → Context → Runtime → Output` 转换。
  4. 所有状态收敛到 `RuntimeContext`；ChatMessage、ToolCall、MemoryEntry、Metrics 等仅为 `RuntimeContext` 的资源。

## 项目概要
v6.9.3-alpha 进入 **Multi-Capability Runtime & Manager Routing** 实施阶段：Capability 从 metadata 提升为 Runtime 一级对象，位于 `agent_workbench/runtime/capability/`；建立以 `assistant` 为根的能力树（Tree，非 Graph），由 `AgentWorkbenchRuntime` 单例持有 `CapabilityRegistry`；`ManagerRuntime` 取代 `AgentManager` 成为默认 Manager，完成 `UserRequest → CapabilityMatch → Task` 路由；`CapabilityRouter` 按 `Task.metadata["capability_id"]` 解析 engine_capability；Orchestrator 支持 `metadata["capability_chain"]` 静态链顺序执行；UI Bridge 后半段只读接入。Task 五字段保持不变，所有扩展写入 metadata。本版本为单一 Agent 实例的能力操作系统奠基，不进入 Multi-Agent / Agent Memory / MCP 大规模接入。

v6.9.2-alpha 完成 **Single Agent Runtime Foundation**：定义稳定的 `Task` 数据模型（`id` / `capability` / `payload` / `metadata` / `created_at`），`submit_task(Task)` 成为 Runtime 唯一入口，`chat()` 降级为 Adapter 包装；新增 `UserRequest` 协议对象与 `Manager` 协议，`AgentManager` 实现 `UserRequest → Task` 解析，Runtime 不再感知 Chat/Prompt 等输入形式；`Orchestrator` 合并 `Task.metadata` 到 `RuntimeContext`；Workbench UI 骨架升级为 `WorkbenchHost → Workbench → NavigatorHost / WorkspaceHost / InspectorHost / StatusBarHost / CommandBarHost`，Host 负责 mount / replace / dispose 生命周期，WorkbenchUIController 与测试均通过 Host 接口交互，不再直接依赖 Qt Widget 内部属性；V6 全量测试 `pytest tests/v6/` 176/176 通过，Workbench 测试 `pytest agent_workbench/tests/` 34/34 通过，合计 210/210 通过。

v6.9.1-alpha 完成 **Runtime Observability Foundation**：将 RuntimeTrace 升级为分层事件模型（Task/Capability/Engine/Provider/Execution/Stream/Request），事件语义不再绑定 LLM Streaming，支持未来多模态扩展；新增 `CapabilityRouter` 作为 Runtime 组件发射 `capability.resolved` 事件；`Orchestrator` 统一发射 `engine.selected` 事件；`WorkbenchLLMEngine` 发射 `execution.started` / `provider.selected` / `request.sent` / `first.token` / `chunk.received` / `stream.finished` / `execution.finished` 结构化事件；`EventBus` Trace Hook 改为 `publish` 阶段同步写入，保证事件顺序与 `task.finish` 不丢失，同时保持订阅者回调异步；新增 `TraceEventRegistry` 与 `TraceWorkspaceItem`，UI 通过事件注册表动态渲染图标/标签/状态，不维护硬编码映射；新增 Trace 事件顺序、父子关系、Workspace 接收等测试；V6 全量测试 `pytest tests/v6/` 176/176 通过，Workbench 测试 `pytest agent_workbench/tests/` 20/20 通过，合计 196/196 通过。

v6.9.0-alpha 完成 **Agent Workbench Single Instance**（V6 框架内第一个真实 Agent 产品实例）：新增 `agent_workbench/` 应用层目录，基于 v6.8.0-alpha Framework Core Foundation Baseline 构建可运行、可配置的单一 Agent 工作 bench；引入 `ConfigStore`（YAML 唯一配置源 + 内存缓存 + namespace 变更通知）、`ProfileManager`（Profile 切换/导入/导出/合并）、`ModuleRegistry`（10 个 RuntimeModule 生命周期管理）与 `AgentWorkbenchRuntime`（组合 ConfigStore/ProfileManager/ModuleRegistry/CoreRuntime，注册 WorkbenchLLMEngine/WorkbenchToolEngine）；定义 10 个 `BaseRuntimeModule`（Runtime/Session/Config/Profile/Prompt/Model/Tool/Memory/Strategy/Trace），每个模块支持 `initialize`/`apply_config`/`dispose`/`to_form`，运行态、配置态、能力态、观测态分层清晰；实现 `WorkbenchController` 作为 Application Layer 唯一入口，UI 不直接持有 Module；实现 `AgentConfigPanel` 配置面板，支持左侧模块列表 + 右侧 JSON 编辑器，满足查看/修改/保存/热更新四件事；扩展 v6 三栏高级 UI：`WorkbenchLeftPanel` 在左下角新增「设置」按钮，`WorkbenchRightPanel` 新增「配置」标签页，`WorkbenchMainWindow` 组装完整三栏，`WorkbenchUIController` 继承 v6 UIController 并复用 Session/Chat 服务，聊天请求转发给 WorkbenchController；提供 CLI/GUI 双入口 `agent_workbench/app.py`；新增 7 个 Workbench 端到端测试，验证聊天生命周期、Tool Engine、PlannerLoop 决策、ConfigStore 读写、CLI 入口；V6 全量测试 `pytest tests/v6/` 175/175 通过，Workbench 测试 `pytest agent_workbench/tests/` 7/7 通过，合计 182/182 通过。

v6.8.0-alpha 完成 V6 Framework Core Foundation Baseline（共享核心框架基座）：新增 `v6/runtime/decision.py` 定义 `DecisionAction`/`Decision` 模型；新增 `v6/runtime/decision_policy.py` 定义 `DecisionPolicy` 与 `RuleBasedDecisionPolicy`；新增 `v6/runtime/planner_loop.py` 实现 `PlannerLoop`（observe/decide/evaluate/plan），补齐 Runtime 调度决策机制；升级 `v6/runtime/orchestrator.py` 集成 PlannerLoop，按 Decision 选择 Engine 执行；升级 `v6/runtime/runtime.py` 使 `AgentRuntime` 默认构造 `PlannerLoop` 并注入 Orchestrator；`Orchestrator._ensure_context()` 自动从 `ChatTask` 提取 `task_type` 与 `messages` 供策略匹配；新增 `tests/v6/test_v6_planner_loop.py` 共 10 个测试覆盖决策、事件发布、Orchestrator 集成与 PlannerLoop/Trace 隔离；至此 V6 核心控制面完整闭环：统一入口（RuntimeContext/Task）、统一协议（Engine）、统一通信（EventBus）、能力发现（CapabilityRegistry）、执行追踪（RuntimeTrace/Replay）、任务编排（Orchestrator）、调度决策（PlannerLoop/Decision）；明确 `PlannerLoop` 是 Runtime 决策机制，`PlannerEngine` 是八大 Engine 之一的能力组件，二者职责分离；该版本作为后续 Agent / Service / Adapter 开发的长期依赖基线；V6 全量测试 175/175 通过。

## v6.14.0-alpha 当前阶段：Agent Workbench OS — Presentation / Shell Integration

```
Phase 0  Architecture Stabilization        ✅ 2026-07-19
         Frozen Zone + Boundary Rules
         ├── v6/runtime/           (19 文件 Frozen)
         ├── capability/           (CapabilityRuntimeContract)
         └── architecture-boundaries.md

Phase 1  Presentation Layer                ✅ 2026-07-20
         ├── Phase 1-A  Presentation Foundation
         │   ├── view_models/    (agent/capability/conversation/memory/settings)
         │   └── adapters/       (5 个 Adapter)
         │
         ├── Phase 1-B  Shell Contract Freeze     ✅ 2026-07-21
         │   ├── shell/protocol.py  (ShellBoundary + 6 模型)
         │   ├── shell/transformers/ (3 个转换器)
         │   ├── shell/integration.py (PresentationPipeline)
         │   └── ADR-001-shell-contract-freeze.md
         │
         └── Phase 1-C  Runtime Adapter Integration   ⏳ Next
             └── 第一条黄金路径：Session → NavigationGroup

Phase 2  Workbench Integration             待定
Phase 3  Multi-Renderer                    待定
```

> **Shell 不是 UI。Shell 是 Agent Workbench OS 的 Renderer-Independent Presentation Contract。**
>
> UI 只是 Shell 的一种 Renderer。未来 Desktop UI / Web UI / Mobile UI / CLI / Embedded Component 全部通过 ShellProtocol 接入。
>
> 详见 [.project/decisions/ADR-001-shell-contract-freeze.md](.project/decisions/ADR-001-shell-contract-freeze.md)

---

## 历史阶段

**v6.11.0-alpha：Metadata-driven Workbench**（在 `v6-agent` 分支执行）：

v6.9.x Runtime Kernel Freeze Series 已收官，`v6.9.6-foundation` 成为长期基线。v6.10.0 完成了 **Configuration-Driven Workbench Loop**：Provider / MCP / Skill / Workflow / Prompt / Memory 全部可通过 Workbench UI 的「+」按钮注册到 ConfigStore，对应 Registry 自动 Reload，Navigator / StatusBar / Inspector 实时刷新。

v6.11.x 起，项目重心从 **Runtime 演进** 转向 **Workbench 演进**。Runtime 是内核，Workbench 才是产品。每一阶段只回答一个问题：

> **Workbench 今天比昨天多支持一种什么类型的对象，而无需修改代码？**

v6.11.0 先让所有已支持对象具备统一的 **Metadata** 描述能力，使 Runtime 能一致地认识 Provider / MCP / Skill / Workflow / Prompt / Memory，为后续 Schema 自动生成 UI 奠定基础。

### v6.11.x 目标

第一梯队（⭐⭐⭐⭐⭐，立即执行）：

- **Metadata Contract**：定义并统一 `BaseRuntimeModule.metadata()` 返回结构，覆盖 `id` / `type` / `name` / `icon` / `properties` / `statistics` / `actions`。
- **MetadataAdapter**：将 `ModuleMetadata` 转换为 `PresentationModel`，供 Navigator / Inspector / StatusBar 统一消费。
- **Runtime Module Metadata 补齐**：Provider / MCP / Skill / Workflow / Prompt / Memory 全部返回符合 Contract 的 Metadata。
- **UI 去硬编码**：Navigator、Inspector、StatusBar 不再按类型维护私有映射，全部通过 `PresentationModel` 渲染。

### 现在不做的事

- **Schema-driven UI**：v6.12.x 再做。当前阶段只统一 Metadata 描述，不自动生成配置控件。
- **Runtime Executors**（ProviderRuntime / ToolRuntime / SkillRuntime）：放到 Schema Foundation 之后，避免每新增一个 Runtime 就要重写一套配置页面。
- **新增 Runtime 类型**：Knowledge / Persona / Browser / Plugin / Gateway / Digital Identity 暂时不接。

### 开发约束

1. **Runtime Kernel 不再扩展**：不允许新增 Runtime-level 模块；所有新能力通过 Capability Runtime Contract 接入。
2. **Metadata 平台无关**：`metadata()` 返回的数据必须能被 Qt、Web、CLI、REST API 同时消费，禁止出现任何 UI 概念。
3. **先 Metadata，后 Schema，再 Plugin**：不跳过阶段，不在 Metadata 未统一时直接做 Schema。
4. **所有实现必须能在 Workbench 中验证**：未完成 Workbench 集成的功能不算完成。
5. **不接 Gateway / Distributed / Remote Runtime / Digital Identity**：第四梯队内容全部冻结到未来阶段。
6. **不接 MCP / Browser / External Service / Marketplace**：第三梯队内容在第二梯队跑通后再启动。

### Workbench 演进路线图

```text
v6.9.x         Runtime Foundation                         ✅
                      ↓
v6.10.0        Configuration-driven Workbench           ✅
                      ↓
v6.11.x        Metadata-driven Workbench                ← 当前
                      ↓
v6.12.x        Schema-driven Workbench
                      ↓
v6.13.x        Plugin-driven Workbench
                      ↓
（未来）        Marketplace / Digital Identity / Gateway
```

阶段定义：

- **Metadata-driven**：所有对象都有统一的描述能力。Runtime 通过 `metadata()` 认识对象。
- **Schema-driven**：所有对象的配置都由 Schema 描述，Dialog / Inspector / JSON Editor / Validator / Import / Export 全部自动生成。
- **Plugin-driven**：放置一个 Plugin，Workbench 自动发现、读取 Metadata 与 Schema、生成 UI、注册 Runtime，做到零代码扩展。

### 优先级重排

| 优先级 | 阶段 | 内容 | 原因 |
|--------|------|------|------|
| 1 | v6.12.x | Schema Foundation | 没有 Schema，每新增 Runtime 都要重写配置 UI |
| 2 | v6.13.x 之前 | Runtime Executors | ProviderRuntime / ToolRuntime / SkillRuntime |
| 3 | 当前 | Workbench UI 去硬编码 | Navigator / Inspector / StatusBar 通过 PresentationModel 渲染 |

### 最高级设计约束

> **Capability Runtime Contract Freeze 只定义 Runtime 对 Capability 的契约，不定义任何具体能力行为。任何图片、视频、浏览器、MCP、本地 Agent、远程 Agent 等新增能力，都必须通过注册 `CapabilityDefinition` 和实现 `CapabilityContext` 来接入，不允许为单个能力增加专用 Runtime 流程。**

### V6 Architecture Constitution（架构宪章）

> 本宪章具有最高优先级，高于普通设计文档与实现细节。任何代码评审、AI 生成代码、未来接手开发的人，都必须先检查是否违反本宪章，再讨论如何实现。
>
> 宪章核心原则：**成熟框架真正稳定，不是因为规定了很多「应该怎么做」，而是因为规定了很多「绝对不能怎么做」。**

#### 1. Capability Metadata ≠ UI Metadata（平台无关性）

`BaseRuntimeModule.metadata()` 只能返回 **Capability Metadata**，即模块「是什么、有什么、能做什么」的纯数据描述。Metadata 必须具有 **平台无关性（Platform Agnostic）**：同一份 Metadata 应能被 Qt、Web、CLI、REST API 同时消费，无需重写。

允许出现的内容：

- `id` / `type` / `name` / `description` / `icon`
- `properties`：属性的名字、类型、当前值、可选值、是否可编辑、描述
- `statistics`：运行时的只读观测值
- `actions`：模块暴露的操作名、标签、图标

禁止出现任何 UI 概念：

- `editor: slider` / `textbox` / `checkbox` / `dropdown`
- `inspector` / `property_editor` / `widget` / `dock` / `panel`
- `layout` / `section` / `tab` / `column`
- `width` / `height` / `horizontal` / `vertical` / `position`

如果 Metadata 中出现 `width: 300`、`layout: horizontal`、`editor: slider`，说明已经越界。如果 Module 开始写 `build_property_list()` / `build_actions()` / `build_statistics()` 这类为 UI 服务的方法，立即叫停并回滚。Module 只为 Runtime 负责，UI 怎么画与 Module 无关。

#### 2. 不要 RuntimeObject：Module Metadata → PresentationModel → Inspector

Runtime 与 UI 之间的翻译层必须叫 **MetadataAdapter**，输入是 `ModuleMetadata`，输出是 **PresentationModel**（例如 `PropertyPresentation` / `ActionPresentation` / `StatisticPresentation` / `ModulePresentation`），然后交给 Inspector 渲染。

禁止引入 `RuntimeObject` 这种名字，因为它会越长越像 Qt 的 `QObject`，最终滑向 `RuntimeObject → QObject → Widget` 的混合架构。也不应叫 `UI ViewModel`，因为以后 Qt、Web、CLI 都可以消费同一份 PresentationModel，它不是 Qt 专用的 ViewModel。

Runtime 的边界到 `ModuleMetadata` 为止；后面是 MetadataAdapter → PresentationModel → Inspector，全部是 UI 层。

正确数据流：

```
PromptModule
    ↓ metadata()
ModuleMetadata
    ↓ MetadataAdapter.adapt()
ModulePresentation / PropertyPresentation / ActionPresentation
    ↓ Inspector 渲染
UI (Qt / Web / CLI)
```

#### 3. 迁移顺序：UI 先立起来，Runtime 再接

从 `ui-template` 迁移成熟 UI 资产时，顺序必须是：

1. **ui-template**：把已有的纯 UI 资产（主题、布局、组件、动画）完整迁移过来，不带业务。
2. **Workbench Skeleton**：建立 `WorkbenchHost` → `Workbench` 骨架，包含 Navigator / WorkspaceHost / Inspector / StatusBar / CommandBar。
3. **Runtime Adapter**：把 Workbench 的信号（selection_changed / property_changed / action_triggered / command_submitted）连接到 Runtime。
4. **Metadata**：让 10 个 RuntimeModule 返回 Capability Metadata。
5. **Property Inspector**：让 Inspector 根据 PresentationModel 动态渲染属性编辑器。

原因：不要一边设计 Metadata 一边画 UI。UI 框架和交互骨架必须先稳定，Runtime 再用 Metadata 往里填内容。

#### 4. Workspace 不拥有任何业务（WorkspaceHost 原则）

`Workspace` 不是 Chat、Dashboard、Trace、Task、Editor 这些具体内容。Workspace 自己只是一个 **WorkspaceHost**，负责承载工作区内容。**Workspace 不拥有任何业务逻辑。**

所有内容都是 **WorkspaceItem**：

- Chat 是一个 WorkspaceItem；
- Trace 是一个 WorkspaceItem；
- Dashboard 是一个 WorkspaceItem；
- Task、Editor、Knowledge Graph、Workflow、Profiler 都是可注册的 WorkspaceItem。

以后增加 Knowledge、Workflow、Profiler，WorkspaceHost 一行不用改。第一版可以只实现 ChatWorkspaceItem，但 `WorkspaceHost` 的接口必须允许后续动态注册新的 WorkspaceItem 类型，不能一开始就把 Workspace 的内容写死。

#### 5. MainWindow → WorkbenchHost → Workbench

不要替换 `MainWindow`。正确的分层是：

```
MainWindow（顶层窗口，只负责 OS 级窗口行为：标题栏、缩放、关闭、菜单）
    ↓ 持有
WorkbenchHost（负责把 Workbench 装进窗口，处理 Host 级事件）
    ↓ 持有
Workbench（真正的 IDE 骨架：Navigator / WorkspaceHost / Inspector / StatusBar / CommandBar）
```

这样以后：

- Desktop：`MainWindow` → `WorkbenchHost` → `Workbench`
- Web：`Browser` → `WorkbenchHost` → `Workbench`
- Embedded：`Host` → `WorkbenchHost` → `Workbench`

Runtime 完全一样，Workbench 本身保持不变。

#### 6. UI 不保存业务状态

任何 UI 不允许保存业务状态。禁止在 UI 中写：

```python
self.selected_model = "gpt-4o"
self.current_profile = "coding"
self.runtime_enabled_tools = [...]
```

真正的业务状态必须全部在 Runtime。UI 只允许保存纯界面状态：

- `selection`：当前选中的对象 ID
- `focus`：当前获得焦点的控件
- `scroll`：滚动位置
- `expanded`：树节点展开状态
- `splitter_sizes`：面板尺寸

当用户修改属性时，UI 只发 Signal，Runtime 自己改；Runtime 改完后通过 EventBus 通知 UI 刷新。

#### 7. Runtime Module 之间禁止互相 Import

任何 Runtime Module 不允许直接 import 另一个 Runtime Module。禁止：

```python
# PromptModule.py
from agent_workbench.runtime.modules.memory_module import MemoryModule
```

模块间通信必须通过：

- **EventBus**：发布/订阅事件；
- **Interface**：模块间只依赖抽象接口；
- **Registry**：通过 ModuleRegistry 查询其他模块的能力或 Metadata。

这条规则保证模块之间零编译耦合，未来替换、升级、测试单个模块时不会影响其他模块。

#### 8. 新需求优先扩展 Metadata，而不是新增 UI

任何新需求进来，第一反应该是：「它能不能通过扩展现有 Metadata 解决？」而不是「我要新增一个什么 Panel / Page / Dialog」。

例如：

- 需要显示 Memory Size → 在 MemoryModule 的 `metadata()` 里增加 `statistics`；Inspector 自动显示，不要新增 MemoryPanel。
- 需要 Provider 切换 → 在 ModelModule 的 `metadata()` 里把 Provider 做成 `select` 类型的 Property；Inspector 自动生成下拉框。
- 需要 Token 统计 → 在 SessionModule 的 `metadata()` 里增加 `statistics`；StatusBar 自动刷新。

如果 Metadata 无法表达该需求，再考虑是否引入新的 PresentationModel 字段或新的 UI 组件。但绝对禁止为某个模块单独写一个专属 Panel。

### 验收标准（Framework Rule，适用于任何 Runtime Module）

新增任何 Runtime Module（Workflow / Knowledge / Plugin / MCP / Scheduler / 其他）时，正确答案必须满足：
1. 在 `ModuleRegistry` 注册 Module；
2. 实现 `metadata()` 返回 Capability Metadata（`id` / `type` / `name` / `properties` / `statistics` / `actions`）。

完成。Navigator 会自动出现新模块，Inspector 会自动渲染其属性、统计和操作，StatusBar 会自动读取相关 statistics。

不应出现：新增 `XXXPanel` / `XXXController` / `XXXInspector` / `XXXNavigator` / `XXXStatus`。如果出现其中任何一个，说明架构又退回到了「堆页面、堆功能」的模式，必须叫停并重构。

简化为一句话：**增加任何 Runtime Module，只允许改两处；任何为该模块单独写的 UI 代码都是犯规。**

## 历史里程碑
v6.9.0-alpha 完成 Agent Workbench Single Instance（V6 框架内第一个真实 Agent 产品实例）：新增 `agent_workbench/` 应用层目录，基于 `v6.8.0-alpha` Framework Core Foundation Baseline 构建可运行、可配置的单一 Agent Workbench；引入 `ConfigStore`（YAML 唯一配置源 + 内存缓存 + namespace 变更通知）、`ProfileManager`（Profile 切换/导入/导出/合并）、`ModuleRegistry`（10 个 RuntimeModule 生命周期管理）与 `AgentWorkbenchRuntime`（组合 ConfigStore/ProfileManager/ModuleRegistry/CoreRuntime，注册 WorkbenchLLMEngine/WorkbenchToolEngine）；定义 10 个 `BaseRuntimeModule`（Runtime/Session/Config/Profile/Prompt/Model/Tool/Memory/Strategy/Trace），每个模块支持 `initialize`/`apply_config`/`dispose`/`to_form`，运行态、配置态、能力态、观测态分层清晰；实现 `WorkbenchController` 作为 Application Layer 唯一入口，UI 不直接持有 Module；实现 `AgentConfigPanel` 配置面板，支持左侧模块列表 + 右侧 JSON 编辑器，满足查看/修改/保存/热更新四件事；扩展 v6 三栏高级 UI：`WorkbenchLeftPanel` 在左下角新增「设置」按钮，`WorkbenchRightPanel` 新增「配置」标签页，`WorkbenchMainWindow` 组装完整三栏，`WorkbenchUIController` 继承 v6 UIController 并复用 Session/Chat 服务，聊天请求转发给 WorkbenchController；提供 CLI/GUI 双入口 `agent_workbench/app.py`；新增 7 个 Workbench 端到端测试，验证聊天生命周期、Tool Engine、PlannerLoop 决策、ConfigStore 读写、CLI 入口；V6 全量测试 `pytest tests/v6/` 175/175 通过，Workbench 测试 `pytest agent_workbench/tests/` 7/7 通过，合计 182/182 通过；PyInstaller 打包 `agent_workbench.spec` 生成 `dist/AgentWorkbenchV6.exe`，CLI/GUI 均可独立启动；`main.py` 已切换为 `agent_workbench.app` 入口。v6.8.0-alpha 完成 V6 Framework Core Foundation Baseline（共享核心框架基座）：新增 `v6/runtime/decision.py` 定义 `DecisionAction`/`Decision` 模型；新增 `v6/runtime/decision_policy.py` 定义 `DecisionPolicy` 与 `RuleBasedDecisionPolicy`；新增 `v6/runtime/planner_loop.py` 实现 `PlannerLoop`（observe/decide/evaluate/plan），补齐 Runtime 调度决策机制；升级 `v6/runtime/orchestrator.py` 集成 PlannerLoop，按 Decision 选择 Engine 执行；升级 `v6/runtime/runtime.py` 使 `AgentRuntime` 默认构造 `PlannerLoop` 并注入 Orchestrator；`Orchestrator._ensure_context()` 自动从 `ChatTask` 提取 `task_type` 与 `messages` 供策略匹配；新增 `tests/v6/test_v6_planner_loop.py` 共 10 个测试覆盖决策、事件发布、Orchestrator 集成与 PlannerLoop/Trace 隔离；至此 V6 核心控制面完整闭环：统一入口（RuntimeContext/Task）、统一协议（Engine）、统一通信（EventBus）、能力发现（CapabilityRegistry）、执行追踪（RuntimeTrace/Replay）、任务编排（Orchestrator）、调度决策（PlannerLoop/Decision）；明确 `PlannerLoop` 是 Runtime 决策机制，`PlannerEngine` 是八大 Engine 之一的能力组件，二者职责分离；该版本作为后续 Agent / Service / Adapter 开发的长期依赖基线；V6 全量测试 175/175 通过。
v6.7.0-alpha 完成 Step 5.4 Runtime Orchestration Foundation：新增 `v6/runtime/orchestrator.py` 实现 Task Lifecycle State Machine（CREATED→PLANNING→EXECUTING→COMPLETED/FAILED），通过 EventBus 事件驱动流程，使用 CapabilityRegistry 选择 Engine；升级 `v6/runtime/runtime.py` 使 `AgentRuntime` 持有 `Orchestrator`；V6 全量测试 166/166 通过。v6.6.2-alpha 完成 Step 5.3 Runtime Trace Replay Foundation：新增 `v6/runtime/replay.py` 实现 `ReplayRecord`/`ReplayLog`/`ReplayService`，支持从 EventBus 订阅事件生成回放记录；V6 全量测试 159/159 通过。v6.6.1-alpha 完成 Step 5.2 Engine Capability Registry：新增 `v6/runtime/capability_registry.py` 实现能力注册、查询、排序与选择；V6 全量测试 144/144 通过。v6.6.0-alpha 完成 Step 5.1 Runtime Event Bus Foundation：升级 `v6/runtime/event_bus.py` 为 Runtime 内部神经系统，支持 RuntimeEvent schema、异步 dispatch、Trace Hook；V6 全量测试 130/130 通过。v6.5.8-alpha 完成 Step 4 八大 Engine Runtime 骨架：新增 `v6/runtime/engines/base.py` 定义 `BaseEngine` 统一生命周期；新增 `llm.py`/`tool.py`/`memory.py`/`planner.py`/`workflow.py`/`code.py`/`vision.py`/`knowledge.py` 八大 Engine 空壳；`RuntimeContext` 保留单 `RuntimeContext` 入口，`EngineManager.execute(name, ctx)` 统一调度；新增 `tests/v6/test_v6_runtime_kernel.py` 验证 Engine 动态发现、生命周期一致、Trace Timeline、Planner 编排 LLM/Tool；清理旧 `v6/runtime/engines/` 不兼容实现与 `tests/v6/test_v6_engines.py`；V6 全量测试 130/130 通过。v6.5.7-alpha 完成 Step 3 Engine Protocol 与 EngineManager 生命周期：新增 `v6/runtime/engine_state.py` 定义 `EngineState` 枚举（CREATED→LOADING→LOADED→INITIALIZING→READY→RUNNING→STOPPING→STOPPED，外加 DEGRADED/ERROR）；新增 `v6/runtime/engines/protocol.py` 定义 `Engine` Protocol、`EngineDescriptor`（含 dependencies/instance）与 `EngineNotReadyError`；`RuntimeContext` 新增 `request` 字段作为 Engine 请求载荷容器；重构 `v6/runtime/engine_manager.py` 支持完整生命周期（register/load/initialize/health_check/execute/shutdown）与自动 Trace 记录；Engine 接口统一为单 `RuntimeContext` 入口 `execute(ctx)`，避免 request/ctx 双权威源；新增/更新 Engine 相关测试 26 个；V6 全量测试 144/144 通过。v6.5.6-alpha 推进 Step 2 Trace + Metrics 联动：扩展 `v6/runtime/trace.py` 的 `TraceStep`，新增 `duration_ms`/`tokens`/`cost`/`tool_time_ms` 字段；`RuntimeTrace.add()` 支持显式传入指标或从 `RuntimeMetrics` 自动提取；新增 `timed_step` 上下文管理器，自动计时并在退出时抓取 metrics，形成 Task Execution Timeline；扩展 `tests/v6/test_v6_trace.py` 新增 9 个联动测试；V6 全量测试 125/125 通过。v6.5.5-alpha 继续夯实 V6.5 Runtime Foundation Layer：明确阶段定位为“Runtime Foundation Layer”而非 Kernel；新增 `v6/runtime/state_machine.py` 定义 `RuntimeStateMachine`，固化 `RuntimeState` 生命周期迁移规则（CREATED→QUEUED→RUNNING→{WAITING/PAUSED/CANCELLED/COMPLETED/FAILED}，FAILED→QUEUED 支持重试，COMPLETED/CANCELLED 为终态），并新增 `tests/v6/test_runtime_state_machine.py` 覆盖 10 个迁移场景；V6 全量测试 116/116 通过。v6.5.4-alpha 推进 Runtime Kernel 预备层：新增 `v6/runtime/metrics.py` 定义 `RuntimeMetrics` 统一统计接口（token/latency/tool_time/cost/retry 等），新增 `v6/runtime/result.py` 定义 `RuntimeResult` 统一输出协议（answer/files/images/artifacts/error/status 等）；`RuntimeContext.metrics/result/status` 从裸 dict/字符串升级为 `RuntimeMetrics`/`RuntimeResult`/`RuntimeState` 枚举，snapshot/restore/clone/reset 全面兼容新类型；`AgentRuntime` 统一使用 `RuntimeState` 枚举设置任务状态；新增 `v6/runtime/engine_manager.py` 统一管理 Engine 注册与获取，避免 Runtime 直接 new Engine，并新增 `tests/v6/test_v6_engine_manager.py` 覆盖注册/获取/注销/运行行为；`trace.py` 补回 `Enum` 导入，`tests/v6/test_v6_trace.py` 改用 `TraceEvent`/`RuntimeState` 枚举断言；`docs/v6/SPEC.md` 将 RuntimeTask 四对象模型升级为五对象模型，新增 8.17/8.18/8.19 三节阐述 RuntimeMetrics/RuntimeResult/RuntimeState 设计原则；V6 全量测试 106/106 通过。v6.5.3-alpha 建立 Runtime Trace 基础能力：`RuntimeContext` 新增 `trace` 与 `result` 字段，每个 Task 自带执行历史；新增 `v6/runtime/trace.py` 定义 `RuntimeTrace`、`TraceStep` 与 `ReplayPlayer`，记录 `Task → Phase → Engine/Service/Tool → Finish` 全过程；`AgentRuntime` 自动记录任务生命周期（task_start / handler_dispatch / task_finish / task_error），`EchoHandler` 与 `LocalRuntimeAdapter` 记录 Engine / Adapter 步骤；`ReplayPlayer` 可按 trace 重放事件，支持调试与审计；`docs/v6/SPEC.md` 新增 Runtime Trace 原则与 RuntimeTask 四对象演进方向；V6 全量测试 99/99 通过。v6.5.2-alpha 完成 UIController 与 RuntimeAdapter 的 Application Boundary 集成：`AgentRuntime` 支持从 `Task.payload` 接收并使用已有的 `RuntimeContext`；`EchoHandler` 优先从 `ctx.messages` 读取输入；`UIController` 移除对 `AgentRuntime` 的直接依赖，改为依赖 `IRuntimeAdapter`，通过 `LocalRuntimeAdapter` 提交 `RuntimeContext`、订阅事件、取消任务；新增 `test_adapter_submit_propagates_context` 验证上下文经 Adapter 透传后状态一致；V6 全量测试 91/91 通过。v6.5.1-alpha 深化 V6 Runtime 协议与 Service 层改造：`RuntimeContext` 新增 `new()` 工厂方法，由 Runtime Task 自动生成 `task_id` 并初始化 Runtime Facts；`ConfigService` / `SessionService` / `ChatService` 统一为 `(ctx)` 输入接口，彻底移除 legacy 方法；`UIController` 全面改用 `RuntimeContext.new()` 构造上下文；`docs/v6/SPEC.md` 补充 Runtime Interface Principle、RuntimeContext 作为唯一 Public Runtime Protocol、Adapter Application Boundary 及 `RuntimeContext.new()` Task 语义等铁律；修复 `test_v6_ui_contract.py` 首行 docstring 语法错误；V6 全量测试 90/90 通过。AI Agent 工作台是一款基于 PySide6 的桌面端 AI 助手，支持三种手动模式（Ask/Plan/Craft），集成 LLM 推理、系统命令、量化分析、网页抓取、剪贴板管理等能力。v5.0.23-alpha 修复 `v5/service/chat_worker.py` 中 `AgentWorker.TOOL_DEFINITIONS` 属性错误，为 v4 归档区创建独立打包入口 `v4/v4_main.py` + `v4/AgentWorkbenchV4.spec` + `v4/scripts/rebuild_v4.ps1`，实现 v5 与 v4 并行打包并分别生成桌面快捷方式「AI Agent Workbench V5」和「AI Agent Workbench V4」；验证 `dist/AgentWorkbench/` 与 `dist/AgentWorkbenchV4/` 均可独立启动。v5.0.22-alpha 补充 `.gitignore`，将 `.reference/`、`.scripts/`、`review/` 等本地参考/调试/归档目录排除在版本控制外，保持 `git status` 干净。v5.0.21-alpha 完成工作区整理与文档同步：修正 `config.yaml` 版本号为 v5.0.20-alpha，统一以 `docs/` 为正式文档目录并在根目录新建 `README.md` 指向 docs/；将 `AgentWorkbench.spec` 与旧 `ui/`、`resources/`、`blueprints/`、`tests/test_v4_*.py` 等历史文件归档到 `v4/legacy/`、`v4/tests/`、`docs/archive/blueprints/`；清理 `docs/*.bak` 与空目录，同步根目录和 docs/ 下 `CHANGELOG.md` / `PROJECT_BLUEPRINT.md` 版本与目录树，全量测试 272/272 通过。v5.0.20-alpha 完成 V5 剩余 5% 细节功能闭环：修复 `v5/service/adapter.py` 工具执行回调命名冲突，实现终端日志与 UI 工具卡片同步输出；`ChatArea` 按 phase 渲染 `PhasePanel` 阶段面板，支持 analyze/confirm/execute/verify/archive 五种阶段；新增工具执行、确认回调、阶段渲染、craft 模式端到端流程等 11 个测试用例，全量测试 272/272 通过；修复 `AgentWorkbench.spec` 隐藏导入（移除已删除的 `v5.model.events`，添加 `v5.service.chat_worker`）并重新打包验证 exe 可独立启动。v5.0.19-alpha 修复聊天区模式列表与引擎不一致的核心 Bug，统一由 `WorkController.manual_modes` 动态管理模式列表；新增 V5 ChatArea / Adapter / Integration 测试共 78 个用例，全量测试 319/319 通过；修复 `AgentWorkbenchV5.spec` 隐藏导入并重新打包验证 exe 可独立启动。v5.0.18-alpha 完成 V5 P6/P7 收尾归档：提交 V5 新增测试、独立打包配置与 v4 归档说明，清理调试产物，全量测试 240/240 通过。v5.0.17-alpha 完成 V5 彻底隔离 v4 方案与 P6/P7 主体整改：清理 `v5/` 全部 v4 文字残留并确认无 v4 导入，统一 Widget 层 V5 标准信号契约，修复 `ChatArea`/`RightPanel`/`MainWindow` 信号连接，补齐终端/文件/浏览器用户操作信号转发到 `WorkController`，修正 `InvisibleResizeHandle` 布局问题；新增 `tests/test_v5_service.py`、`test_v5_controller.py`、`test_v5_smoke.py` 共 15 个用例；新增 `AgentWorkbenchV5.spec` 独立打包配置，新增 `v4/README.md` 标注归档废弃。v5.0.13-alpha 修复打包后浏览器标签不可用的问题：在 AgentWorkbench.spec 中显式打包 QtWebEngineProcess.exe、resources、qtwebengine_locales，并恢复 WebChannel/WebSockets/Sql 依赖，exe 内浏览器可正常加载 Bing 页面；v5.0.12-alpha 完成 UI 完全移植工程最终完整性检查与存档：复核 P10 旧 UI 清理与 PyInstaller 打包验证，完成 P11 `v4-refactor` 旧 UI 线路最终归档并推送 `v4.0.11-alpha` 归档标签，真实 GUI 验证三栏完整显示、无旧 UI 残留，全量测试 225/225 通过；v5.0.11-alpha 完成 P9 全量冒烟与集成测试验证及 UI 硬编码清理：清理 'v4 架构升级' 等旧 UI 硬编码文本，实现聊天区标题动态化；v5.0.9-alpha 完成新 UI 完全移植与旧 UI 清理；v5.0.8-alpha 完成 GUI 冒烟修复；v5.0.7-alpha 完成右栏真实功能回填；v5.0.6-alpha 完成持久化校验整改；v5.0.5-alpha 完成会话数据持久化与列表同步；v5.0.4-alpha 完成关键用户动作对接；v5.0.3-alpha 完成模块化骨架拆分；v5.0.2-alpha 完成 UIRenderer 与新 UI 桥接；v5.0.1-alpha 备份旧 UI 组件至 `v4/legacy/` 并标记 v5-dev 线路；v5.0.0-alpha 为 v5-dev 线路起点与新 UI 后端核心注入。v4.x 为旧 UI 完整版线路，已归档至 `v4-refactor` / `ui-template` 分支，不再维护。

## 技术栈
| 类别 | 技术 | 版本 | 用途 |
| 语言 | Python | 3.14 | 主语言 |
| UI 框架 | PySide6 | 6.21.0 | 桌面界面 (Fusion 深色主题) |
| LLM 框架 | LangChain + langchain-openai | latest | 工具调用与多模型对话 |
| 本地模型 | Ollama (OpenAI compatible) | latest | gemma2:2b / qwen3:4b 本地推理 |
| 云端模型 | DeepSeek API | V4 | deepseek-v4-flash / deepseek-v4-pro |
| 量化工具 | akshare + backtrader | latest | 股票数据 + 策略回测 |
| 交易接口 | MetaTrader5 Python API | latest | 实时报价 + 下单 |
| 打包工具 | PyInstaller | 6.21.0 | 一键生成 exe |
| 密钥管理 | python-dotenv | latest | .env 环境变量 |
| 持久化 | SQLite | built-in | 对话 / Token 追踪 |
| 配置格式 | YAML | built-in | 模式 / 工具 / 记忆配置 |

## 目录结构
```
/
├── main.py                 # 程序入口
├── AgentWorkbenchV5.spec   # PyInstaller V5 打包配置
├── requirements.txt        # Python 依赖
├── .gitignore              # Git 忽略规则
│
├── config/                 # 配置分组
│   ├── config.yaml         # 全局配置（打包后可写副本位于 exe 同级 config/）
│   ├── .env                # 环境变量（API Keys，不提交）
│   └── .env.example        # 环境变量模板
│
├── assets/                 # 资源分组
│   └── app.ico             # 应用图标
│
├── scripts/                # 脚本分组
│   ├── rebuild.ps1         # 一键打包脚本
│   ├── runtime_hook.py     # PyInstaller 运行时钩子
│   └── start.bat           # 启动脚本
│
├── docs/                   # 文档分组
│   ├── README.md           # 项目总入口（定位、启动、文件地图）
│   ├── ARCHITECTURE.md     # 架构全景（Mermaid 图 + 核心概念 + 设计决策）
│   ├── CHANGELOG.md        # AI 维护的变更日志
│   ├── PROJECT_BLUEPRINT.md # 本文件
│   └── getting-started.md  # 5 分钟上手指南
│
├── # 源码分组
├── agent_workbench/        # 【V6 第一个真实产品实例】Agent Workbench V6
│   ├── __init__.py
│   ├── app.py              # CLI/GUI 双入口
│   ├── controller.py       # Application Layer 控制器，持有 AgentWorkbenchRuntime
│   ├── adapter.py          # Workbench Runtime Adapter（预留）
│   ├── config/             # 配置资源
│   │   ├── default.yaml    # 10 模块默认 YAML 配置
│   │   └── loader.py       # 配置加载器
│   ├── runtime/            # Agent Workbench 内部 Runtime
│   │   ├── agent_runtime.py
│   │   ├── config_store.py
│   │   ├── profile_manager.py
│   │   ├── module_registry.py
│   │   └── modules/        # 10 个 RuntimeModule
│   │       ├── base.py
│   │       ├── runtime_module.py
│   │       ├── session_module.py
│   │       ├── config_module.py
│   │       ├── profile_module.py
│   │       ├── prompt_module.py
│   │       ├── model_module.py
│   │       ├── tool_module.py
│   │       ├── memory_module.py
│   │       ├── strategy_module.py
│   │       └── trace_module.py
│   ├── services/           # 能力服务（第一版下放到 Agent 层）
│   │   ├── model_provider.py
│   │   ├── echo_provider.py
│   │   ├── prompt_renderer.py
│   │   ├── python_renderer.py
│   │   ├── tool_registry.py
│   │   └── memory_service.py
│   ├── engines/            # Workbench 专用 Engine
│   │   ├── workbench_llm_engine.py
│   │   └── workbench_tool_engine.py
│   ├── ui/                 # Workbench 三栏 UI 扩展
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── left_panel.py
│   │   ├── right_panel.py
│   │   ├── config_panel.py
│   │   ├── workbench_ui_controller.py
│   │   ├── sections/
│   │   └── widgets/
│   └── tests/              # Workbench 端到端测试
│       └── test_agent_workbench.py
│
├── v6/                     # 【全新纯净主线】V6 从零重写
│   ├── __init__.py
│   ├── main_window.py      # 纯 UI 壳（仅创建 Widget + 转发事件 + 窗口行为）
│   ├── ui_controller.py    # UI 与业务唯一桥梁
│   ├── layout_manager.py   # 三栏布局/拖拽/折叠
│   ├── session_manager.py  # 会话 CRUD
│   ├── config_manager.py   # 配置管理
│   ├── runtime/            # AgentRuntime
│   │   ├── runtime.py
│   │   ├── context.py
│   │   ├── event_bus.py
│   │   ├── scheduler.py
│   │   ├── task.py
│   │   └── engines/        # Phase/Inference/Tool/Policy/Memory/Metrics
│   ├── ui/                 # 纯 UI 组件层
│   │   ├── base.py
│   │   ├── window_frame.py
│   │   ├── left_panel.py
│   │   ├── chat_area.py
│   │   ├── right_panel.py
│   │   ├── header_bar.py
│   │   ├── input_area.py
│   │   ├── chat_items.py
│   │   ├── chat_scene.py
│   │   ├── session_item.py
│   │   ├── session_group.py
│   │   ├── function_page.py
│   │   ├── tab_button.py
│   │   ├── recent_files.py
│   │   ├── more_dropdown.py
│   │   ├── terminal_widget.py
│   │   ├── file_reader_widget.py
│   │   ├── browser_widget.py
│   │   ├── apple_menu.py
│   │   └── settings_dialog.py
│   └── services/           # 业务服务
│       ├── config_service.py
│       ├── session_service.py
│       └── chat_service.py
│
├── v5/                     # 【只读归档区】V5 已冻结，不再维护
│   ├── __init__.py
│   ├── main.py             # V5 启动/引导、依赖组装
│   ├── main_window.py      # 轻量化顶层窗口（仅 UI 组装 + 单层信号转发）
│   ├── controller/
│   │   └── work_controller.py   # 全局唯一业务中枢
│   ├── service/            # V5 包装层，隔离根共享底层
│   │   ├── config_service.py
│   │   ├── session_service.py
│   │   ├── chat_service.py
│   │   └── adapter.py
│   ├── model/              # V5 标准化事件与数据模型
│   │   └── events.py
│   └── widgets/            # 纯 UI 层，禁止导入 controller/service
│       ├── base.py         # V5 主题、字体、SVG 工具
│       ├── window_frame.py # 无边框、拖拽、Apple 菜单
│       ├── left_panel.py   # 左侧功能/会话面板
│       ├── chat_items.py   # 聊天项卡片
│       ├── chat_scene.py   # 聊天图形渲染场景
│       ├── chat_area.py    # 中栏聊天区
│       ├── right_panel.py  # 右侧多标签容器
│       ├── terminal_widget.py     # 终端面板
│       ├── file_reader_widget.py  # 文件编辑器面板
│       ├── browser_widget.py      # 浏览器面板
│       ├── dropdown_selector.py   # 通用下拉选择器
│       └── settings_dialog.py     # 设置弹窗
│
├── v4/                     # 【只读归档区】旧 UI 完整版
│   ├── README.md           # 归档说明
│   ├── main_window.py      # 旧 UI 主窗口
│   ├── widgets/            # 旧 UI 控件库
│   ├── legacy/             # 更早版本 UI 备份
│   └── ...                 # 旧后端骨架（repository/orchestrator/worker 等）
│
├── agent_engine/           # 引擎层（v4/v5 共用）
│   ├── __init__.py
│   ├── agent_session.py    # 跨 Phase 复用会话
│   ├── llm_registry.py     # LLM 提供商注册与持久化
│   ├── memory_manager.py   # 会话记忆管理
│   ├── orchestrator.py     # 编排器（支持八引擎委托）
│   ├── phase_manager.py    # Phase-Driven Workflow Engine
│   └── engines/            # 八引擎模块
│       ├── __init__.py
│       ├── interfaces.py
│       ├── context_engine.py
│       ├── prompt_engine.py
│       ├── inference_engine.py
│       ├── tool_engine.py
│       ├── phase_engine.py
│       ├── memory_engine.py
│       ├── metrics_engine.py
│       └── policy_engine.py
├── tools/                  # 工具层
│   ├── __init__.py
│   ├── system.py           # 系统命令 / 文件读写 / 网络 / 剪贴板 / 通知 / 进程
│   ├── quant.py            # 股票数据 + 回测
│   ├── mt5.py              # MT5 报价 + 下单
│   ├── external_apis.py    # 财经新闻 / 宏观数据
│   └── screen.py           # 屏幕相关工具
├── core/                   # 核心基础设施
│   ├── __init__.py
│   ├── event_bus.py        # 基于 Qt Signal 的事件总线
│   └── events.py           # 强类型跨组件事件定义
├── services/               # 根共享服务层
│   ├── __init__.py
│   ├── config_service.py   # 配置读取与持久化
│   ├── session_service.py  # SQLite 对话持久化
│   ├── theme_service.py    # QSS 主题加载
│   ├── project_service.py  # 项目目录与会话关联
│   ├── activity_service.py # 活动记录持久化
│   ├── context_service.py  # 工作空间上下文
│   ├── path_resolver.py    # 路径解析
│   ├── python_resolver.py  # Python 解释器解析
│   ├── metrics_collector.py
│   ├── interpreter_service.py
│   ├── pending_queue.py
│   └── task_service.py
├── workers/                # 后台线程
│   ├── __init__.py
│   ├── agent_worker.py     # 流式 Agent 推理
│   ├── base_worker.py
│   ├── terminal_worker.py  # 终端命令输出捕获
│   ├── session_task.py
│   ├── task_capacity.py
│   └── task_queue.py
├── tests/                  # 测试分组（272 个 V5 单元 / 集成 / UI 测试）
│   ├── __init__.py
│   ├── integration/
│   │   └── integration_test_deepseek_metrics.py
│   ├── test_v5_service.py
│   ├── test_v5_controller.py
│   ├── test_v5_smoke.py
│   ├── test_agent_worker.py
│   ├── test_agent_session_integration.py
│   ├── test_agent_session_room.py
│   ├── test_async_tools.py
│   ├── test_context_service.py
│   ├── test_event_bus.py
│   ├── test_interpreter_service.py
│   ├── test_memory_manager.py
│   ├── test_metrics_collector.py
│   ├── test_mcp_service.py
│   ├── test_mt5_signal.py
│   ├── test_orchestrator_phase.py
│   ├── test_pending_queue.py
│   ├── test_persistence_service.py
│   ├── test_phase_manager.py
│   ├── test_self_context.py
│   ├── test_task_service_terminal.py
│   ├── test_threading_baseline.py
│   └── test_tool_gateway.py
│
└── storage/                # 运行时数据（SQLite / JSON，不提交）
    ├── conversations_v4.db
    ├── conversations.db
    ├── activities.json
    └── vector_store/
```

## 最近变更
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v6.12.0-beta.15 | 2026-07-10 | Repository Infrastructure Migration：所有项目统一 GitHub 为 Single Source of Truth（origin），Gitee 退化为可选 Release Mirror（release）；所有 Skill 重构为 Repository Generic（Archive/Mirror/Publish/Handoff/Sync Workspace/GitOps）；Mirror 从 Archive 解耦，仅在 Release 时 GitHub→Gitee 单向同步；Sync Workspace 移除 mirror fallback；新增 .project/contracts/repository_contract.md；Engineering Workflow Contract 升级为 v1.1 | docs | docs/engineering-workflow.md, .project/decisions/ai-software-engineering-workflow.md, .project/contracts/repository_contract.md, c:/Users/ThinkPad/.trae-cn/skills/*, c:/Users/ThinkPad/.trae-cn/user_rules/rule.md |

## 历史归档
| 版本 | 日期 | 描述 | 类型 | 涉及文件 |
|---|---|---|---|---|
| v6.12.0-beta.14 | 2026-07-10 | Engineering Workflow 全面冻结：五层架构（Product/Workflow/Repository/Workspace/Runtime）、五大标准 Skill（Archive/Mirror/Publish/Handoff/Sync Workspace）、Mirror 严格单向、Sync Workspace 增加 Analyze/Upgrade Plan/.sync/ 三元状态、Handoff 新增 Pending Questions、发布 docs/engineering-workflow.md 作为跨 AI 工程契约 | docs | .project/decisions/ai-software-engineering-workflow.md, docs/engineering-workflow.md |
| v6.12.0-beta.13 | 2026-07-10 | AI软件工程工作流架构决策：定义 Repository/Workspace/Product 三层模型，新增 Mirror Skill 负责 Gitee→GitHub 同步，Sync Workspace 拆分为 Repository Sync 与 Workspace Upgrade，建立 .project/ 项目知识目录并纳入 Git 跟踪 | docs | .gitignore, .project/decisions/ai-software-engineering-workflow.md |
| v6.12.0-alpha.2 | 2026-07-09 | Conversation 自动标题：新增 `agent_workbench/conversation/` Domain 层，包含 `TitleGenerator` / `RuleTitleGenerator` / `ConversationTitleService` / `ConversationService`；`ConversationService` 统一封装 Session/Chat/Title 生命周期，在第一轮 Assistant 回复完成后自动根据首条用户消息生成标题；空标题会话在 Navigator / 会话列表显示 `New Conversation`；手动重命名后自动标题不再覆盖；新增 tests/conversation/ 17 个测试；686/686 测试通过 | feat/test | agent_workbench/conversation/__init__.py, agent_workbench/conversation/title_generator.py, agent_workbench/conversation/title_service.py, agent_workbench/conversation/conversation_service.py, agent_workbench/ui/workbench_ui_controller.py, v6/ui/session_item.py, tests/conversation/test_title_generator.py, tests/conversation/test_conversation_service.py |
| v6.12.0-alpha.1 | 2026-07-09 | Metadata → PresentationModel 完整映射：扩展 PropertyPresentation / StatisticPresentation / ActionPresentation / ModulePresentation 字段，支持 ResourceDefinition 通过 `adapt_resource()` 进入 PresentationModel；UI Adapter 重命名为 `PresentationMetadataAdapter` 并显式实现 `MetadataAdapter` Protocol；PROJECT_BLUEPRINT 正式宣布 Metadata Contract 长期冻结（Additive Only）；新增 docs/v6/v6.12-task-list.md 拆分 Commit 6/7/8；新增 tests/ui/test_metadata_presentation.py 覆盖 Capability / Resource / Legacy 映射与 Protocol 合规；669/669 测试通过 | feat/test/docs | agent_workbench/ui/workbench/presentation.py, agent_workbench/ui/workbench/metadata_adapter.py, agent_workbench/ui/workbench/__init__.py, agent_workbench/ui/workbench_ui_controller.py, docs/v6/v6.11-task-list.md, docs/v6/v6.12-task-list.md, tests/ui/test_metadata_presentation.py |
| v6.11.0-beta.4 | 2026-07-09 | Provider Registry + 多模型接入：新增 ProviderRegistry 统一注册与发现模型 Provider；新增 Claude / Gemini / Kimi / Qwen / DeepSeek 五个 OpenAI 兼容 Provider；ModelModule 通过注册表动态实例化 Provider；AddProviderDialog 从 ModelModule 动态读取可用 Provider 类型；新增 tests/runtime/test_provider_registry.py 与 UI 集成测试；662/662 测试通过 | feat/test | agent_workbench/runtime/provider_registry.py, agent_workbench/services/claude_provider.py, agent_workbench/services/gemini_provider.py, agent_workbench/services/kimi_provider.py, agent_workbench/services/qwen_provider.py, agent_workbench/services/deepseek_provider.py, agent_workbench/runtime/modules/model_module.py, agent_workbench/ui/dialogs/add_provider_dialog.py, agent_workbench/ui/workbench_ui_controller.py, tests/runtime/test_provider_registry.py, tests/ui/test_provider_config_loop.py |
| v6.11.0-beta.3 | 2026-07-09 | Resource Metadata：迁移 Model / MCP / Skill / Prompt / Memory / Workflow 六个 Runtime Module 的 metadata() 到 MetadataDefinition，统一使用 ValueType 描述属性类型；新增 agent_workbench/metadata/resource.py 定义 ResourceType / ResourceConnection / ResourceDefinition，建立 Resource 跨层描述契约；新增 tests/runtime/modules/test_module_metadata.py 覆盖模块 Metadata 与 Resource Metadata；648/648 测试通过 | feat/test | agent_workbench/metadata/__init__.py, agent_workbench/metadata/resource.py, agent_workbench/runtime/modules/model_module.py, agent_workbench/runtime/modules/mcp_module.py, agent_workbench/runtime/modules/skill_module.py, agent_workbench/runtime/modules/model_module.py, agent_workbench/runtime/modules/prompt_module.py, agent_workbench/runtime/modules/memory_module.py, agent_workbench/runtime/modules/workflow_module.py, tests/runtime/modules/test_module_metadata.py |
| v6.11.0-beta.2 | 2026-07-09 | Streaming UI 对话闭环：WorkbenchUIController 引入 `_finalize_stream()` 原子化结束流式输出，修复流式结束后重复生成完整 AI 消息与错误消息重复问题；建立 `AI_CHUNK → sign_stream_chunk`、`AI_END / ENGINE_FAILED → sign_stream_end` 确定性事件映射；新增 tests/ui/test_streaming_chat_loop.py 覆盖流式路径不重复、非流式路径回退、错误唯一传播；640/640 测试通过 | feat/test/ui | agent_workbench/ui/workbench_ui_controller.py, tests/ui/test_streaming_chat_loop.py |
| v6.11.0-beta.1 | 2026-07-09 | First Real LLM Link：ManagerAI 默认将 GENERAL_QUERY 路由为 ACTION → chat Capability；CapabilityResolver 支持 GENERAL_QUERY → chat；OpenAIProvider 经 ModelModule 接入 Runtime；新增 tests/integration/test_openai_chat_loop.py 用 mock HTTP 验证完整链路、api_key 不泄露、错误传播；632/632 测试通过 | feat/test | agent_workbench/runtime/decision/manager_ai.py, agent_workbench/runtime/decision/resolver.py, tests/integration/test_openai_chat_loop.py, tests/v6/runtime/test_decision_layer.py, tests/test_controller_interaction.py |
| v6.11.0-alpha.3 | 2026-07-09 | Workbench-First B-line Pivot：ROADMAP 与 v6.11-task-list 调整时序原则，B线（产品线）优先推进单一真实 LLM 对话闭环，A线（架构线）Metadata Contract 已冻结并冻结式推进；明确 OpenAI Provider 为 v6.11.0-beta.1 唯一目标，暂缓 MCP / Workflow / Memory / Tool Calling / 多模型 | docs | docs/v6/ROADMAP.md, docs/v6/v6.11-task-list.md |
| v6.9.2-alpha | 2026-07-08 | Single Agent Runtime Foundation：Task模型固定五字段；UserRequest+Manager协议+AgentManager建立UserRequest→Task→submit_task主链；Workbench UI骨架升级为WorkbenchHost→Workbench→五大Host，Host负责mount/replace/dispose生命周期；UI与测试均调整到Host接口层；V6 176/176、Workbench 34/34通过，合计210/210 | feat/refactor/test/ui | v6/runtime/task.py, v6/runtime/user_request.py, v6/runtime/manager.py, v6/runtime/orchestrator.py, agent_workbench/controller.py, agent_workbench/runtime/agent_runtime.py, agent_workbench/services/manager.py, agent_workbench/ui/workbench/*_host.py, agent_workbench/ui/workbench/workbench.py, agent_workbench/ui/workbench/__init__.py, agent_workbench/tests/test_manager.py, tests/v6/test_v6_task.py, tests/v6/test_v6_user_request.py, agent_workbench/tests/test_agent_workbench.py, PROJECT_BLUEPRINT.md, CHANGELOG.md |
| v6.9.1-alpha | 2026-07-08 | Runtime Observability Foundation：重构RuntimeTrace为分层事件模型Task/Capability/Engine/Provider/Execution/Stream/Request；新增CapabilityRouter发射capability.resolved、Orchestrator发射engine.selected、WorkbenchLLMEngine发射execution/provider/request/stream结构化事件；EventBus Trace Hook改为publish同步写入保证顺序；新增TraceEventRegistry与TraceWorkspaceItem；新增Trace顺序/父子关系/Workspace接收测试；V6 176/176、Workbench 20/20通过 | feat/refactor/test/ui | v6/runtime/enums.py, v6/runtime/event_bus.py, v6/runtime/orchestrator.py, v6/runtime/trace.py, v6/runtime/planner_loop.py, agent_workbench/runtime/capability_router.py, agent_workbench/engines/workbench_llm_engine.py, agent_workbench/ui/workbench/trace_*.py, agent_workbench/ui/workbench_ui_controller.py, tests/v6/test_v6_*.py, agent_workbench/tests/test_agent_workbench.py, PROJECT_BLUEPRINT.md, CHANGELOG.md |
| v6.9.0-alpha | 2026-07-08 | Agent Workbench Single Instance：新增agent_workbench/应用层，含ConfigStore/ProfileManager/ModuleRegistry/AgentWorkbenchRuntime/10个RuntimeModule/WorkbenchController/Workbench Engine；扩展v6三栏UI实现AgentConfigPanel配置面板，支持查看/修改/保存/热更新；新增7个Workbench端到端测试；V6+Workbench合计182/182测试通过 | feat/test/ui | agent_workbench/**, v6/runtime/planner_loop.py, PROJECT_BLUEPRINT.md, CHANGELOG.md |
| v6.5.8-alpha | 2026-07-07 | 八大Engine Runtime骨架：新增engines/base.py及llm/tool/memory/planner/workflow/code/vision/knowledge空壳；EngineManager统一execute(name,ctx)；新增Runtime Kernel集成测试验证Engine发现/生命周期/Trace Timeline/Planner编排；清理旧engines不兼容实现；130/130测试通过 | feat/refactor/test | v6/runtime/engines/base.py, v6/runtime/engines/*.py, v6/runtime/engine_manager.py, tests/v6/test_v6_runtime_kernel.py, tests/v6/test_v6_smoke.py |
| v6.5.7-alpha | 2026-07-07 | Engine Protocol与EngineManager生命周期：新增EngineState/EngineDescriptor/EngineNotReadyError；Engine接口统一execute(ctx)；RuntimeContext新增request；EngineManager支持load/initialize/health_check/execute/shutdown并自动记录Trace；新增/更新26个Engine测试；144/144测试通过 | feat/refactor/test | v6/runtime/engine_state.py, v6/runtime/engines/protocol.py, v6/runtime/engine_manager.py, v6/runtime/context.py, tests/v6/test_engine_protocol.py, tests/v6/test_v6_engine_manager.py |
| v6.5.6-alpha | 2026-07-07 | Trace+Metrics联动：TraceStep新增duration_ms/tokens/cost/tool_time_ms；RuntimeTrace.add支持从RuntimeMetrics提取；新增timed_step上下文管理器自动计时并抓metrics；test_v6_trace.py新增9个联动测试；125/125测试通过 | feat/test | v6/runtime/trace.py, tests/v6/test_v6_trace.py |
| v6.5.5-alpha | 2026-07-07 | Runtime Foundation Layer：新增RuntimeStateMachine固化生命周期迁移规则；新增test_runtime_state_machine.py覆盖10个状态迁移场景；116/116测试通过 | feat/test | v6/runtime/state_machine.py, tests/v6/test_runtime_state_machine.py |
| v6.5.4-alpha | 2026-07-07 | Runtime Kernel预备层：新增RuntimeMetrics/RuntimeResult；RuntimeContext.metrics/result/status升级为对象与RuntimeState枚举；新增EngineManager与单元测试；trace测试改用枚举断言；SPEC升级五对象模型并新增8.17/8.18/8.19；106/106测试通过 | feat/refactor/docs/test | v6/runtime/metrics.py, v6/runtime/result.py, v6/runtime/engine_manager.py, v6/runtime/context.py, v6/runtime/runtime.py, v6/runtime/trace.py, tests/v6/test_v6_trace.py, tests/v6/test_v6_engine_manager.py, docs/v6/SPEC.md |
| v6.5.3-alpha | 2026-07-07 | Runtime Trace基础能力：RuntimeContext新增trace/result；新增v6/runtime/trace.py与ReplayPlayer；AgentRuntime/EchoHandler/Adapter记录执行步骤；SPEC补充Trace原则与RuntimeTask四对象演进；99/99测试通过 | feat/docs/test | v6/runtime/context.py, v6/runtime/runtime.py, v6/runtime/adapter.py, v6/runtime/trace.py, tests/v6/test_v6_trace.py, docs/v6/SPEC.md |
| v6.5.2-alpha | 2026-07-07 | UIController↔RuntimeAdapter集成：AgentRuntime支持从Task.payload接收RuntimeContext；UIController改为依赖IRuntimeAdapter；新增Adapter上下文传播测试；91/91测试通过 | refactor/test | v6/runtime/runtime.py, v6/ui_controller.py, tests/v6/test_v6_runtime_adapter.py |
| v6.5.1-alpha | 2026-07-07 | V6 Runtime协议深化：RuntimeContext新增new()工厂自动生成task_id；Service层统一(ctx)接口；UIController全面改用RuntimeContext；SPEC补充Runtime Interface Principle与Task语义；修复测试docstring语法错误；90/90测试通过 | refactor/feat/docs/test | v6/runtime/context.py, v6/services/*.py, v6/ui_controller.py, tests/v6/*.py, docs/v6/SPEC.md |
| v6.0.0-alpha | 2026-07-07 | V6项目启动与架构规格：判定V5失败并归档冻结，启动V6从零重写；建立V6独立目录与架构文档；明确分层架构与专业Agent协作流程；新增模块import smoke测试5/5通过 | feat/docs/chore/test | v6/**, docs/v6/**, tests/v6/test_v6_smoke.py |
| v5.0.23-alpha | 2026-07-06 | 修复chat_worker.py TOOL_DEFINITIONS属性错误；创建v4独立打包入口/配置/脚本，实现v5与v4并行打包及桌面快捷方式；验证dist/AgentWorkbench/与dist/AgentWorkbenchV4/均可独立启动；272/272测试通过 | fix/build/chore | v5/service/chat_worker.py, v4/v4_main.py, v4/AgentWorkbenchV4.spec, v4/scripts/rebuild_v4.ps1, scripts/rebuild.ps1, v4/README.md |
| v5.0.22-alpha | 2026-07-06 | 补充.gitignore：排除.reference/、.scripts/、review/等本地参考/调试/归档目录，保持git status干净 | chore | .gitignore |
| v5.0.21-alpha | 2026-07-06 | 工作区整理与文档同步：修正config.yaml版本号，统一docs/为正式文档目录，根目录新建README.md；归档AgentWorkbench.spec、ui/、resources/、blueprints/、v4测试到v4/legacy/、v4/tests/、docs/archive/blueprints/；清理.bak与空目录，同步根目录与docs/下CHANGELOG/PROJECT_BLUEPRINT，272/272测试通过 | chore/docs/archive/test | README.md, CHANGELOG.md, PROJECT_BLUEPRINT.md, docs/README.md, docs/CHANGELOG.md, docs/PROJECT_BLUEPRINT.md, config/config.yaml, AgentWorkbenchV5.spec, scripts/rebuild.ps1, v4/legacy/, v4/tests/, docs/archive/blueprints/ |
| v5.0.20-alpha | 2026-07-06 | V5剩余5%细节功能闭环：修复adapter.py工具执行回调命名冲突，ChatArea按phase渲染阶段面板，新增工具执行/确认/阶段渲染/craft端到端测试，全量272/272通过；修复AgentWorkbenchV5.spec隐藏导入并重新打包验证exe启动 | fix/feat/test/build | v5/service/adapter.py, v5/widgets/chat_area.py, v5/widgets/chat_items.py, tests/test_v5_*.py, AgentWorkbenchV5.spec |
| v5.0.19-alpha | 2026-07-06 | 修复聊天区模式列表与引擎不一致Bug，WorkController.manual_modes动态管理模式；新增V5 ChatArea/Adapter/Integration测试78用例，319/319通过；修复AgentWorkbenchV5.spec隐藏导入并打包验证 | fix/test/build | v5/widgets/chat_area.py, v5/controller/work_controller.py, tests/test_v5_*.py, AgentWorkbenchV5.spec |
| v5.0.18-alpha | 2026-07-06 | V5 P6/P7收尾归档：提交v5新增测试、独立打包配置与v4归档说明，清理调试产物，README/PROJECT_BLUEPRINT/CHANGELOG版本对齐，240/240测试通过 | docs/archive/test/build | tests/test_v5_*.py, AgentWorkbenchV5.spec, v4/README.md, docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.17-alpha | 2026-07-06 | V5彻底隔离v4与P6/P7主体整改：清理v5/全部v4文字残留并确认无v4导入；统一Widget层V5信号契约，修复ChatArea/RightPanel/MainWindow连接，补齐终端/文件/浏览器用户操作信号；修正InvisibleResizeHandle布局；新增15个V5测试，240/240测试通过；新增AgentWorkbenchV5.spec与v4/README.md归档说明 | refactor/test/build/docs | v5/**, tests/test_v5_*.py, AgentWorkbenchV5.spec, v4/README.md, docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.12-alpha | 2026-07-06 | UI完全移植工程最终完整性检查与存档：复核P10旧UI清理与PyInstaller打包验证，完成P11 v4-refactor旧UI线路最终归档并推送v4.0.11-alpha标签，真实GUI验证三栏完整显示，225/225测试通过 | docs/archive/test | docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.11-alpha | 2026-07-06 | P9全量冒烟与集成测试验证及UI硬编码清理：真实GUI启动验证三栏完整显示，清理'v4 架构升级'等旧UI硬编码，实现聊天区标题动态化，225/225测试通过 | fix/test/ui | v4/widgets/chat_area.py, v4/widgets/right_panel.py, v4/widgets/left_panel.py, v4/main_window.py, tests/test_v4_gui_smoke.py |
| v5.0.10-alpha | 2026-07-06 | v5项目文档同步：README/PROJECT_BLUEPRINT/CHANGELOG全面更新为v5新UI完整版线路，反映v5.0.0~v5.0.9全部阶段成果，目录结构同步v4/widgets/与v4/legacy/，测试数更新为225 | docs | docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.9-alpha | 2026-07-06 | P10清理旧UI与打包验证：删除v4根目录重复旧UI文件（已备份至v4/legacy/），迁移旧测试导入，更新AgentWorkbench.spec hiddenimports为v4.widgets.*，PyInstaller打包成功并验证exe独立启动 | chore/build/test | AgentWorkbench.spec, v4/legacy/*, tests/test_v4_input_area.py, tests/test_v4_right_panel.py |
| v5.0.8-alpha | 2026-07-06 | P8完整功能回填GUI冒烟修复：修复ChatArea中QPen导入缺失导致的paintEvent崩溃，验证三栏加载/会话创建/UI事件分发正常 | fix/ui/test | v4/widgets/chat_area.py |
| v5.0.7-alpha | 2026-07-06 | P7右栏真实功能回填：实现TerminalWidget/FileReaderWidget/BrowserWidget并集成到RightPanel；最近文件列表及点击打开；同步会话项目路径到终端工作目录 | feat/ui/test | v4/widgets/right_panel.py, v4/widgets/terminal_widget.py, v4/widgets/file_reader_widget.py, v4/widgets/browser_widget.py, workers/terminal_worker.py, tests/test_v4_widgets_right_panel.py |
| v5.0.6-alpha | 2026-07-06 | P5/P6持久化校验与测试整改：增强app.last_mode/last_model启动与设置应用校验，补充主题键backward compatibility，新增边界测试 | fix/test | v4/main_window.py, v4/widgets/base.py, tests/test_v4_integration.py |
| v5.0.5-alpha | 2026-07-06 | P5会话数据持久化与列表同步：实现last_session_id持久化与启动恢复、会话切换/创建/删除配置同步、无效会话清理、左栏空状态显示 | feat/test | v4/main_window.py, v4/widgets/left_panel.py, v4/repository.py |
| v5.0.4-alpha | 2026-07-06 | P4关键用户动作对接：停止/确认/分析按钮、导出会话、设置对话框、搜索过滤、模式模型下拉选择器 | feat/ui | v4/main_window.py, v4/widgets/chat_area.py, v4/widgets/left_panel.py, v4/widgets/dropdown_selector.py, v4/widgets/settings_dialog.py |
| v5.0.3-alpha | 2026-07-06 | 模块化骨架拆分与致命Bug修复：将v4/main_window.py拆分为v4/widgets/9个模块，修复_session_idx_map为空问题 | refactor/fix | v4/widgets/*, v4/main_window.py |
| v5.0.2-alpha | 2026-07-06 | P3 UIRenderer与新UI桥接完成：ChatArea真实消息渲染/流式输出/确认条/阶段状态，LeftPanel会话列表刷新与badge更新 | feat/ui | v4/widgets/chat_area.py, v4/widgets/left_panel.py, v4/ui_renderer.py |
| v5.0.1-alpha | 2026-07-06 | 备份v4旧UI组件至v4/legacy/并标记v5-dev线路 | chore/docs | v4/legacy/*, docs/README.md, docs/PROJECT_BLUEPRINT.md, docs/CHANGELOG.md |
| v5.0.0-alpha | 2026-07-06 | v5-dev线路起点与新UI后端核心注入 | feat/ui | v4/main_window.py, v4/widgets/* |
| v4.0.7-alpha | 2026-07-01 | 标题栏三键（搜索/更多/展开）+ execute步骤条自动解析；三键图标改为SVG path并接入搜索高亮/更多菜单/全局快捷键；docs/ui/归档6 SVG+2 spec | feat/docs/fix | v4/main_window.py, v4/ui_renderer.py, AgentWorkbench.spec, docs/ui/* |
| v4.0.6-alpha | 2026-07-01 | 补齐目录标准化遗漏：`AgentWorkbench.spec` datas加入`assets/app.ico`；`services/project_service.py`改用`_get_app_root()`定位`storage/activities.json`，避免exe在CWD创建storage | fix/build | AgentWorkbench.spec, services/project_service.py |
| v4.0.5-alpha | 2026-06-30 | 工程目录标准化改造：根目录文件按职责分组为config/、assets/、scripts/、docs/，源码目录统一标注为src/分组；同步修正PyInstaller datas、runtime_hook、图标路径、config_service/LLMRegistry路径解析及所有代码中的配置路径引用；README/ARCHITECTURE/PROJECT_BLUEPRINT/getting-started同步更新 | refactor/docs/build | AgentWorkbench.spec, scripts/rebuild.ps1, services/config_service.py, agent_engine/llm_registry.py, v4/main_window.py, v4/worker.py, v4/repository.py, services/activity_service.py, services/session_service.py, docs/README.md, docs/ARCHITECTURE.md, docs/PROJECT_BLUEPRINT.md, docs/getting-started.md |
| v4.0.4-alpha | 2026-06-30 | v4对话UI三层折叠结构：阶段面板始终展开、工具执行与思考过程默认收起、内部命令输出超长折叠；左栏会话列表精简为标题+最后消息预览+时间三字段；新增无LLM依赖的UI折叠验证脚本 | feat/test | v4/main_window.py, v4/ui_renderer.py, v4/conversation_list.py, v4/events.py, v4/orchestrator.py, v4/worker.py, v4/worker_manager.py, tests/test_v4_integration.py, scripts/verify_ui_fold.py |
| v4.0.3-alpha | 2026-06-30 | Phase工作流接入v4：V4Worker内建PhaseEngine支持craft模式analyze→confirm→execute→verify→archive完整流程；analyze/verify阶段解绑工具强制文本输出；PyInstaller spec适配v4单轨架构；清理27个零引用v2/v3文件；修复用户停止任务CANCELLED状态与Worker销毁 | feat/refactor/fix | v4/worker.py, v4/orchestrator.py, v4/worker_manager.py, v4/event_bus.py, v4/events.py, AgentWorkbench.spec, tests/test_v4_integration.py |
| v4.0.2-alpha | 2026-06-30 | v4原生Worker八引擎推理：新建v4/worker.py以V4Worker(QThread+asyncio)直驱ReAct循环，零绞杀者依赖旧AgentWorker/AgentOrchestrator/AgentSession；worker_manager接入V4Worker替代EngineWorker；orchestrator传递user_text到WorkerCreateEvent | feat/refactor | v4/worker.py, v4/worker_manager.py, v4/orchestrator.py, v4/events.py, v4/main_window.py |
| v4.0.1-alpha | 2026-06-30 | v4 Solo极简UI重构：固定两栏布局（左280px/右填充）、主题切换按钮（🌙/☀️ 暗色/浅色持久化到config.yaml）、会话列表极简化（标题+预览+时间）、延迟创建会话（首条消息才写DB） | feat/test | v4/main_window.py, v4/conversation_list.py, config.yaml, tests/test_v4_gui_smoke.py, tests/test_v4_integration.py |
| v3.12.0 | 2026-06-30 | AI Engine 架构升级：八引擎模块化 + System Prompt 增强 + LLM 参数可配 + 记忆路径修正 + 绞杀者集成 | feat/refactor/fix | agent_engine/engines/*.py, agent_engine/orchestrator.py, agent_engine/llm_registry.py, services/self_context.py, config.yaml, ui/main_window.py, tests/test_self_context.py |
| v3.11.4 | 2026-06-29 | MainWindow 架构收敛重构：移除 _pending_queue/_worker/_workers/_phase_manager 等旧全局状态，统一走 v3 MessageBus 路径；修复新会话按钮只能添加一个标签、会话标签名均为"新对话"、Enter 键首次失效（新增 `_focus_input_field` 强制焦点）、切换新会话显示无意义接替上下文；补充 FileTreeWidget.get_root_path 与 SessionManager Qt 导入修复；新增 MainWindow UI 自动化测试 | fix/refactor/test | ui/main_window.py, ui/widgets/sidebar.py, ui/managers/session_manager.py, services/self_context.py, tests/test_main_window_ui_automation.py |
| v3.11.3 | 2026-06-29 | 修复真实运行时 WorkerManager 无法解析 LLM、Phase 错误后未 reset、空对话守卫导致单标签、新建会话后 Orchestrator 当前会话不同步、SessionManager 标题 data role 错误；新增 pytest.ini 排除 scripts 测试噪音 | fix | ui/managers/worker_manager.py, ui/managers/phase_coordinator.py, services/session_orchestrator.py, ui/main_window.py, ui/managers/session_manager.py, pytest.ini |
| v3.11.2 | 2026-06-29 | 修复 v3 Worker 重复创建导致无响应：Orchestrator 移除 worker.created/execute_required/verify_required 重复订阅；新 runtime 创建后同步 UI 队列状态；README 与文档规范化 | fix/docs | services/session_orchestrator.py, tests/integration/test_v3_flow.py, README.md, docs/getting-started.md, PROJECT_BLUEPRINT.md |
| v3.11.1 | 2026-06-29 | 修复 v3 事件流：Worker 创建后立即 analyze、会话切换同步队列 UI、历史会话自动创建 runtime、切换不误杀后台任务 | fix/refactor | core/events.py, ui/managers/worker_manager.py, services/session_orchestrator.py, ui/main_window.py, ui/managers/session_manager.py, README.md |
| v3.11.0 | 2026-06-29 | 工程标准化：新增 README、ARCHITECTURE、blueprints/、docs/getting-started | docs | README.md, ARCHITECTURE.md, blueprints/*.md, docs/*.md |
| v3.9.1 | 2026-06-29 | 修复 Phase 状态机重入与任务状态回收：调整 flow_finished/reset 顺序、统一 TaskService.complete_task 调用、修复会话切换覆盖 completed 状态、补充 completed 绿色图标、修复 SessionManager 标题更新 data role | fix/refactor | agent_engine/phase_manager.py, services/task_service.py, services/pending_queue.py, services/self_context.py, ui/main_window.py, ui/widgets/conversation.py, ui/chat_view.py, workers/agent_worker.py, tests/test_pending_queue.py, tests/test_self_context.py, ui/managers/*.py |
| v3.9.0 | 2026-06-27 | 多任务管理系统（TaskService+WorkerPool）、Session-as-Room 会话隔离、Trae 暗黑主题、底栏容量状态条、会话状态图标、信号调试管道 | feat/fix | services/task_service.py, workers/task_capacity.py, workers/task_queue.py, workers/worker_pool.py, workers/session_task.py, workers/task_worker_adapter.py, resources/themes/trae_dark.qss, services/theme_service.py, ui/main_window.py, ui/widgets/conversation.py, ui/chat_view.py, agent_engine/agent_session.py, workers/agent_worker.py, config.yaml, AgentWorkbench.spec, tests/test_agent_session_integration.py, tests/test_main_window_session_isolation.py |
| v3.8.1 | 2026-06-27 | 填充架构占位文件、对话气泡排版优化、活动面板多选增强、屏幕工具注册 | feat/fix | tools/screen.py, tools/__init__.py, ui/overlay.py, ui/settings.py, ui/tools_panel.py, ui/chat_view.py, ui/widgets/activity_panel.py, workers/agent_worker.py, config.yaml |
| v3.8.0 | 2026-06-27 | MVC资源管理器、PersistenceService持久化、MemoryManager画像schema、工具注册与依赖对齐 | feat/fix | ui/models/explorer_tree_model.py, ui/widgets/explorer_view.py, ui/widgets/explorer.py, services/persistence_service.py, agent_engine/memory_manager.py, config.yaml, workers/agent_worker.py, requirements.txt, AgentWorkbench.spec, tests/* |
| v3.7.4 | 2026-06-27 | Analyze 阶段强制只读工具与结果截断对齐 | fix/feat | agent_engine/orchestrator.py, agent_engine/agent_session.py |
| v3.7.3 | 2026-06-26 | 分级超时与持久化路径修复 | fix/feat | agent_engine/orchestrator.py, agent_engine/memory_manager.py, workers/agent_worker.py, services/config_service.py, tools/system.py, ui/main_window.py, config.yaml |
| v3.7.2 | 2026-06-26 | 修复 v3.7.1 中窗口标题初始化顺序导致的打包启动崩溃 | fix | ui/main_window.py |
| v3.7.1 | 2026-06-26 | 修复启动时解释器检测弹窗、历史会话 AI 回复丢失、终端输入框无法编辑；窗口标题动态读取版本号；活动面板增强说明/全局分类/右键复制 | fix/feat | services/interpreter_service.py, ui/main_window.py, ui/widgets/terminal.py, ui/widgets/activity_panel.py, config.yaml |
| v3.7 | 2026-06-26 | 终端解释器管理：自动发现 Python(venv/系统)/PowerShell/CMD/Git Bash、TerminalWidget 下拉切换、解释器上下文注入 prompt、run_python/run_powershell/run_bash 工具、相关 bug 修复 | feat/fix | services/interpreter_service.py, services/context_service.py, ui/main_window.py, ui/widgets/terminal.py, ui/widgets/workspace.py, workers/terminal_worker.py, tools/system.py, config.yaml, AgentWorkbench.spec, tests/test_interpreter_service.py |
| v3.6 | 2026-06-26 | Phase-Driven Workflow Engine：Mode×Phase 矩阵、Analyze→Confirm→Execute→Verify→Archive 阶段流转、软硬 Checkpoint、任务清单驱动、UI 阶段指示器与确认门控 | feat | agent_engine/phase_manager.py, agent_engine/orchestrator.py, services/context_service.py, ui/main_window.py, ui/chat_view.py, workers/agent_worker.py, AgentWorkbench.spec, tests/test_phase_manager.py |
| v3.5 | 2026-06-26 | 请求级指标：token/耗时收集、AI 气泡下方显示 metrics、日志输出 TTFT 详情 | feat | services/metrics_collector.py, agent_engine/orchestrator.py, workers/agent_worker.py, workers/base_worker.py, ui/main_window.py, ui/chat_view.py |
| v3.4 | 2026-06-26 | 工作空间上下文感知：自动检测项目目录、右侧文件摘要注入 prompt、文件工具相对路径解析、最近项目下拉 | feat | services/context_service.py, services/path_resolver.py, services/project_service.py, agent_engine/orchestrator.py, tools/system.py, ui/main_window.py, ui/widgets/document_editor.py, ui/widgets/workspace.py, ui/widgets/sidebar.py, ui/widgets/status_indicator.py, workers/agent_worker.py, config.yaml, AgentWorkbench.spec, tests/test_context_service.py |
| v3.3 | 2026-06-25 | 精细化打磨：任意格式文件预览、对话/活动分栏、文档编辑快捷键、修复模型持久化与活动重复记录 | feat/fix | ui/widgets/document_editor.py, ui/widgets/conversation.py, ui/widgets/activity_panel.py, services/activity_service.py, ui/main_window.py, resources/themes/dark_github.qss, AgentWorkbench.spec |
| v3.2 | 2026-06-25 | 项目目录与对话上下文：资源管理器切换/打开文件夹、按目录组织会话、目录下开启新对话 | feat/refactor | services/project_service.py, services/session_service.py, ui/widgets/sidebar.py, ui/widgets/conversation.py, ui/main_window.py, config.yaml, resources/themes/dark_github.qss |
| v3.1 | 2026-06-25 | 重建右侧工作区：终端/日志/文档标签页、左侧文件树联动文档编辑器、文本文件编辑模式 | feat/refactor | ui/widgets/workspace.py, ui/widgets/document_editor.py, ui/main_window.py, resources/themes/dark_github.qss, AgentWorkbench.spec |
| v3 | 2026-06-25 | 工具分层编排、AI身份系统、17工具库、UI全栈修复 | feat/fix | agent_worker, config, main_window, tools/* |
| v0.3 | 2026-06-25 | v2生产级重构：模块化架构、8工具、流式UI | feat/refactor | 全部模块 |
| v0.2 | 2026-06-25 | DeepSeek密钥修复与模型选择下拉功能 | feat/fix | config.yaml, llm_registry.py, main.py |
| v0.1 | 2026-06-24 | 初始提交AI工作台项目 | feat | main.py, config.yaml, agent_engine/, tools/ |

## 存档流程
1. 更新 docs/CHANGELOG.md + docs/PROJECT_BLUEPRINT.md + docs/README.md + docs/ARCHITECTURE.md + blueprints/ + docs/（全部项目文档）
2. git add -u && git add docs/CHANGELOG.md docs/PROJECT_BLUEPRINT.md（覆盖已跟踪修改 + 两个维护文件）
3. git commit -m "..." + git tag vX.Y.Z
4. git push + git push origin vX.Y.Z（仅当前分支 + 当前标签，禁 --tags）

_更新于 2026-07-06 by AI-Kimi-K2.7-Code_

## Agent交接记录
| 时间 | 方向 | 从 | 到 | 交接点 | 备注 |
|---|---|---|---|---|---|
| 2026-06-27T19:00 | 移交 | Kimi-K2.7-Code | — | v3.9.0 存档后 | 多任务管理系统+Session-as-Room+Trae暗黑主题已完成，全部单测通过，已推送 |

---
