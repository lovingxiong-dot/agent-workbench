# Phase 3.11-D — Parent-Child Execution Model Design

> **Status**: DESIGN REVIEWED — ARCHITECTURE POLISH ACCEPTED (v0.3)
> **Date**: 2026-07-25
> **Phase**: 3.11-D
> **Supersedes**: v0.2 (2026-07-25)
> **Depends on**: Phase 3.11-A.1 (Frozen), ADR-013 (ACCEPTED), ADR-014 (ACCEPTED)
> **Supplements**: ADR-015 — Parent-Child Execution Propagation (ACCEPTED v0.3)

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial: ExecutionRegistry, propagation rules, ExecutionControl migration |
| v0.2 | 2026-07-25 | 移除 graph fields 入 ExecutionMetadata；CancellationPropagationContext；timeout → deadline；Registry lifecycle |
| v0.3 | 2026-07-25 | Architecture Polish: children_ids active topology references；extend() 内部 enforce depth；origin/chain invariant；PARENT_TIMEOUT → DEADLINE_EXCEEDED；cleanup safe predicate（terminal + descendants terminal + retention expired）；Future DeadlineScheduler ADR |

---

## 1. Purpose

定义 Phase 3.11 Parent-Child Execution Model 完整语义，v0.3 Architecture Polish 强化：

- **Active topology references**：`children_ids` 不再强一致，保留历史引用供 Trace 查询
- **extend() 内部 enforce depth**：不依赖调用方守卫
- **origin/chain invariant**：`chain[0] == origin_execution_id`
- **DEADLINE_EXCEEDED 统一**：移除残留 `PARENT_TIMEOUT`
- **Cleanup safe predicate**：terminal + descendants terminal + retention expired
- **Future DeadlineScheduler**：记录未来演化方向，避免优化变成 breaking change

---

## 2. Design Goals

| 目标 | 优先级 |
|------|--------|
| 支持 Runtime 内部生成子 Execution | P0 |
| 父取消时所有后代被取消 | P0 |
| 父 deadline 到期时所有后代被取消 | P0 |
| 取消理由携带结构化传播链 | P0 |
| Registry lifecycle 完整（cleanup safe） | P0 |
| ExecutionControl 最终归属到 `ctx.execution.control` | P1 |
| 不修改 RuntimeEvent schema / RuntimeState ABI / RuntimeContext ABI | P0 |
| 不修改 Task / Capability / Decision / UI / Provider | P0 |

---

## 3. v0.3 关键变更摘要

### 3.1 children_ids 语义调整（变更 #1，High）

**v0.2**：强一致（cleanup 时立即从 parent.children_ids 移除）

**v0.3**：active topology references

| 维度 | v0.2 强一致 | v0.3 active references |
|------|-----------|----------------------|
| cleanup 时修改 parent.children_ids | 是 | **否** |
| 历史拓扑可查询 | 不可（已删除） | ✅ 可（保留引用） |
| 活跃查询 | 直接遍历 | 需 filter `_nodes` 存在性 |
| Trace 重放 | 受限 | ✅ 完整 |

**新查询 API**：
- `get_active_children(execution_id)` — 过滤后的活跃子节点
- `get_active_descendants(execution_id)` — 过滤后的活跃后代
- `children_ids` 字段保留为 historical topology references（只读）

### 3.2 Cancellation depth enforce 位置（变更 #2，High）

**v0.2**：在 `Orchestrator.cancel()` 调用前检查

**v0.3**：在 `CancellationPropagationContext.extend()` 内部 enforce

```python
# v0.3: Context 是 invariant owner
def extend(self, current_execution_id, new_type=None):
    new_depth = len(self.chain) + 1
    if new_depth > MAX_PROPAGATION_DEPTH:  # 32
        raise CancellationPropagationLimitExceeded(
            depth=new_depth,
            max_depth=MAX_PROPAGATION_DEPTH,
        )
    ...
```

