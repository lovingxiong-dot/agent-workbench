# Architecture Decision: Shell Contract Freeze

## Status

Accepted — 2026-07-21
Phase 1-B Freeze Review — Passed
Scope: `agent_workbench/presentation/shell/`

## Context

Agent Workbench OS 在 v6.14.0-alpha 阶段面临一个核心架构问题：

**UI 层和 Runtime 层的边界在哪里？**

之前的架构演变：

```
v1: MainWindow 直接持有 Runtime → mainwindow.py 3000+ lines
v2: 拆分为 WorkbenchHost → Workbench → NavigatorHost / WorkspaceHost / InspectorHost
v3: 引入 Presentation Layer → Adapter → ViewModel → UI
```

但在 Phase 1-B 之前，`presentation/shell/` 的定位存在模糊地带：

- 它是 UI Layer 的一部分？还是 Runtime 的出口协议？
- NavigationModel 命名混乱（`NavigationState` vs `NavigationGroup`）
- Shell Boundary 约束未文档化

核心风险：如果 Shell 被误解为 UI Layer，未来多端扩展（Web/Mobile/CLI/Embedded）会污染核心逻辑。

## Decision

### 1. Shell 定位

**Shell 不是 UI。Shell 是 Agent Workbench OS 的 Renderer-Independent Presentation Contract。**

```
Runtime
   ↓
Capability
   ↓
Adapter
   ↓
ViewModel
   ↓
Shell Contract   ← presentation/shell/ (THIS LAYER)
   ↓
Renderer         ← 多端实现：Desktop UI / Web UI / Mobile UI / CLI
```

定位等价于：Agent OS 的表现层接口定义（Presentation ABI）。

### 2. 命名规范

| 模型 | 语义 | 类型 |
|------|------|------|
| `NavigationGroup` | 导航结构分组 | 结构模型（静态） |
| `NavigationItem` | 导航项 | 结构模型（静态） |
| `WorkspaceState` | 工作区运行时快照 | 状态模型（动态） |
| `WorkspaceMessage` | OS 级消息 | 数据模型 |
| `InspectorState` | 属性面板运行时快照 | 状态模型（动态） |
| `CommandState` | 命令/状态栏快照 | 状态模型（动态） |

**Group 表示结构模型，State 表示运行时快照。** 两者不混淆。

`NavigationState` 已替换为 `NavigationGroup`——导航不是运行时状态，是层级组织结构。

### 3. Shell Boundary 约束

```
Allowed:
  ✓ Pure Python data models (dataclasses)
  ✓ Protocol interfaces (typing.Protocol)
  ✓ Data transformers (ViewModel → Shell Model)
  ✓ Type annotations and enumerations

Forbidden:
  ✗ PySide6 imports
  ✗ Runtime imports
  ✗ Agent execution
  ✗ Tool execution
  ✗ Storage access
  ✗ Business logic
  ✗ Widget creation or manipulation
```

这一约束确保：

- PySide6 Renderer 可以替换为 React Renderer，Shell 不变
- CLI Renderer 可以复用同一份 Shell Contract
- 未来任何人都不会将业务逻辑放入 Shell

### 4. Adapter 是唯一翻译入口

```
Runtime  ──NEVER import by Shell──►

        Presentation Layer
        │
        ├── adapters/        ← Runtime → ViewModel 翻译
        │
        ├── view_models/     ← 数据类型定义
        │
        └── shell/           ← ViewModel → Shell Model 翻译
            │
            ├── protocol.py  ← ShellBoundary + 6 模型
            ├── integration.py ← PresentationPipeline
            └── transformers/ ← 3 个转换器
```

依赖方向（单向）：`shell → view_models ← adapters ← runtime`

Shell 不 import Runtime。Adapter 不 import Shell。ViewModel 是中间契约。

### 5. 目录结构暂不拆分

当前模型定义在 `protocol.py` 中，不创建独立的 `models/` 子目录。

原因：
- 模型数量少（6 个），拆分会增加循环依赖风险
- Protocol + Model 是一个整体概念，类似 `typing.Protocol` + dataclass
- 当模型数量超过 20+ 时再考虑拆分为 `protocol.py` + `models/`

## Consequences

### 正面影响

- 多端扩展：Desktop/Web/Mobile/CLI/Embedded 全部通过 Shell Contract 接入
- 架构隔离：业务逻辑不能进入 Shell，Shell 不能调用 Runtime
- 可替换性：Renderer 替换不需要修改 Shell Contract
- 契约文档化：Shell Boundary 注释即 Constitution

### 负面/约束

- 新增 Renderer 必须实现 `ShellProtocol` 全部 4 个方法
- Transformer 层增加了一层间接性（ViewModel ↔ Shell Model）
- 未来模型数量增长后需要拆分目录

## Alternatives Considered

### 方案 A：Shell 直接作为 UI Layer

```
Runtime → UI
```

**否决**：导致 mainwindow.py 3000+ lines，多端不可扩展。

### 方案 B：ViewModel 直接对接 Runtime

```
Runtime → ViewModel → UI
```

**否决**：ViewModel 承担了过多职责，转换逻辑分散。

### 方案 C：引入中间 Shell Contract（当前方案）

```
Runtime → Adapter → ViewModel → Shell Contract → Renderer
```

**采纳**：Adapter + ViewModel + Shell 三层，职责清晰。

## References

- [Shell Boundary Contract](../../agent_workbench/presentation/shell/protocol.py)
- [Shell Protocol Test](../../agent_workbench/tests/test_shell_protocol.py)
- [Phase 1-B Freeze Report](file:///e:/Development/workbench/agent_workbench/.project/handoff/latest.md)
- [PROJECT_BLUEPRINT.md — Agent Workbench OS 定位](../../PROJECT_BLUEPRINT.md)
