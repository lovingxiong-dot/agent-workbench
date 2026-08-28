# ADR-017: Persistence Authority

> **Status**: Architecture Review (Phase 3.16)
> **Date**: 2026-07-25
> **Scope**: Who is allowed to write to persistent storage?

---

## 核心问题

> **谁允许写入持久化存储？**

需要避免：

```
Agent
 ↓
Memory.write()
 ↓
永久状态改变
```

形成无限自治。

---

## 当前倾向（Phase 3.16 Review）

```
Read Authority
    ≠
Write Authority
```

**Read 与 Write 必须分离。**

---

## 决策

### D-017.1: Read Authority（宽）

任何 Layer 都可以 Read（除了明确禁读的 State）：

- Observation / Insight / Decision / Execution 都可以 Read
- Read 是 contract 的属性
- Read 不修改 State

### D-017.2: Write Authority（窄）

Write 必须有 **explicit authority grant**：

| Write 目标 | Authority Grant 来源 |
|-----------|---------------------|
| ObservationArtifact | Producer (Runtime / Human / Agent) |
| InsightArtifact | Adapter (纯函数, no state change) |
| DecisionArtifact | Adapter (纯函数, no state change) |
| Memory (Persistent Knowledge) | **Human Authority** + Contract |
| Runtime Lifecycle State | Runtime (internal) |
| Session State | Workspace |
| Agent Internal Mutable State | Agent Instance (bounded) |

### D-017.3: Memory Write 必须经过 Human Approval

```
Memory.write()
   ↓
必须经过
   ↓
Human Approval
   ↓
Memory Commit
```

不是：

```
Agent
 ↓
Memory.write()    ← 无 Human 介入
```

### D-017.4: Read-Only Contract 不允许 Write

ObservationArtifact / InsightArtifact / DecisionArtifact 是 frozen contract：

- 任何 Layer 都不应修改它们
- 如果需要"扩展"，创建新 Artifact，引用旧 Artifact
- 严格避免 mutation

---

## 禁止的反模式

### 反模式 1: Agent 自动写 Memory

```
Agent Loop
   ↓
观察 → 推断 → 建议 → 自动写入 Memory
```

❌ 这形成自证循环，绕过 Human Authority。

### 反模式 2: Read-Write 合并

```
ReadInsight() {
    return mutate_insight()
}
```

❌ Read 与 Write 必须在 API 边界分离。

### 反模式 3: Persistent State 没有 Owner

```
"Global Memory"
   │
   ├── 谁都可以写
   │
   └── 无 Audit Trail
```

❌ 任何 Persistent State 必须有 Owner + Authority Grant。

---

## 与其他 ADR 的关系

- **ADR-016 State Ownership**：State Owner 是 Write Authority 的基础
- **ADR-018 Agent Lifecycle**：Write 操作发生在 Lifecycle 哪个阶段？
- **ADR-019 Runtime Authority**：Runtime 可以 Write 什么？
- **ADR-020 Human Approval Boundary**：Memory Write 必须经过 Human

---

## 关键判断（Insight ↔ Memory 隔离）

Phase 3.14 Insight 强调：

> **Insight ≠ Memory**

```
Insight
   ↓
不应该直接写入 Memory
   ↓
避免 Inference 持久化为永久知识
```

Insight 是 **structured understanding layer**，**不是知识**。

写入 Memory 之前必须：

1. 经过 Human Review
2. 经过 explicit Memory Contract 校验
3. 经过 Authority Grant

---

## 下一步

Future Architecture Cycle：

- Memory 具体实现（写入接口、Audit Trail、版本控制）
- Human Approval 的接口契约
- Memory ↔ State 的关系定义