新增异常类型：`CancellationPropagationLimitExceeded`。

### 3.3 origin/chain invariant（变更 #3，Medium）

**v0.3 新增不变量**：`chain[0] == origin_execution_id`

在 `__post_init__` 验证：

```python
@dataclass(frozen=True)
class CancellationPropagationContext:
    def __post_init__(self):
        if self.chain and self.chain[0] != self.origin_execution_id:
            raise ValueError(...)
```

### 3.4 PropagationType 重命名（变更 #4，High）

**v0.3 枚举**：

```python
class PropagationType(str, Enum):
    USER_REQUEST = "user_request"
    PARENT_CANCELLED = "parent_cancelled"
    DEADLINE_EXCEEDED = "deadline_exceeded"  # v0.3 新命名
```

**移除**：`PARENT_TIMEOUT`（v0.1 残留，timeout 语义已被 deadline 取代）

### 3.5 Cleanup Safe Predicate（变更 #6，High）

**v0.3 守卫条件**：

```
node cleanup safe  ⟺  node.terminated_at ≠ None
                       ∧ all_active_descendants.terminated
                       ∧ now ≥ cleanup_eligible_at
```

```python
def _is_cleanup_safe(self, node, now):
    if node.terminated_at is None:
        return False
    if not self._all_active_descendants_terminal(node):
        return False
    if node.cleanup_eligible_at is None or now < node.cleanup_eligible_at:
        return False
    return True
```

`cleanup_eligible_at = terminated_at + retention_seconds`。

### 3.6 Future DeadlineScheduler（变更 #5，Medium）

**v0.3 不实现**，但 ADR-015 Decision #15 记录演化方向：

```
Current: per-execution threading.Thread timer
Future:  centralized DeadlineScheduler (heap-based, 类似 Linux timer wheel)
```

迁移约束：
- `ExecutionMetadata.deadline_at` API 不变
- 触发机制不变（仍发 cancel）
- 仅内部实现替换

---

## 4. Design: ExecutionRegistry (v0.3)

### 4.1 约束

- 不进入 RuntimeContext / RuntimeEvent / ExecutionMetadata（除 parent_execution_id）
- 不暴露到 Presentation Layer

### 4.2 Schema (v0.3)

