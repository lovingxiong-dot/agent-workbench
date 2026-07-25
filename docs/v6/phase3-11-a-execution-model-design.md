# Phase 3.11-A — Execution Identity Model Design

> **Status**: DESIGN REVIEWED — AMENDMENT ACCEPTED (v0.2)
> **Date**: 2026-07-25
> **Phase**: 3.11-A.1
> **Supersedes**: v0.1 (2026-07-25)
> **Depends on**: Phase 3.10 (CLOSED), ADR-012 (PROPOSAL), ADR-013 (ACCEPTED), ADR-014 (ACCEPTED)

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial design: ExecutionMetadata, single-state Lifecycle, standalone CancellationToken |
| v0.2 | 2026-07-25 | Amendment: RuntimeContext.execution 挂载, Lifecycle/Activity 双状态模型, ExecutionControl 抽象 |
| v0.2.1 | 2026-07-25 | Add Cancellation Precedence Rule (ADR-014), Terminal State Mutually Exclusive Invariant, ExecutionControl 长期归属 |

---

## 1. Purpose

定义 Phase 3.11 的 Execution Identity Model，包括：
- `ExecutionMetadata` Schema + `RuntimeContext.execution` 挂载
- Lifecycle / Activity 双状态模型
- `ExecutionControl` 抽象（CancellationToken + 未来 PauseToken/CheckpointToken）
- Parent-Child Execution Relation

设计冻结后，Phase 3.11-B/C/D 按此设计实现。

---

## 2. Current State Analysis

### 2.1 现有模型

| 模型 | 文件 | 执行身份相关字段 |
|------|------|-----------------|
| `Task` | `v6/runtime/task.py` | `id`, `metadata: dict` |
| `RuntimeContext` | `v6/runtime/context.py` | `task_id`, `status: RuntimeState`, `metadata: dict`, `created_at: float` |
| `RuntimeEvent` | `v6/runtime/event_bus.py` | `task_id`, `trace_id`, `source`, `phase`, `timestamp` |
| `RuntimeState` | `v6/runtime/enums.py` | 10 states, 4 used in orchestrator（混合 Lifecycle + Activity） |
| `RuntimeStateMachine` | `v6/runtime/state_machine.py` | 完整迁移规则，CANCELLED/COMPLETED 为终态 |

### 2.2 当前 Gap

| Gap | 影响 |
|-----|------|
| 无 `execution_id` | 同一次 Task 的多次重试无法区分 |
| 无 `parent_execution_id` | 无法建立 Agent 父子关系 |
| 无结构化 timeout | 依赖隐式 `metadata` dict |
| 无 `CancellationToken` | 无法安全取消运行中任务 |
| `RuntimeEvent` 无 `parent_id` | Trace 树无法建立父子关系（不修改 RuntimeEvent） |
| Lifecycle 与 Activity 混合 | 无法表达 "EXECUTING + STREAMING" 等组合状态 |
| `QUEUED` 定义但未使用 | 任务提交后直接进入 PLANNING |
| 无 `ExecutionControl` 抽象 | CancellationToken 成孤立模块，无法扩展 pause/resume |

---

## 3. Design: ExecutionMetadata

### 3.1 Schema

```python
# 新增文件: v6/runtime/execution_metadata.py

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ExecutionMetadata:
    """单次执行的身份元数据。

    ExecutionMetadata 是 Execution Identity，不是 Task Identity。
    关系：
        Task 1 ──── ExecutionMetadata A  (第 1 次执行)
              └──── ExecutionMetadata B  (retry 第 2 次执行)

    禁止：
    - 写入 RuntimeEvent.payload（避免污染 Protocol）
    - 替代 Task（Task 是业务模型，ExecutionMetadata 是执行模型）
    - 包含 UI 相关字段
    """

    # ── Identity ──────────────────────────────────────
    execution_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    task_id: str = ""
    parent_execution_id: Optional[str] = None

    # ── Timestamps ────────────────────────────────────
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    # ── Control ───────────────────────────────────────
    timeout_seconds: Optional[float] = None

    # ── Retry ─────────────────────────────────────────
    retry_count: int = 0
    max_retries: int = 0

    # ── Priority ──────────────────────────────────────
    priority: int = 0  # 0 = default, higher = more urgent

    # ── Tags ──────────────────────────────────────────
    tags: list[str] = field(default_factory=list)


    # ── Computed Properties ───────────────────────────

    @property
    def is_timed_out(self) -> bool:
        if self.timeout_seconds is None or self.started_at is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        return elapsed > self.timeout_seconds

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at is None:
            return None
        end = self.finished_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()

    @property
    def is_root_execution(self) -> bool:
        return self.parent_execution_id is None

    @property
    def is_retry(self) -> bool:
        return self.retry_count > 0
```

