# Phase 3.16 Memory + Harness — Architecture Review Overview

> **Status**: Review Only (NOT a Code Phase)
> **Date**: 2026-07-25
> **Context**: Phase 3.11-3.15 Code Complete (Observe → Understand → Recommend)
> **Next**: Future Architecture Cycle

---

## 1. 触发条件

Phase 3.11-3.15 已经形成认知链闭环：

```
Observation
      ↓
Insight
      ↓
Decision Support
```

下一步真正影响 AOS Runtime 的不是继续增加 Capability，而是确认根边界：

```
State
Memory
Lifecycle
Authority
Execution Permission
```

这些属于系统根边界。如果现在直接归档 Phase 3，后续接入 Harness / Memory 时，容易重新讨论同一批边界问题。

---

## 2. 范围

5 个 ADR（每个覆盖一个根边界问题）：

| ADR | 核心问题 |
|-----|---------|
| ADR-016 | State Ownership（谁拥有系统状态） |
| ADR-017 | Persistence Authority（谁允许写入持久化存储） |
| ADR-018 | Agent Lifecycle（生命周期在哪里管理） |
| ADR-019 | Runtime Authority（Runtime 可以决定什么） |
| ADR-020 | Human Approval Boundary（哪些必须 Human Authority） |

---

## 3. 约束

- ❌ 不写代码
- ❌ 不增加 Runtime
- ❌ 不增加 Memory
- ❌ 不增加 Harness
- ❌ 不进入 Implementation / Test / Commit
- ✅ 仅讨论架构边界

---

## 4. ADR 之间的关系

```
ADR-016 State Ownership
       │
       ├── 影响 ──> ADR-017 Persistence Authority (谁可以写)
       │
       └── 影响 ──> ADR-018 Agent Lifecycle (谁管理状态转换)

ADR-019 Runtime Authority
       │
       └── 限定 ──> ADR-018 Agent Lifecycle

ADR-020 Human Approval Boundary
       │
       └── 限定 ──> ADR-019 Runtime Authority
                   (Runtime 不能跨过 Human Approval)
```

---

## 5. 下一个 Architecture Cycle 入口

Phase 3.16 不结束 Architecture 路线。

完成 5 个 ADR 后，进入 **Future Architecture Cycle**：

- Memory 实现（如 Harness 触发）
- Runtime 扩展（如新增 Authority）
- Decision → Execution 链（如 Human Approval 通过）