```python
@dataclass
class ExecutionNode:
    """Orchestrator 内部 Execution 节点（v0.3: 含 cleanup lifecycle）。"""
    execution_id: str
    task_id: str
    parent_execution_id: Optional[str]
    children_ids: List[str] = field(default_factory=list)  # historical references
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    terminated_at: Optional[datetime] = None
    cleanup_eligible_at: Optional[datetime] = None  # v0.3: retention 过期时间


class ExecutionRegistry:
    """Orchestrator 内部的 Execution 树注册表（v0.3: active topology + cleanup safe）。"""

    DEFAULT_RETENTION_SECONDS = 300.0

    def __init__(self, retention_seconds: float = DEFAULT_RETENTION_SECONDS) -> None:
        self._nodes: Dict[str, ExecutionNode] = {}
        self._cleanup_timers: Dict[str, threading.Timer] = {}
        self._retention_seconds = retention_seconds
        self._lock = threading.Lock()

    # ── Register ─────────────────────────────────────────

    def register(self, execution_id, task_id, parent_execution_id=None):
        """注册 Execution 节点。
        
        Raises:
            ValueError: parent 形成环路或 execution_id 重复
        """
        with self._lock:
            if execution_id in self._nodes:
                raise ValueError(f"Duplicate execution_id: {execution_id}")
            
            # 环路检测
            if parent_execution_id is not None:
                current = parent_execution_id
                while current is not None:
                    if current == execution_id:
                        raise ValueError(
                            f"Cycle detected: {execution_id} cannot be its own ancestor"
                        )
                    node = self._nodes.get(current)
                    if node is None:
                        break
                    current = node.parent_execution_id
            
            node = ExecutionNode(
                execution_id=execution_id,
                task_id=task_id,
                parent_execution_id=parent_execution_id,
            )
            self._nodes[execution_id] = node
            
            if parent_execution_id is not None:
                parent = self._nodes.get(parent_execution_id)
                if parent is not None:
                    parent.children_ids.append(execution_id)
                    # 注意：v0.3 不再强一致；即使 parent 已被清理，children_ids 仍保留历史引用

    # ── Lifecycle Markers ────────────────────────────────

    def mark_terminated(self, execution_id: str) -> None:
        """标记节点为终态。"""
        with self._lock:
            node = self._nodes.get(execution_id)
            if node is not None and node.terminated_at is None:
                node.terminated_at = datetime.now(timezone.utc)
                node.cleanup_eligible_at = node.terminated_at + timedelta(
                    seconds=self._retention_seconds
                )

    # ── Cleanup (v0.3: safe predicate) ──────────────────

    def schedule_cleanup(self, execution_id: str) -> None:
        """v0.3: 注册延迟清理（cleanup_eligible_at 后触发）。"""
        with self._lock:
            node = self._nodes.get(execution_id)
            if node is None or node.terminated_at is None:
                return
            
            # 取消已有 timer
            existing = self._cleanup_timers.pop(execution_id, None)
            if existing is not None:
                existing.cancel()
            
            def _cleanup():
                with self._lock:
                    self._cleanup_timers.pop(execution_id, None)
                    current = self._nodes.get(execution_id)
                    if current is None:
                        return
                    if self._is_cleanup_safe(current, datetime.now(timezone.utc)):
                        self._remove_node(execution_id)
                    # 否则：descendants 尚未 terminal，跳过本次 cleanup
                    # 可选：重新 schedule（v0.3 简化：跳过）
            
            delay = max(
                0.0,
                (node.cleanup_eligible_at - datetime.now(timezone.utc)).total_seconds()
            )
            timer = threading.Timer(delay, _cleanup)
            timer.daemon = True
            self._cleanup_timers[execution_id] = timer
            timer.start()

    def _is_cleanup_safe(self, node: ExecutionNode, now: datetime) -> bool:
        """v0.3: cleanup safe predicate（三条件）。"""
        if node.terminated_at is None:
            return False
        if not self._all_active_descendants_terminal(node):
            return False
        if node.cleanup_eligible_at is None or now < node.cleanup_eligible_at:
            return False
        return True

    def _all_active_descendants_terminal(self, node: ExecutionNode) -> bool:
        """所有 active descendants 均已 terminal。"""
        for child_id in node.children_ids:
            child = self._nodes.get(child_id)
            if child is None:
                continue  # 已清理（active filter）
            if child.terminated_at is None:
                return False
            if not self._all_active_descendants_terminal(child):
                return False
        return True

    def _remove_node(self, execution_id: str) -> None:
        """v0.3: 仅从 _nodes 删除，不修改 parent.children_ids。
        
        parent.children_ids 保留为 historical topology references。
        """
        with self._lock:
            self._nodes.pop(execution_id, None)
            # 不修改 parent.children_ids（v0.3 active topology 语义）

    def cleanup_all(self) -> None:
        """Orchestrator 销毁时全量清理。"""
        with self._lock:
            for timer in self._cleanup_timers.values():
                timer.cancel()
            self._cleanup_timers.clear()
            self._nodes.clear()

    # ── Query (v0.3: active filter) ──────────────────────

    def get(self, execution_id: str) -> Optional[ExecutionNode]:
        with self._lock:
            return self._nodes.get(execution_id)

    def get_children(self, execution_id: str) -> List[ExecutionNode]:
        """返回所有 children（historical + active）。"""
        with self._lock:
            node = self._nodes.get(execution_id)
            if node is None:
                return []
            return [
                self._nodes[child_id]
                for child_id in node.children_ids
                if child_id in self._nodes
            ]

    def get_active_children(self, execution_id: str) -> List[ExecutionNode]:
        """v0.3: 返回 active children（filter by _nodes presence）。"""
        return self.get_children(execution_id)  # 已内置 filter

    def get_descendants(self, execution_id: str) -> List[ExecutionNode]:
        """返回所有 descendants（active filter applied）。"""
        with self._lock:
            result: List[ExecutionNode] = []
            self._collect_active_descendants(execution_id, result)
            return result

    def _collect_active_descendants(self, execution_id, result):
        node = self._nodes.get(execution_id)
        if node is None:
            return
        for child_id in node.children_ids:
            child = self._nodes.get(child_id)
            if child is not None:
                result.append(child)
                self._collect_active_descendants(child_id, result)

    def get_root(self, execution_id: str) -> Optional[ExecutionNode]:
        """追溯到根 execution。"""
        with self._lock:
            current = self._nodes.get(execution_id)
            if current is None:
                return None
            while current.parent_execution_id is not None:
                parent = self._nodes.get(current.parent_execution_id)
                if parent is None:
                    break
                current = parent
            return current

    def get_depth(self, execution_id: str) -> int:
        """返回到 root 的深度（root=0，清理后 ancestor 不可达时截断）。"""
        with self._lock:
            depth = 0
            current = self._nodes.get(execution_id)
            if current is None:
                return -1
            while current.parent_execution_id is not None:
                parent = self._nodes.get(current.parent_execution_id)
                if parent is None:
                    break  # v0.3: parent 已清理，截断
                current = parent
                depth += 1
            return depth
```