### 3.2 与 Task / RuntimeContext 的关系

```
Task                    ExecutionMetadata          RuntimeContext
─────                   ─────────────────          ──────────────
id (task_id)    ──────► task_id                    task_id
                         execution_id ◄── new
                         parent_execution_id ◄── new
capability                                           phase
payload                                              messages
created_at       ──────► created_at                  created_at
                         started_at ◄── new
                         finished_at ◄── new
                         timeout_seconds ◄── new
                         retry_count ◄── new
                         priority ◄── new
                         tags ◄── new
```

### 3.3 挂载方式（Amendment: 直接字段，非 metadata dict）

**v0.1（旧）**：
```python
ctx.metadata["execution"] = exec_meta  # ❌ 扩展容器承载核心身份
```

**v0.2（新）**：
```python
# RuntimeContext 新增字段：
execution: Optional[ExecutionMetadata] = None

# Orchestrator.submit() 内部：
ctx.execution = ExecutionMetadata(
    task_id=task.id,
    timeout_seconds=timeout,
)
```

**原因**：`metadata` 是扩展容器，不应承载 Runtime Core Identity。`execution` 作为 RuntimeContext 一级字段，与 `task_id`/`status` 同级。

---

## 4. Design: Lifecycle / Activity 双状态模型

### 4.1 问题：单状态模型混合两个维度

当前 `RuntimeState` 枚举混合了任务生命周期（Lifecycle）和当前执行活动（Activity）：

```
RuntimeState 混合:
  CREATED     ← lifecycle
  QUEUED      ← lifecycle
  PLANNING    ← lifecycle
  EXECUTING   ← lifecycle
  RUNNING     ← activity
  WAITING     ← activity
  PAUSED      ← activity
  CANCELLED   ← lifecycle
  COMPLETED   ← lifecycle
  FAILED      ← lifecycle
```

问题：无法表达 "EXECUTING + STREAMING"（LLM 流式）、"EXECUTING + WAITING"（Tool 等待）、"EXECUTING + RUNNING"（Workflow 执行）等组合状态。

### 4.2 目标：双状态模型

#### LifecycleState — 任务生命周期

```python
# 新增: v6/runtime/enums.py

class LifecycleState(str, Enum):
    """任务生命周期状态。

    每个 Task 在当前时刻仅处于一个 LifecycleState。
    终态：COMPLETED / FAILED / CANCELLED。
    """

    CREATED = "created"       # 任务已创建，尚未提交
    QUEUED = "queued"         # 已提交到调度队列，等待分配
    PLANNING = "planning"     # 正在规划执行策略
    EXECUTING = "executing"   # 正在执行（ActivityState 描述具体活动）
    COMPLETED = "completed"   # 终态：执行成功
    FAILED = "failed"         # 终态：执行失败
    CANCELLED = "cancelled"   # 终态：已取消
```

```
CREATED
    │
    ▼
QUEUED                          ◄── 新增：等待调度
    │
    ▼
PLANNING
    │
    ▼
EXECUTING                       ◄── ActivityState 描述当前活动
    │
    ├──────────────────────────► COMPLETED
    │
    ├──────────────────────────► FAILED
    │
    └──────────────────────────► CANCELLED     ◄── 新增：取消路径
```

#### ActivityState — 当前执行活动

