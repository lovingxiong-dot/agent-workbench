# ADR-014 — Cancellation Precedence Rule

> **Status**: ACCEPTED
> **Date**: 2026-07-25
> **Supersedes**: None
> **Scope**: Runtime — Execution Lifecycle 终态优先级规则

---

## 1. Purpose

冻结 Runtime 取消与失败之间的优先级关系，避免在并发场景下产生非法状态（如 `CANCELLED → FAILED`）。这是 Phase 3.11-C Architecture Review 的关键发现。

---

## 2. Context

### 2.1 竞态问题

Phase 3.11-C 实现 `Orchestrator.cancel()` 后，发现如下竞态：

```
Thread A (用户/调度):              Thread B (Worker):
cancel(task_id)
  ├─ control.cancel(reason)
  ├─ state → CANCELLED
  └─ publish(TASK_CANCELLED)         execute()
                                       ├─ 执行引擎调用
                                       └─ 抛出 Exception
                                          └─ _fail_task()
                                             ├─ state CANCELLED → FAILED ❌
                                             └─ 非法迁移
```

`cancel()` 与 worker `execute()` 之间存在天然竞态。如果 Worker 在 cancel 完成之后才检测到异常，会试图把状态从 `CANCELLED` 迁移到 `FAILED`，触发状态机拒绝，并产生不一致的 Trace。

### 2.2 现有修复

Phase 3.11-C 实现时已通过 `_execute_task` 中的状态守卫缓解：

```python
except TaskCancelledError:
    current = self.state(task_id)
    if current not in (RuntimeState.CANCELLED, RuntimeState.COMPLETED, RuntimeState.FAILED):
        self._fail_task(task_id, {"reason": "cancelled during execution"})
```

但这一修复是隐式行为，必须升级为正式 ADR 冻结。

---

## 3. Decision

### 3.1 Cancellation Wins Over Failure

**规则**：Cancellation 是终态意图（user / system / timeout intent），优先级高于 Worker 因取消请求而产生的异常。

### 3.2 终态优先级

```
COMPLETED > CANCELLED > FAILED
```

含义：

- 如果 Task 已进入 `COMPLETED`，视为正常完成，**任何后续操作都不能改变状态**（包括 cancel）。
- 如果 cancel 已发生，状态进入 `CANCELLED`，后续 Worker 异常**不得覆盖**为 `FAILED`。
- 如果 cancel 与 Worker 异常同时发生，最终状态为 `CANCELLED`。

### 3.3 状态机不变量

```
COMPLETED ∩ CANCELLED ∩ FAILED = ∅
```

三个终态两两互斥。一旦任务进入任一终态，状态机拒绝向其他终态的迁移。

### 3.4 实现约束

| 约束 | 说明 |
|------|------|
| `cancel()` 必须检查当前终态 | 已在终态（COMPLETED/FAILED/CANCELLED）则返回 `False`，不发布事件 |
| Worker `execute()` 必须捕获 `TaskCancelledError` | 该异常**优先**于其他异常被处理 |
| Worker 异常处理路径必须做终态守卫 | 只有当前状态非终态时才能调用 `_fail_task()` |
| `_fail_task()` 必须由状态机守卫 | 状态机应禁止从终态迁移到 FAILED |

### 3.5 Test 守卫

必须存在以下测试：

| 测试 | 验证 |
|------|------|
| `test_cancel_completed_task_returns_false` | COMPLETED 后 cancel 返回 False |
| `test_cancel_failed_task_returns_false` | FAILED 后 cancel 返回 False |
| `test_cancel_already_cancelled_returns_false` | 重复 cancel 幂等 |
| `test_worker_exception_after_cancel_no_state_change` | cancel 后 Worker 异常不得覆盖状态 |
| `test_concurrent_cancel_and_worker_exception` | 真并发场景下终态保持 |

---

## 4. Consequences

### Positive

- 冻结终态优先级规则，避免 Runtime 行为不确定性
- 为 Phase 3.11-D Parent-Child Execution 的传播规则提供基础（parent CANCELLED → child CANCELLED，而非 child FAILED）
- 减少 Trace 数据不一致风险

### Negative

- Worker 异常被"吞掉"的场景必须通过 TASK_CANCELLED 事件携带 reason，外部才能感知
- 实现层必须在多个路径放置终态守卫（防止未来重构丢失）

### Risk

- 如果未来 PauseToken 引入，状态机会增加 `PAUSED` 中间态，本规则需要扩展为"终态优先级 + 中间态可恢复"模型
- Parent-Child Execution 引入后，需要新增"Parent state propagation" 规则（Phase 3.11-D 范围）

---

## 5. References

- Phase 3.11-A Execution Identity Model Design v0.2
- `v6/runtime/orchestrator.py` — `cancel()`, `_execute_task()` 终态守卫
- `v6/runtime/state_machine.py` — 终态迁移拒绝
- `tests/v6/runtime/test_phase3_11_c_cancellation.py` — TestOrchestratorCancel / TestCooperativeCancellation
- ADR-013 — Runtime Lifecycle Event Extension (TASK_CANCELLED)