### 4.3 v0.3 关键不变量

- `children_ids` 保留 historical references（cleanup 不删除）
- active query 通过 `_nodes` filter 实现
- `_is_cleanup_safe` 三条件守卫
- `cleanup_eligible_at = terminated_at + retention`

---

## 5. Design: CancellationPropagationContext (v0.3)

### 5.1 完整 Schema

```python
# v6/runtime/cancellation_propagation.py — 新增

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Tuple, Optional


class CancellationPropagationLimitExceeded(Exception):
    """v0.3 新增：取消传播链深度超限。"""
    
    def __init__(self, depth: int, max_depth: int) -> None:
        self.depth = depth
        self.max_depth = max_depth
        super().__init__(
            f"Cancellation propagation chain depth {depth} exceeds limit {max_depth}"
        )


class PropagationType(str, Enum):
    """v0.3: 移除 PARENT_TIMEOUT，统一为 DEADLINE_EXCEEDED。"""
    USER_REQUEST = "user_request"
    PARENT_CANCELLED = "parent_cancelled"
    DEADLINE_EXCEEDED = "deadline_exceeded"


MAX_PROPAGATION_DEPTH = 32


@dataclass(frozen=True)
class CancellationPropagationContext:
    """取消传播上下文（v0.3: 内部 enforce invariants）。"""
    propagation_type: PropagationType
    origin_execution_id: str
    chain: Tuple[str, ...]
    reason: str
    initiated_at: datetime

    def __post_init__(self) -> None:
        """v0.3: enforce origin/chain invariant。"""
        if self.chain and self.chain[0] != self.origin_execution_id:
            raise ValueError(
                f"chain[0] ({self.chain[0]}) must equal "
                f"origin_execution_id ({self.origin_execution_id})"
            )

    @staticmethod
    def user_request(origin_execution_id: str, reason: str = ""):
        """顶层用户取消。"""
        return CancellationPropagationContext(
            propagation_type=PropagationType.USER_REQUEST,
            origin_execution_id=origin_execution_id,
            chain=(origin_execution_id,),  # v0.3: chain[0] = origin
            reason=reason or "user_request",
            initiated_at=datetime.now(timezone.utc),
        )

    def extend(
        self,
        current_execution_id: str,
        new_type: Optional[PropagationType] = None,
    ) -> "CancellationPropagationContext":
        """v0.3: 内部 enforce depth limit。"""
        new_depth = len(self.chain) + 1
        if new_depth > MAX_PROPAGATION_DEPTH:
            raise CancellationPropagationLimitExceeded(
                depth=new_depth,
                max_depth=MAX_PROPAGATION_DEPTH,
            )
        
        return CancellationPropagationContext(
            propagation_type=new_type or self.propagation_type,
            origin_execution_id=self.origin_execution_id,
            chain=self.chain + (current_execution_id,),
            reason=self.reason,
            initiated_at=self.initiated_at,
        )

    def to_payload(self) -> dict:
        return {
            "propagation_type": self.propagation_type.value,
            "origin_execution_id": self.origin_execution_id,
            "chain": list(self.chain),
            "reason": self.reason,
            "initiated_at": self.initiated_at.isoformat(),
        }

    def to_reason_string(self) -> str:
        if self.propagation_type == PropagationType.USER_REQUEST:
            return self.reason or "user_request"
        return f"{self.propagation_type.value}:{self.origin_execution_id}"

    def max_chain_depth(self) -> int:
        return len(self.chain)
```

