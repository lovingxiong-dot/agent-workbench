# ADR-020: Human Approval Boundary

> **Status**: Architecture Review (Phase 3.16)
> **Date**: 2026-07-25
> **Scope**: What MUST go through Human Authority?

---

## 核心问题

> **哪些事情必须经过 Human Authority？**

---

## 当前倾向（Phase 3.16 Review）

**Human Authority 是 Root Authority，不可被绕过。**

正确链路：

```
Information
    ↓
Insight
    ↓
Decision Support
    ↓
Human Approval
    ↓
Execution
```

❌ 错误链路（必须禁止）：

```
Insight
 ↓
Agent decides
 ↓
Agent executes
```

---

## 决策

### D-020.1: 必须经过 Human Authority 的操作

| 操作 | 必须 Human Authority | 原因 |
|------|----------------------|------|
| Persistent Memory Write | ✅ | 长期状态改变 |
| Agent Create / Archive | ✅ | Lifecycle 决定 |
| Cross-System Action | ✅ | 影响范围超出 Agent |
| Intent Modification | ✅ | User intent 是 root |
| Authority Grant | ✅ | 权限提升 |
| Execution Permission | ✅ | Execution 触发 |

### D-020.2: 不需要 Human Authority 的操作

| 操作 | 不需要 Human Authority |
|------|--------------------------|
| Observation Produce | ❌ (Producer 自主) |
| Insight Generate (rule-based) | ❌ (Adapter 纯函数) |
| Decision Options Generate | ❌ (Adapter 纯函数) |
| Session Internal | ❌ (Runtime 内部) |
| Contract Validation | ❌ (协议内置) |
| Read-Only Access | ❌ (Read ≠ Write) |

### D-020.3: Human Approval 必须可审计

每次 Human Approval：

- Timestamp
- Decision Artifact ID
- Human Identity
- Approval / Rejection
- Optional Reason

Audit Trail 是 **persistent**。

### D-020.4: Human 可以 Override 任何 Decision

Human Authority 是 Root。任何 Decision / Insight / Execution 都可以被 Human Override。

```
Human
   ↓
"Reject this Decision"
   ↓
Decision Artifact 标记为 Rejected
   ↓
不会触发 Execution
```

不是：

```
Agent
   ↓
Decided
   ↓
"Human 不要干预"
```

---

## 禁止的反模式

### 反模式 1: Agent Auto-Execute Decision

```
Decision Support
   ↓
"High Confidence"
   ↓
Auto-Execute
   ↓
（绕过 Human Authority）
```

❌ 任何 Execution 必须经过 Human Authority。

### 反模式 2: Authority Escalation

```
Agent
   ↓
"我需要更多权限"
   ↓
Self-Grant Authority
```

❌ Authority 只能从 Human / Workspace 获得，Agent 不能自授权。

### 反模式 3: Implicit Human Approval

```
"User 已经在线，所以同意"
   ↓
Agent 执行
```

❌ 必须有 **explicit** Human Approval。

### 反模式 4: 跳过 Audit

```
Human Approved
   ↓
无 Audit
   ↓
无 Accountability
```

❌ 任何 Human Approval 必须有 Audit Trail。

---

## Human Approval 的接口形态

**未具体实现（Phase 3.16 不进入 Implementation）**，但接口契约应该是：

```python
class HumanApprovalInterface:
    def request_approval(
        self,
        decision_artifact: DecisionArtifact,
        timeout: Optional[float] = None,
    ) -> ApprovalResult:
        """Request human approval for a decision."""
        ...

class ApprovalResult:
    approved: bool
    approver_id: str  # Human identity
    timestamp: float
    reason: Optional[str]
```

不是：

```
Agent Auto-Execute
```

---

## 与其他 ADR 的关系

- **ADR-016 State Ownership**：Human Authority 可以授予 State Owner
- **ADR-017 Persistence Authority**：Memory Write 必须经过 Human Approval
- **ADR-018 Agent Lifecycle**：Agent Create / Archive 必须经过 Human
- **ADR-019 Runtime Authority**：Runtime 不能跨过 Human Approval

---

## 关键判断（Insight ≠ Auto-Execute）

Phase 3.14 已经强调：

> **Insight ≠ AI Summary, Insight ≠ Decision**

Phase 3.15 已经强调：

> **Decision ≠ Execution, Decision ≠ Auto-Execute**

Phase 3.16 ADR-020 进一步明确：

> **Insight + Decision → Human Approval → Execution**

不是：

> **Insight + Decision → Agent Auto-Execute**

---

## 与 Phase 3 的关系

```
Phase 3.11 Runtime      (Execution Engine)
Phase 3.12 Observation  (What happened)
Phase 3.13 Presentation (How to display)
Phase 3.14 Insight      (What does it mean)
Phase 3.15 Decision     (What should we consider)

Phase 3.16 ADR-020      (Human Authority decides)
                       ↓
Future Execution        (After Human Approval)
```

---

## 下一步

Future Architecture Cycle：

- Human Approval Interface 具体实现
- Approval Timeout / Default Rejection 策略
- Multi-Human Approval（如需）
- Authority 撤销机制