```python
class ActivityState(str, Enum):
    """当前执行活动状态。

    仅在 LifecycleState.EXECUTING 期间有意义。
    其他 LifecycleState 下固定为 IDLE。
    """

    IDLE = "idle"           # 无活动（非 EXECUTING 状态）
    RUNNING = "running"     # 正在执行（通用）
    STREAMING = "streaming" # 流式输出中（LLM）
    WAITING = "waiting"     # 等待外部事件（Tool/MCP/API）
    PAUSED = "paused"       # 已暂停（用户或系统触发）
```

```
IDLE
    │
    ├──► RUNNING      (通用执行)
    │
    ├──► STREAMING    (LLM 流式输出)
    │
    ├──► WAITING      (Tool/MCP 等待)
    │
    └──► PAUSED       (暂停)
```

#### 组合示例

| 场景 | LifecycleState | ActivityState |
|------|---------------|---------------|
| 任务刚创建 | CREATED | IDLE |
| 排队等待 | QUEUED | IDLE |
| 规划中 | PLANNING | IDLE |
| LLM 流式输出 | EXECUTING | STREAMING |
| Tool 调用等待 | EXECUTING | WAITING |
| Workflow 执行 | EXECUTING | RUNNING |
| 用户暂停 | EXECUTING | PAUSED |
| 完成 | COMPLETED | IDLE |
| 失败 | FAILED | IDLE |
| 取消 | CANCELLED | IDLE |

### 4.3 向后兼容

RuntimeContext 保留 `status: RuntimeState` 字段，提供 `lifecycle` 和 `activity` 新字段：

```python
@dataclass
class RuntimeContext:
    # 保留旧字段（向后兼容）
    status: RuntimeState = RuntimeState.CREATED

    # 新字段（Phase 3.11）
    lifecycle: LifecycleState = LifecycleState.CREATED
    activity: ActivityState = ActivityState.IDLE
    execution: Optional[ExecutionMetadata] = None
```

旧代码仍可通过 `ctx.status` 访问，新代码使用 `ctx.lifecycle` + `ctx.activity`。

### 4.4 LifecycleState 迁移规则

| From | To | 说明 |
|------|-----|------|
| CREATED | QUEUED | 提交到调度队列 |
| QUEUED | PLANNING | 调度器分配执行 |
| PLANNING | EXECUTING | 开始执行 |
| EXECUTING | COMPLETED | 执行成功 |
| EXECUTING | FAILED | 执行失败 |
| EXECUTING | CANCELLED | 取消 |
| QUEUED | CANCELLED | 排队中取消 |
| PLANNING | CANCELLED | 规划中取消 |

### 4.5 ActivityState 迁移规则

| From | To | 触发条件 |
|------|-----|---------|
| IDLE | RUNNING | 引擎开始执行 |
| IDLE | STREAMING | 引擎开始流式输出 |
| RUNNING | STREAMING | 检测到流式输出 |
| STREAMING | RUNNING | 流式结束，继续执行 |
| RUNNING | WAITING | Tool 调用/MCP 等待 |
| WAITING | RUNNING | Tool 返回结果 |
| RUNNING | PAUSED | 用户暂停 |
| PAUSED | RUNNING | 用户恢复 |
| RUNNING | IDLE | 执行完成/失败/取消 |
| STREAMING | IDLE | 流式完成/失败/取消 |
| WAITING | IDLE | 等待超时/取消 |

### 4.6 关键约束：内部状态迁移不发布新 Event

Lifecycle `CREATED → QUEUED`、`QUEUED → PLANNING`、Activity `IDLE → STREAMING` 等内部迁移**不发布新 RuntimeEvent**，避免破坏 Presentation Layer 兼容性。

**例外**：`CANCELLED` 需要发布 `TASK_CANCELLED` 事件（见 ADR-013）。

---

## 5. Design: ExecutionControl

### 5.1 问题：CancellationToken 不应成为孤立模块

未来 Runtime Control 必然包含 cancel、pause、resume、checkpoint、retry。不应让 `cancellation.py` 成为新孤立模块。

### 5.2 ExecutionControl 抽象