### 5.2 不变量

- `chain[0] == origin_execution_id`（在 `__post_init__` 验证）
- `len(chain) ≤ MAX_PROPAGATION_DEPTH`（在 `extend()` enforce）
- 不可变：frozen dataclass
- `chain` 是 tuple

---

## 6. Design: Deadline 模型

### 6.1 ExecutionMetadata schema

```python
@dataclass
class ExecutionMetadata:
    # 唯一 graph 字段
    parent_execution_id: Optional[str] = None
    
    # v0.2 deadline 模型
    deadline_at: Optional[datetime] = None
    
    # v0.3 ExecutionControl 归属
    control: ExecutionControl = field(default_factory=ExecutionControl)
    
    # 其余字段同 v0.2（execution_id, task_id, timestamps, retry, priority, tags）
```

### 6.2 Effective Deadline = min(parent, child)

```python
def _compute_effective_deadline(parent_ctx, child_ctx):
    parent_dl = parent_ctx.execution.deadline_at if (parent_ctx and parent_ctx.execution) else None
    child_dl = child_ctx.execution.deadline_at if child_ctx.execution else None
    if parent_dl is None and child_dl is None:
        return None
    if parent_dl is None:
        return child_dl
    if child_dl is None:
        return parent_dl
    return min(parent_dl, child_dl)
```

### 6.3 Deadline 到期触发 cancel

```python
def _start_deadline_timer(self, task_id, ctx):
    if ctx.execution is None or ctx.execution.deadline_at is None:
        return
    deadline = ctx.execution.deadline_at
    now = datetime.now(timezone.utc)
    
    if deadline <= now:
        # 已过期，立即 cancel（DEADLINE_EXCEEDED 上下文）
        self._cancel_with_deadline(task_id)
        return
    
    def _deadline_worker():
        remaining = (deadline - datetime.now(timezone.utc)).total_seconds()
        if remaining > 0:
            cancelled = ctx.control.cancellation.wait(timeout=remaining)
            if cancelled:
                return  # 已被 cancel
        self._cancel_with_deadline(task_id)
    
    threading.Thread(
        target=_deadline_worker,
        daemon=True,
        name=f"orch-deadline-{task_id[:8]}",
    ).start()


def _cancel_with_deadline(self, task_id):
    """v0.3: 使用 DEADLINE_EXCEEDED 类型。"""
    ctx = self._contexts.get(task_id)
    if ctx is None or ctx.execution is None:
        return
    propagation = CancellationPropagationContext(
        propagation_type=PropagationType.DEADLINE_EXCEEDED,
        origin_execution_id=ctx.execution.execution_id,
        chain=(ctx.execution.execution_id,),
        reason=f"deadline exceeded at {ctx.execution.deadline_at.isoformat()}",
        initiated_at=datetime.now(timezone.utc),
    )
    self.cancel(task_id, propagation)
```

