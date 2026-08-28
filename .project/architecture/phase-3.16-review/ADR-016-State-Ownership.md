# ADR-016: State Ownership

> **Status**: Architecture Review (Phase 3.16)
> **Date**: 2026-07-25
> **Scope**: Who owns system state?

---

## 核心问题

> **谁拥有系统状态？**

```
Observation
    ↓
Artifact
    ↓
State
```

State 可能属于：

- Runtime
- Agent Instance
- Workspace
- Factory
- Human

---

## 当前倾向（Phase 3.16 Review）

```
Runtime ≠ State Owner
```

**Runtime 只管理生命周期和协议，不拥有 State。**

---

## 决策

### D-016.1: State 与 Runtime 解耦

Runtime 不应是 State 的 Owner。State 的 Owner 取决于 State 的语义：

| State 类型 | Owner |
|-----------|-------|
| Runtime Lifecycle State | Runtime |
| Session State | Workspace |
| Agent Knowledge State | Agent Instance (NOT Runtime) |
| Persistent Knowledge | Memory Authority |
| User Intent State | Human |

### D-016.2: 一份 State 一份 Owner

每份 State 必须有且只有一个 Owner。Owner 拥有：

- Read 权限
- Mutation 权限
- 销毁权限

### D-016.3: Artifact 不是 State

Artifact（ObservationArtifact / InsightArtifact / DecisionArtifact）是 **frozen contract**，不是 State。

State 是：

- Runtime Lifecycle State
- Session State
- Agent 内部 mutable state
- Persistent memory

Artifact 是：

- Frozen dataclass
- Read-only after construction
- Cross-layer contract

---

## 禁止的反模式

### 反模式 1: Runtime 持有 Cross-Layer State

```
Runtime
   ├── Session 1
   ├── Session 2
   └── "Insight cache for Session 1"   ← Runtime 不应持有这个
```

❌ Runtime 越权。

### 反模式 2: Agent 修改 Insight

```
Agent
   ↓
"我有了新的理解"
   ↓
modify InsightArtifact
   ↓
自证循环
```

❌ InsightArtifact 是 frozen contract，Agent 不能写回。

### 反模式 3: Workspace 拥有跨 User State

```
Workspace
   ├── User A Intent
   └── User B Intent
```

❌ Workspace 应该有用户隔离的 State。

---

## 与其他 ADR 的关系

- **ADR-017 Persistence Authority**：State Owner 决定 Write Authority
- **ADR-018 Agent Lifecycle**：State Owner 决定 Lifecycle Transition Authority
- **ADR-019 Runtime Authority**：Runtime 可以管理哪些 State？

---

## 下一步

Future Architecture Cycle：

- Memory Owner 的具体定义
- Workspace 边界定义
- Cross-Agent State 共享规则