```python
# 新增文件: v6/runtime/execution_control.py

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


class TaskCancelledError(Exception):
    """任务被取消时抛出的异常。"""

    def __init__(self, task_id: str = "", reason: str = "") -> None:
        self.task_id = task_id
        self.reason = reason
        super().__init__(
            f"Task {task_id} cancelled: {reason}" if task_id else f"Task cancelled: {reason}"
        )


class CancellationToken:
    """协作式取消令牌。

    设计原则：
    - 不使用 thread.kill()（Python 不支持安全 kill）
    - Worker 线程定期检查 token，主动停止
    - 取消信号通过 threading.Event 传播
    """

    def __init__(self) -> None:
        self._event = threading.Event()
        self._reason: str = ""

    def cancel(self, reason: str = "") -> None:
        self._reason = reason or self._reason
        self._event.set()

    def is_cancelled(self) -> bool:
        return self._event.is_set()

    @property
    def reason(self) -> str:
        return self._reason

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise TaskCancelledError(reason=self._reason)

    def wait(self, timeout: Optional[float] = None) -> bool:
        return self._event.wait(timeout=timeout)


@dataclass
class ExecutionControl:
    """执行控制容器。

    聚合所有执行控制令牌，避免 CancellationToken 成为孤立模块。
    未来扩展：
        - pause: PauseToken
        - checkpoint: CheckpointToken
    """

    cancellation: CancellationToken = field(default_factory=CancellationToken)

    # Future:
    # pause: PauseToken = field(default_factory=PauseToken)
    # checkpoint: CheckpointToken = field(default_factory=CheckpointToken)

    @property
    def is_cancelled(self) -> bool:
        return self.cancellation.is_cancelled()

    def cancel(self, reason: str = "") -> None:
        self.cancellation.cancel(reason)

    def raise_if_cancelled(self) -> None:
        self.cancellation.raise_if_cancelled()
```

### 5.3 挂载到 ExecutionMetadata

```python
# ExecutionMetadata 挂载 ExecutionControl：
exec_meta = ExecutionMetadata(
    task_id=task.id,
    timeout_seconds=timeout,
)
control = ExecutionControl()
ctx.execution = exec_meta
ctx.control = control  # 或 ctx.execution.control
```

### 5.4 取消流程

```
                cancel(task_id)
                     │
                     ▼
          Orchestrator._cancel_task()
                     │
                ┌────┴────┐
                │         │
          control.cancel()  publish
          (set Event)      TASK_CANCELLED
                │         │
                ▼         ▼
          Worker checks   Presentation
          token per        Layer
          step
                │
                ▼
          raise TaskCancelledError
                │
                ▼
          Orchestrator catches
                │
                ▼
          lifecycle → CANCELLED
          activity → IDLE
```

### 5.5 Timeout 统一走 Cancellation

```python
def _start_timeout_timer(self, task_id: str, control: ExecutionControl, timeout: float) -> None:
    def _on_timeout():
        control.cancel(reason=f"timeout after {timeout}s")
        self._cancel_task(task_id, reason=f"timeout after {timeout}s")

    timer = threading.Timer(timeout, _on_timeout)
    timer.daemon = True
    timer.start()
```

### 5.6 长期归属建议（Phase 3.11-D 前确认）

当前实现：`ctx.control`（RuntimeContext 一级字段）。

长期推荐：`ctx.execution.control`（ExecutionControl 属于 Execution 的属性）。

**理由**：ExecutionControl 是 Execution 生命周期内的控制平面，而非 Context 本身的属性。在 Phase 3.11-C 中保留 `ctx.control` 作为临时挂载以减少 churn，但 Phase 3.11-D Parent-Child Execution 引入前必须确定最终归属。

---

## 5.7 Cancellation Precedence Rule（ADR-014）

### 5.7.1 问题：cancel() 与 worker 线程的竞态

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

如果 cancel 已经发生，后续 Worker 异常不能覆盖状态为 FAILED。

### 5.7.2 规则：Cancellation Wins Over Failure

终态优先级：

```
COMPLETED > CANCELLED > FAILED
```

