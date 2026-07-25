# Phase 3.12-A — Derived Metrics Algorithm Spec

> **Status**: SPEC — v0.1
> **Date**: 2026-07-25
> **Phase**: 3.12-A.4
> **Depends on**: 3.12-A.3 Evidence Collection Architecture
> **Governance**: Derived Metrics Only（不是 Metrics Infrastructure）

---

## 1. Purpose

定义 5 类 Primitive Metrics 的算法 + Pure Function 契约 + Test Case 矩阵。

每条规则都是 **Pure Function**：
- 输入：Frozen Runtime 数据（事件列表 / Metadata / Registry snapshot）
- 输出：Metric 数值
- 无副作用 / 无 I/O / 无状态

---

## 2. Metric 1 — Execution Latency

### 2.1 计算公式

```
execution.duration_ms
  = terminal_event.timestamp - TASK_STARTED.timestamp
```

### 2.2 Pure Function 签名

```python
def execution_latency_ms(
    events: List[RuntimeEvent],
    task_id: str,
) -> Optional[float]:
    """计算 task 的执行延迟（毫秒）。

    Args:
        events: RuntimeEvent 流（按 timestamp 升序）
        task_id: 目标任务

    Returns:
        延迟（毫秒），若无完整 start/terminal events 返回 None
    """
```

### 2.3 算法步骤

1. 找到 `task_id` 的第一个 `TASK_STARTED` 事件 → `started_ts`
2. 找到 `task_id` 的第一个 terminal event（`TASK_COMPLETED` / `TASK_FAILED` / `TASK_CANCELLED`） → `terminal_ts`
3. 若两者都存在：`latency_ms = (terminal_ts - started_ts) * 1000`

### 2.4 Edge Cases

| Case | Behavior |
|------|----------|
| 无 TASK_STARTED | return None |
| 无 Terminal Event | return None |
| TASK_STARTED 在 Terminal 之后 | return None（异常数据） |
| 多个 Terminal Event | 取首个 |

---

## 3. Metric 2 — Cancellation Propagation Latency

### 3.1 计算公式

```
cancel.propagation_ms
  = TASK_CANCELLED.timestamp
    - payload.initiated_at_to_unix_timestamp()
```

### 3.2 Pure Function 签名

```python
def cancellation_propagation_ms(
    cancel_event: RuntimeEvent,
) -> Optional[float]:
    """计算 cancel 从发起（initiated_at）到 TASK_CANCELLED 发布的延迟。
    
    payload 结构（Phase 3.11-D v0.3 冻结）：
    {
      "propagation_type": "user_request" | "parent_cancelled" | "deadline_exceeded",
      "origin_execution_id": str,
      "chain": List[str],
      "reason": str,
      "initiated_at": ISO8601 字符串
    }
    
    Returns:
        传播延迟（毫秒），若 payload 无 initiated_at 返回 None
    """
```

### 3.3 Edge Cases

| Case | Behavior |
|------|----------|
| payload 缺 `initiated_at` | return None |
| `initiated_at` 解析失败 | return None |
| `initiated_at` 在未来（异常） | 可负值，正常返回 |

---

## 4. Metric 3 — Deadline Accuracy

### 4.1 计算公式

```
deadline.error_ms
  = actual_finish.timestamp - deadline_at.unix_timestamp()
```

正值表示超过 deadline（晚完成）；负值表示提前完成。

### 4.2 Pure Function 签名

```python
def deadline_error_ms(
    events: List[RuntimeEvent],
    metadata: ExecutionMetadata,
    task_id: str,
) -> Optional[float]:
    """计算 deadline 与实际完成时间的偏差。
    
    Returns:
        偏差（毫秒），若 metadata.deadline_at 未设置或 task 无 terminal event 则返回 None
    """
```

### 4.3 Edge Cases

| Case | Behavior |
|------|----------|
| `metadata.deadline_at` 为 None | return None |
| 无 Terminal Event | return None |
| `deadline_at` 在过去（已过期） | 返回正偏差（实际就更晚） |

---

## 5. Metric 4 — Event Throughput

