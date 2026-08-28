# ADR-019: Runtime Authority

> **Status**: Architecture Review (Phase 3.16)
> **Date**: 2026-07-25
> **Scope**: What can Runtime decide?

---

## 核心问题

> **Runtime 可以决定什么？**

确认边界：

Runtime 可以：

- ✅ execute protocol
- ✅ manage session
- ✅ validate contract

Runtime 不可以：

- ❌ own ecosystem state
- ❌ modify user intent
- ❌ autonomously create authority

---

## 当前倾向（Phase 3.16 Review）

**Runtime 是 Protocol Executor，不是 State Owner，不是 Authority Grantor。**

Runtime 的本质：

```
Protocol
   ↓
Execution
   ↓
Event Emission
   ↓
Contract Validation
```

不是：

```
Authority
   ↓
Decision
   ↓
State Mutation
```

---

## 决策

### D-019.1: Runtime 是 Stateless Executor

Runtime Kernel (Phase 3.11 v6.16.0-alpha Frozen) 的核心：

- 接收 Protocol Contract
- 执行 Protocol Steps
- 发出 Lifecycle Events
- 验证 Child Contract

Runtime 不持有跨 Session State。

### D-019.2: Runtime Authority Boundaries

Runtime 可以：

| 可以 | 说明 |
|------|------|
| ✅ Execute Protocol | 按 contract 执行 |
| ✅ Validate Contract | 校验输入 / 输出 |
| ✅ Emit Lifecycle Events | ADR-013 已定义 |
| ✅ Cancel Execution | ADR-014 已定义 |
| ✅ Propagate to Child | ADR-015 已定义 |
| ✅ Manage Session | Session internal state |

Runtime 不可以：

| 不可以 | 原因 |
|--------|------|
| ❌ Own Ecosystem State | State Owner 是 Human / Workspace |
| ❌ Modify User Intent | Intent 是 Human Authority |
| ❌ Create Agent | Agent Lifecycle 是 Human / Workspace Authority |
| ❌ Archive Agent | 同上 |
| ❌ Persist Memory | Persistence Authority 需 Human Grant |
| ❌ Trigger Decision | Decision Layer 独立 |
| ❌ Skip Contract Validation | 必须严格 |

### D-019.3: Runtime Authority 来自 Contract

Runtime 执行的不是"自己的意志"，而是 **Contract 定义的 Protocol**。

```
Contract
   ↓
Runtime
   ↓
Execute Protocol
```

Contract 是 Source of Truth，Runtime 是 Executor。

---

## 禁止的反模式

### 反模式 1: Runtime 持有 Session State

```
Runtime
   ├── Session 1 (state A, state B)
   └── "User prefers X"   ← 不应持有
```

❌ Runtime 是 Stateless Executor，不持有 User-level State。

### 反模式 2: Runtime 自作主张

```
Runtime
   ↓
"我觉得应该这样做"
   ↓
Execute without Contract
```

❌ Runtime 不能在没有 Contract 的情况下 Execute。

### 反模式 3: Runtime Modify Intent

```
User Intent: "做 A"
Runtime: "我觉得应该做 B"
Runtime Modify Intent to B
```

❌ Runtime 不能 Modify User Intent。

---

## Runtime 与其他 Layer 的关系

| Layer | Runtime 可以 Read | Runtime 可以 Write |
|-------|-------------------|---------------------|
| Contract (Protocol) | ✅ | ✅ (validate / emit) |
| Session | ✅ | ✅ (session internal) |
| Observation | ✅ | ✅ (produce) |
| Insight | ✅ | ❌ (read-only) |
| Decision | ✅ | ❌ (read-only) |
| Memory | ✅ | ❌ (need Human Grant) |
| Agent Lifecycle | ✅ (emit event) | ❌ (decide) |

---

## 与其他 ADR 的关系

- **ADR-016 State Ownership**：Runtime 不持有 State，只 Execute
- **ADR-017 Persistence Authority**：Runtime 不能 Write Persistent State
- **ADR-018 Agent Lifecycle**：Runtime 不能决定 Agent Lifecycle
- **ADR-020 Human Approval Boundary**：Runtime 必须尊重 Human Authority

---

## 与 Phase 3.11 Runtime Kernel 的关系

Phase 3.11 v6.16.0-alpha 已经 Frozen 的边界：

- ADR-013: Runtime Lifecycle Event Extension
- ADR-014: Cancellation Precedence Rule
- ADR-015: Parent-Child Execution Propagation

这些 ADRs **已经实现 Runtime 内部 Authority 边界**。

Phase 3.16 ADR-019 是 **Runtime 与其他 Layer 的 Authority 边界**，与 ADR-013/014/015 互补。

---

## 下一步

Future Architecture Cycle：

- Runtime Authority 的具体 Contract 定义
- Runtime 与 Memory 的具体隔离方式
- Runtime 与 Human Approval 的具体接口