- COMPLETED 是正常完成，cancel 不应改变（cancel 拒绝终态任务）
- CANCELLED 是终态意图，Worker 后续异常不得覆盖为 FAILED
- 如果 cancel 与 Worker 异常同时发生，最终状态为 CANCELLED

### 5.7.3 终态互斥不变量（Terminal State Mutually Exclusive Rule）

```
COMPLETED ∩ CANCELLED ∩ FAILED = ∅
```

三个终态两两互斥。一旦进入任一终态，状态机拒绝向其他终态迁移。

这一规则是 Phase 3.11-D Parent-Child Execution 引入"Parent state propagation"的必要前置。否则会出现：

```
Parent FAILED → Child ???  ← 未定义
Parent CANCELLED → Child FAILED  ← 非法
```

### 5.7.4 实现约束

| 约束 | 说明 |
|------|------|
| `cancel()` 必须检查当前终态 | 已在终态则返回 `False` |
| Worker 必须捕获 `TaskCancelledError` | 优先于其他异常处理 |
| Worker 异常处理必须做终态守卫 | 仅非终态可调 `_fail_task()` |
| 状态机禁止终态间迁移 | 状态机层守卫 |

### 5.7.5 Test 守卫

- `test_cancel_completed_task_returns_false`
- `test_cancel_failed_task_returns_false`
- `test_worker_exception_after_cancel_no_state_change`
- `test_concurrent_cancel_and_worker_exception`

详见 [ADR-014](.project/decisions/ADR-014-cancellation-precedence-rule.md)。

---

## 6. Design: Parent-Child Execution Relation

### 6.1 存储位置

`ExecutionMetadata.parent_execution_id`，**不修改 RuntimeEvent**。

### 6.2 传播到 Presentation Layer

```python
# EventAdapter 内部：
def _on_task_started(self, event: RuntimeEvent) -> None:
    ctx = self._layer.get_context(event.task_id)
    parent_id = ctx.execution.parent_execution_id if ctx.execution else ""

    trace_model = TracePresentationModel.from_runtime_event(
        event,
        parent_id=parent_id,  # ← 从 ExecutionMetadata 读取，非 RuntimeEvent
    )
```

### 6.3 未来 Agent 树

```
Planner Agent
    execution_id: exec-001
    parent_execution_id: None
    │
    ├── Research Agent
    │   execution_id: exec-002
    │   parent_execution_id: exec-001
    │
    ├── Coding Agent
    │   execution_id: exec-003
    │   parent_execution_id: exec-001
    │
    └── Test Agent
        execution_id: exec-004
        parent_execution_id: exec-001
```

---

## 7. Event Contract: ADR-013

`TASK_CANCELLED` 是新增 RuntimeEventType，属于 Protocol Extension，需要 ADR 记录。

详见 [ADR-013](.project/decisions/ADR-013-runtime-lifecycle-event-extension.md)。

### 新增事件类型

```python
# v6/runtime/event_bus.py — RuntimeEventType（additive only）
TASK_CANCELLED = "task.cancelled"
```

### 不变部分

- `RuntimeEvent` dataclass schema **零修改**
- 不新增 `task.queued` / `task.streaming` 等内部状态事件
- `TASK_CANCELLED` 的 payload 仅含 `{"reason": str}`，不包含 execution_metadata

---

## 8. Phase 3.11 完整拆解（更新）

| Phase | 内容 | 依赖 | 状态 |
|-------|------|------|------|
| **3.11-A.1** | Design Amendment v0.2（本文档） | 3.11-A v0.1 | ✅ Frozen (Amendment Accepted) |
| **3.11-B** | Lifecycle + Activity 双状态接入 Orchestrator | 3.11-A.1 | ✅ Complete |
| **3.11-C** | ExecutionControl + Cancellation + Timeout | 3.11-A.1 | ✅ Complete + Documentation Finalized |
| **3.11-D** | Parent-Child Execution | 3.11-A.1, ADR-014 | ⏳ Pending Design Review |
| **3.11-E** | Freeze Validation（回归 + Contract 零修改） | 3.11-B/C/D | ⏳ Pending |

---

## 9. Files Plan（更新）

### 新增文件