### 6.4 Future DeadlineScheduler (ADR-015 #15)

**当前 MVP**：`per-execution threading.Thread timer`

**未来演化**：
```
DeadlineScheduler
  heap: (deadline_at, execution_id)
       |
       v
  Cancellation Engine (单线程 timer wheel)
```

迁移约束：
- API 不变（`deadline_at` 字段）
- 仅内部实现替换

---

## 7. Design: Orchestrator.submit_child()

### 7.1 API

```python
def submit_child(
    self,
    parent_execution_id: str,
    task: Task,
    timeout: Optional[float] = None,
) -> str:
    """创建子 Execution。

    Args:
        parent_execution_id: 父 Execution 的 execution_id
        task: 子 Task
        timeout: 可选 duration 秒数；转 deadline_at = now + timeout

    Returns:
        子 Task 的 task_id

    Raises:
        ValueError: parent 不存在或形成环路
    """
```

### 7.2 实现（v0.3）

```python
def submit_child(self, parent_execution_id, task, timeout=None):
    with self._lock:
        parent_node = self._execution_registry.get(parent_execution_id)
        if parent_node is None:
            raise ValueError(f"Parent execution not found: {parent_execution_id}")

    task_id = self.submit(task)

    with self._lock:
        ctx = self._contexts[task_id]
        if ctx.execution is None:
            ctx.execution = ExecutionMetadata(task_id=task_id)
        ctx.execution.parent_execution_id = parent_execution_id

        if timeout is not None:
            ctx.execution.deadline_at = datetime.now(timezone.utc) + timedelta(seconds=timeout)
        
        parent_ctx = self._contexts.get(parent_node.task_id)
        effective_dl = _compute_effective_deadline(parent_ctx, ctx)
        if effective_dl is not None:
            ctx.execution.deadline_at = effective_dl

        self._execution_registry.register(
            execution_id=ctx.execution.execution_id,
            task_id=task_id,
            parent_execution_id=parent_execution_id,
        )

    return task_id
```

---

## 8. Design: Cancellation Propagation (v0.3)

### 8.1 完整 cancel() 实现

```python
def cancel(
    self,
    task_id: str,
    propagation: CancellationPropagationContext,
) -> bool:
    """v0.3: 使用 CancellationPropagationContext 的取消。"""
    with self._lock:
        ctx = self._contexts.get(task_id)
        if ctx is None:
            return False

        # ADR-014: 终态守卫
        if ctx.lifecycle in (
            LifecycleState.COMPLETED,
            LifecycleState.FAILED,
            LifecycleState.CANCELLED,
        ):
            return False

        # 触发取消令牌 + 状态迁移
        reason_str = propagation.to_reason_string()
        ctx.control.cancel(reason_str)
        current = self._task_states.get(task_id)
        if current is None:
            return False
        try:
            self._state_machine.transition(current, RuntimeState.CANCELLED)
            self._task_states[task_id] = RuntimeState.CANCELLED
            ctx.set_lifecycle(LifecycleState.CANCELLED, ActivityState.IDLE)
            if ctx.execution is not None:
                ctx.execution.finished_at = datetime.now(timezone.utc)
        except RuntimeStateTransitionError:
            pass

        # 收集后代（v0.3: active filter 内置）
        child_task_ids: List[str] = []
        if ctx.execution is not None:
            descendants = self._execution_registry.get_descendants(
                ctx.execution.execution_id
            )
            child_task_ids = [n.task_id for n in descendants]

        # Registry 生命周期
        if ctx.execution is not None:
            self._execution_registry.mark_terminated(ctx.execution.execution_id)
            self._execution_registry.schedule_cleanup(ctx.execution.execution_id)

    # 发布 TASK_CANCELLED 事件
    self._publish(
        RuntimeEventType.TASK_CANCELLED,
        propagation.to_payload(),
        task_id=task_id,
        source="orchestrator",
    )
    if self._event_bus is not None:
        self._event_bus.remove_trace_hook(task_id)

    # 递归 cancel 子任务（chain 延长；v0.3 extend 内部 enforce depth）
    for child_task_id in child_task_ids:
        child_ctx = self._contexts.get(child_task_id)
        if child_ctx is None or child_ctx.execution is None:
            continue
        try:
            child_propagation = propagation.extend(child_ctx.execution.execution_id)
            self.cancel(child_task_id, child_propagation)
        except CancellationPropagationLimitExceeded:
            # 深度超限，记录错误但不静默吞掉
            self._publish(
                RuntimeEventType.TASK_FAILED,
                {"reason": "cancellation_propagation_limit_exceeded"},
                task_id=child_task_id,
                source="orchestrator",
            )

    return True
```

