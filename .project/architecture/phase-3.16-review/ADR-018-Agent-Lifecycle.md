# ADR-018: Agent Lifecycle

> **Status**: Architecture Review (Phase 3.16)
> **Date**: 2026-07-25
> **Scope**: Where is the agent lifecycle managed (created → destroyed)?

---

## 核心问题

> **Agent 从创建到销毁的生命周期在哪里管理？**

```
Created
 ↓
Initialized
 ↓
Active
 ↓
Suspended
 ↓
Archived
```

谁拥有 **状态转换权限**。

---

## 当前倾向（Phase 3.16 Review）

**Lifecycle Authority 不属于 Runtime。**

Runtime 可以触发 Lifecycle 事件，但：

- 不能决定 Agent 是否存在
- 不能决定 Agent 是否 Archived
- 这些决定属于 **Human Authority** 或 **Workspace Authority**

---

## 决策

### D-018.1: Agent Lifecycle States

```
       Created
          ↓
      Initialized
          ↓
         Active
        ↙    ↘
   Suspended  Resumed (back to Active)
        ↓
     Archived
        ↓
     Destroyed
```

| State | Authority to Transition |
|-------|--------------------------|
| Created → Initialized | Workspace / Factory |
| Initialized → Active | Workspace / Factory |
| Active → Suspended | Human / Workspace |
| Suspended → Active (Resume) | Human / Workspace |
| Active → Archived | Human Authority (explicit) |
| Archived → Destroyed | System (cleanup) |

### D-018.2: Runtime 不创建 Agent

```
Runtime
   ↓
不能 Create Agent
   ↓
不能 Archive Agent
```

Runtime 只管理 Runtime 内部 lifecycle（session, task, event），不管理 Agent lifecycle。

### D-018.3: Agent 不能自我 Archive

```
Agent
   ↓
"我完成了任务"
   ↓
Self-Archive
```

❌ Agent 不能自我 Archive。

Agent 只能：

- 标记 Ready-to-Archive
- 等待 Human / Workspace Authority 决定

### D-018.4: Lifecycle 转换必须经过 Audit

每次 Lifecycle 转换：

- Timestamp
- From → To states
- Authority Grant (who triggered)
- Reason

Audit Trail 是 **persistent**，可以 read-only access。

---

## 禁止的反模式

### 反模式 1: Runtime Auto-Archive

```
Runtime
   ↓
"任务完成"
   ↓
Auto-Archive Agent
   ↓
Agent 状态被 Runtime 单方面改变
```

❌ Runtime 越权。

### 反模式 2: Agent Self-Destruct

```
Agent
   ↓
"我决定终止"
   ↓
Self-Destroy
```

❌ Agent 不能自我销毁。Agent 是被创建的，不是 self-owning。

### 反模式 3: 无 Audit Trail

```
Archived
   ↓
无 Trace
```

❌ 任何 Lifecycle 转换必须有 Audit Trail。

---

## 与其他 ADR 的关系

- **ADR-016 State Ownership**：Agent 内部 State 的 Owner
- **ADR-017 Persistence Authority**：Lifecycle Audit Trail 是 Write Authority 的一部分
- **ADR-019 Runtime Authority**：Runtime 可以触发 Lifecycle 事件，但不决定 Lifecycle
- **ADR-020 Human Approval Boundary**：Archive / Destroy 必须经过 Human Authority

---

## 与 Phase 3.11 Runtime 的关系

Phase 3.11 Runtime Kernel (v6.16.0-alpha Frozen) 提供的：

- Lifecycle Event Extension (ADR-013)
- Cancellation Precedence (ADR-014)
- Parent-Child Execution (ADR-015)

这些都是 **Runtime Internal Lifecycle**，不是 **Agent Lifecycle**。

**Agent Lifecycle 是更高层概念，Owner 是 Human / Workspace，不是 Runtime。**

---

## 下一步

Future Architecture Cycle：

- Agent Instance 实现（如需要）
- Workspace Authority 的具体权限模型
- Audit Trail 的具体存储格式