### 5.1 计算公式

```
event.rate (events/sec)
  = event_count / window_seconds
```

### 5.2 Pure Function 签名

```python
def event_throughput(
    events: List[RuntimeEvent],
    window_start: Optional[float] = None,
    window_end: Optional[float] = None,
) -> Optional[float]:
    """事件 throughput（每秒钟事件数）。
    
    若 window_start/window_end 未提供，使用 events 实际首尾 timestamp。
    若 events 为空，返回 None。
    """
```

### 5.3 Edge Cases

| Case | Behavior |
|------|----------|
| events 为空 | return None |
| window_start == window_end | return None（避免除零） |
| window 跨负时间（异常） | return None |

---

## 6. Metric 5 — Registry Footprint

### 6.1 计算公式

```
registry.entries            = len(ExecutionRegistry._nodes)
registry.active_entries     = count(nodes where terminated_at is None)
registry.terminal_entries   = count(nodes where terminated_at is not None)
registry.max_depth          = max depth among all active nodes
registry.memory_estimate    = sum(len(ExecutionNode pickled) approx)
```

### 6.2 Pure Function 签名

```python
def registry_footprint(
    registry: ExecutionRegistry,
) -> FootprintSnapshot:
    """采集 ExecutionRegistry 当前 Footprint（不修改 Registry）。

    仅通过 public API 调用（has_node / get / get_descendants）。
    避免直接读 _nodes 内部（破坏 ABI）。
    """
```

### 6.3 Implementation Strategy

为避免读 `_nodes` 内部（会破坏 ABI 约束），**建议**：

```python
# 通过 public API 枚举
active_ids = [
    eid for eid in some_enumeration_source
    if registry.has_node(eid)
]
```

但 ExecutionRegistry 当前 **缺少外部可枚举的 ID 列表**。

**Gate 触发条件（Review Re-trigger）**：
若 3.12-A.4 实现需要 ExecutionRegistry 增加 `snapshot() -> list[str]` 公共方法，**必须重新触发 Architecture Review**，因为这是 Registry API 演进。

**当前实现策略**：
```python
# 暂时通过已知 execution_id 集合外部传入
def registry_footprint(
    registry: ExecutionRegistry,
    known_execution_ids: Iterable[str],
) -> FootprintSnapshot:
    """通过外部传入的 known_execution_ids + has_node() 采集。"""
```

---

## 7. FootprintSnapshot Dataclass

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class FootprintSnapshot:
    entries: int
    active_entries: int
    terminal_entries: int
    max_depth: int
    memory_estimate_bytes: int
    sampled_at: float  # time.time()
    sample_window_ids: int  # 已采样的 ID 数量（用于审计）
```

---

## 8. Pure Functions 通用约束

| 约束 | 说明 |
|------|------|
| 输入 | 仅 Frozen 数据 + 参数 |
| 输出 | 数值 / Snapshot |
| 副作用 | 无 |
| I/O | 无文件 / 无网络 / 无 print |
| Logging | 不调用 RuntimeEventType.publish |
| Error Handling | 不抛异常，返回 None 或默认值 |

---

## 9. Validation Tests（Pure Function 层）

```python
# test_latency.py
def test_latency_normal():
    """started 0s, terminal 1.5s → 1500ms."""

def test_latency_no_start_returns_none():
    """仅 terminal event → None."""

def test_latency_multi_terminal_takes_first():
    """started → completed → failed → first terminal wins."""

def test_latency_invalid_order_returns_none():
    """terminal before start → None."""
```

---

## 10. Stage 进度

| Plan | 内容 | 状态 |
|------|------|------|
| 3.12-A.1 | Design Document | ✅ APPROVED |
| 3.12-A.2 | Observation Contract | 🟡 Pending Review |
| 3.12-A.3 | Evidence Collection | 🟡 Pending Review |
| 3.12-A.4 | Derived Metrics Spec（本） | 🟡 Pending Review |
| 3.12-A.5 | Validation Report | ⏳ Pending |
| 3.12-A.6 | Tool Implementation | ⏳ Pending |