### 8.2 用户入口（兼容 reason 字符串）

```python
def cancel(self, task_id, reason=""):
    """兼容旧 API：reason 字符串 → user_request propagation。"""
    ctx = self._contexts.get(task_id)
    execution_id = ctx.execution.execution_id if ctx and ctx.execution else task_id
    propagation = CancellationPropagationContext.user_request(execution_id, reason)
    return self._cancel_with_propagation(task_id, propagation)
```

### 8.3 TASK_CANCELLED Payload（v0.3）

```json
{
  "propagation_type": "deadline_exceeded",
  "origin_execution_id": "exec-001",
  "chain": ["exec-001", "exec-002"],
  "reason": "deadline exceeded at 2026-07-25T10:30:00+00:00",
  "initiated_at": "2026-07-25T10:30:00+00:00"
}
```

---

## 9. Design: Trace Model（保持不变）

- `TracePresentationModel.parent_id` 已存在
- EventAdapter 内部 index 扩展（不进入 contract）

---

## 10. Design: ExecutionControl 归属（v0.3）

- `ExecutionMetadata.control` 一级字段
- `ctx.control` 作为 property alias
- 不变量：`ctx.control is ctx.execution.control`

---

## 11. Files Plan

### 新增文件

| 文件 | 内容 |
|------|------|
| `v6/runtime/execution_registry.py` | ExecutionRegistry + ExecutionNode（v0.3 active topology + cleanup safe） |
| `v6/runtime/cancellation_propagation.py` | CancellationPropagationContext + PropagationType + CancellationPropagationLimitExceeded |
| `docs/v6/phase3-11-d-parent-child-execution-design.md` | 本文档 v0.3 |
| `.project/decisions/ADR-015-parent-child-execution-propagation.md` | ADR-015 v0.3（15 decisions） |
| `docs/v6/phase3-11-e-freeze-checklist.md` | Freeze Validation Checklist（v0.3 新增） |
| `tests/v6/runtime/test_phase3_11_d_parent_child.py` | Parent-Child 测试 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `v6/runtime/execution_metadata.py` | `deadline_at`；新增 `control: ExecutionControl` |
| `v6/runtime/orchestrator.py` | `submit_child()` / `cancel()` v0.3 / `_start_deadline_timer()` / `_execution_registry` |
| `v6/runtime/context.py` | `control` property 委托 |

### 禁止修改（v0.3 不变）

| 文件/契约 | 原因 |
|------|------|
| `RuntimeEvent` schema | 冻结 |
| `Task` | 冻结 |
| `RuntimeState` ABI | 冻结 |
| `RuntimeContext` ABI | 冻结 |
| `TracePresentationModel` schema | 冻结 |
| Capability / Decision / UI / Provider | 冻结 |

---

## 12. Frozen Boundary Summary

### 已冻结（来自 3.11-A.1 / 3.11-C / 3.11-D v0.1/v0.2）