| 文件 | 内容 |
|------|------|
| `v6/runtime/execution_metadata.py` | ExecutionMetadata dataclass |
| `v6/runtime/execution_control.py` | ExecutionControl + CancellationToken + TaskCancelledError |
| `tests/v6/runtime/test_phase3_11_b_lifecycle.py` | Lifecycle + Activity 双状态测试 |
| `tests/v6/runtime/test_phase3_11_c_cancellation.py` | ExecutionControl + Cancellation 测试 |
| `tests/v6/runtime/test_phase3_11_d_parent_child.py` | Parent-Child 测试 |
| `tests/v6/runtime/test_phase3_11_e_freeze.py` | Freeze 回归测试 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `v6/runtime/context.py` | 新增 `execution: ExecutionMetadata`、`lifecycle: LifecycleState`、`activity: ActivityState` 字段 |
| `v6/runtime/enums.py` | 新增 `LifecycleState`、`ActivityState` 枚举（additive only） |
| `v6/runtime/event_bus.py` | 新增 `TASK_CANCELLED` 事件类型（additive only） |
| `v6/runtime/orchestrator.py` | 接入双状态模型、ExecutionControl、Timeout、Parent-Child |

### 禁止修改

| 文件 | 原因 |
|------|------|
| `v6/runtime/event_bus.py` (core) | RuntimeEvent schema 冻结 |
| `v6/runtime/task.py` | Task 模型冻结 |
| `agent_workbench/runtime/*` | Runtime Kernel Contracts 冻结 |
| `v6/presentation/*` | Presentation Contract 冻结 |

---

## 10. Frozen Boundary Summary

### 已冻结（Frozen）

| 项目 | 决策 |
|------|------|
| Task ≠ Execution Identity | `execution_id` 独立于 `task_id` |
| `execution_id` 独立存在 | 每次执行唯一 ID |
| `parent_execution_id` | 存储在 ExecutionMetadata，不进入 RuntimeEvent |
| RuntimeEvent 不增加 execution 字段 | schema 零修改 |
| Cooperative Cancellation | `threading.Event`，非 `thread.kill()` |
| ExecutionMetadata 作为 RuntimeContext 一级字段 | `ctx.execution`，非 `ctx.metadata["execution"]` |
| Lifecycle / Activity 分离 | 双状态模型，防止 State Explosion |
| ExecutionControl 抽象 | 聚合 CancellationToken + 未来 PauseToken/CheckpointToken |
| Cancellation Precedence Rule | ADR-014：Cancellation wins over Failure |
| Terminal State Mutually Exclusive | COMPLETED ∩ CANCELLED ∩ FAILED = ∅ |
| `TASK_CANCELLED` 事件类型 | ADR-013 ACCEPTED，Protocol Extension 仅 1 个事件 |

### 待 Phase 3.11-D 确认

| 项目 | 状态 |
|------|------|
| ExecutionControl 最终归属 | `ctx.control`（当前）vs `ctx.execution.control`（长期推荐） |

---

## 11. Design Review Gate

| 检查项 | 状态 |
|--------|------|
| ExecutionMetadata 不替代 Task | PASS |
| ExecutionMetadata 不写入 RuntimeEvent.payload | PASS |
| `ctx.execution` 一级字段（非 metadata dict） | PASS |
| Lifecycle / Activity 双状态分离 | PASS |
| CancellationToken 不使用 thread.kill() | PASS |
| Timeout 走 Cancellation 统一入口 | PASS |
| ExecutionControl 抽象（非孤立 cancellation.py） | PASS |
| Parent-child 不修改 RuntimeEvent | PASS |
| 内部状态迁移不发布新 Event | PASS |
| 仅新增 1 个 RuntimeEventType（TASK_CANCELLED） | PASS |
| 不修改 Frozen Contracts | PASS |
| Cancellation Precedence Rule | PASS（ADR-014，竞态已通过终态守卫解决） |
| Terminal State Mutually Exclusive | PASS（状态机禁止终态间迁移） |
| ADR-013 状态 | ACCEPTED |
| ADR-014 状态 | ACCEPTED |