| 项目 | 决策 |
|------|------|
| Task ≠ Execution Identity | `execution_id` 独立 |
| `parent_execution_id` | ExecutionMetadata 唯一 graph 字段 |
| RuntimeEvent 不增加 execution 字段 | schema 零修改 |
| Cooperative Cancellation | `threading.Event` |
| ExecutionMetadata 作为 RuntimeContext 一级字段 | `ctx.execution` |
| Lifecycle / Activity 分离 | 双状态模型 |
| ExecutionControl 抽象 | 聚合 CancellationToken |
| Cancellation Precedence Rule | ADR-014 |
| Terminal State Mutually Exclusive | `COMPLETED ∩ CANCELLED ∩ FAILED = ∅` |
| `TASK_CANCELLED` 事件类型 | ADR-013 |

### Phase 3.11-D v0.3 新冻结

| 项目 | 决策 |
|------|------|
| ExecutionMetadata 零 graph 字段 | 除 `parent_execution_id` 外禁止 |
| ExecutionRegistry 唯一 topology owner | ADR-015 #14 |
| children_ids active references | 不再 cleanup 时强删 |
| CancellationPropagationContext frozen + invariants | extend() 内部 enforce depth；__post_init__ 验证 origin/chain |
| PropagationType.DEADLINE_EXCEEDED | 统一 deadline 触发类型；移除 PARENT_TIMEOUT |
| Cleanup safe predicate | terminal + descendants_terminal + retention_expired |
| Registry 不是历史数据库 | 历史拓扑由 Trace / EventStore 承担 |
| Future DeadlineScheduler | ADR-015 #15 记录演化方向 |
| Cancel chain depth ≤ 32 | CancellationPropagationLimitExceeded |

### 待 Phase 3.11-E 验证

| 项目 | 状态 |
|------|------|
| `ctx.control is ctx.execution.control` | 不变量 |
| Cancel 传播完整性 | DFS 覆盖所有 active descendants |
| Cleanup safe predicate 有效性 | 三条件守卫 |
| Deadline 到期准确性 | UTC 统一 |
| History topology 可追溯 | children_ids 保留 |

---

## 13. Design Review Gate

| 检查项 | 状态 |
|--------|------|
| children_ids active references | ✅ |
| extend() 内部 enforce depth | ✅ |
| origin/chain invariant | ✅ |
| PARENT_TIMEOUT → DEADLINE_EXCEEDED | ✅ |
| Future DeadlineScheduler ADR | ✅ |
| Cleanup safe predicate 三条件 | ✅ |
| ADR-015 新增 #14/#15 | ✅ |
| ADR-014 终态守卫保留 | ✅ |
| ADR-013 TASK_CANCELLED payload 兼容 | ✅ |
| 不修改 RuntimeEvent schema | ✅ |
| 不修改 RuntimeState ABI | ✅ |
| 不修改 RuntimeContext ABI | ✅ |
| 不修改 Trace schema | ✅ |
| 不修改 Capability / Decision / UI / Provider | ✅ |

---

## 14. Phase 3.11 拆解（更新）

| Phase | 内容 | 状态 |
|-------|------|------|
| **3.11-A.1** | Design Amendment v0.2 | ✅ Frozen |
| **3.11-B** | Lifecycle + Activity 双状态 | ✅ Complete |
| **3.11-C** | ExecutionControl + Cancellation + Timeout | ✅ Complete |
| **3.11-D** | Parent-Child Execution（v0.3 Polish） | 🟡 Pending Final Review |
| **3.11-E** | Freeze Validation | ⏳ Pending |

---

## 15. Freeze Validation Checklist 入口

完整 checklist 见 [`phase3-11-e-freeze-checklist.md`](phase3-11-e-freeze-checklist.md)。

摘要：
- 跨文档一致性
- Do Not Touch 项零修改
- Implementation Constraints 全部落地
- Test Guards 覆盖