# ADR-015 — Parent-Child Execution Propagation

> **Status**: ACCEPTED (v0.3)
> **Date**: 2026-07-25
> **Supersedes**: ADR-015 v0.2 (2026-07-25)
> **Scope**: Runtime — Parent-Child Execution 取消 / Deadline 传播规则

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial draft: 字符串拼接 reason、timeout_seconds 模型、单一 register/unregister |
| v0.2 | 2026-07-25 | CancellationPropagationContext（frozen dataclass）；timeout → deadline；Registry lifecycle |
| v0.3 | 2026-07-25 | Architecture Polish: children_ids active references；extend() 内部 enforce depth；origin/chain invariant；PARENT_TIMEOUT → DEADLINE_EXCEEDED；Cleanup safe predicate；Future DeadlineScheduler；新增 Decision #14/#15 |

---

## 1. Purpose

冻结 Phase 3.11-D Parent-Child Execution Model 的核心传播规则，v0.3 Architecture Polish 强化：

- **Registry 不是历史数据库**：active topology references 取代强一致
- **Context 是 invariant owner**：extend() 内部 enforce depth
- **Cleanup Safe Predicate**：三条件守卫
- **Future DeadlineScheduler**：记录未来演化方向

---

## 2. Context

Phase 3.11-D 引入 Parent-Child Execution 后，必须回答：

1. Parent 取消时，子 Execution 怎么办？
2. Parent deadline 到期时，子 Execution 怎么办？
3. Child 已 COMPLETED 时，Parent 取消是否影响 Child？
4. Child 取消时，Parent 是否被通知？
5. Deadline 是覆盖还是取 min？
6. ExecutionControl 归属何处？
7. Trace 如何展示父子关系？
8. Registry 何时清理？清理策略？
9. Cleanup 是否会破坏正在执行的 Execution？

---

## 3. Decision

### 3.1 Cancellation Propagation：Top-down DFS 后序

**规则**：Parent cancel → 所有 active descendants cancel。

传播方向：**单向 Top-down**。Child cancel 不传播给 Parent。

传播顺序：**DFS 后序**（先 leaf，最后 root）。

### 3.2 Terminal State 守卫（继承 ADR-014）

**规则**：若 descendant 已处于 COMPLETED / FAILED / CANCELLED，parent cancel 跳过该 descendant，不改变其状态。

依据：ADR-014 Terminal State Mutually Exclusive Rule。

### 3.3 CancellationPropagationContext：结构化传播上下文

**规则**：取消传播通过 `CancellationPropagationContext` 结构体传递，取代字符串拼接。

不可变性：`frozen=True`，`extend()` 返回新实例。

Payload 序列化：`to_payload()` 输出 TASK_CANCELLED 事件 payload。

### 3.4 PropagationType 枚举（v0.3 修订）

```python
class PropagationType(str, Enum):
    USER_REQUEST = "user_request"
    PARENT_CANCELLED = "parent_cancelled"
    DEADLINE_EXCEEDED = "deadline_exceeded"  # v0.3 新命名
```

**移除**：`PARENT_TIMEOUT`（v0.1 残留，timeout 语义已被 deadline 取代）。

理由：Runtime 内部只有 deadline 语义。保留 `PARENT_TIMEOUT` 会让未来代码误解为支持 timeout。

### 3.5 CancellationPropagationContext Invariants（v0.3 新增）

**Invariant 1**：`chain[0] == origin_execution_id`

在 `__post_init__` 验证；不满足抛 `ValueError`。

**Invariant 2**：`len(chain) ≤ MAX_PROPAGATION_DEPTH` (32)

在 `extend()` 内部 enforce；不满足抛 `CancellationPropagationLimitExceeded`。

**设计原则**：Context 是 invariant owner，不依赖调用方守卫。

### 3.6 Deadline 模型：effective = min(parent, child)

**规则**：子 Execution 的 effective deadline = min(parent.deadline_at, child.deadline_at)。

取代 v0.1 `timeout_seconds` 相对时长模型。

### 3.7 Deadline 触发走 cancel 路径

Parent deadline 到期 → `cancel(propagation_context with DEADLINE_EXCEEDED)` → 标准 cancel 传播。

### 3.8 ExecutionControl 归属：ExecutionMetadata

**最终归属**：`ctx.execution.control`。

迁移路径：
- Phase 3.11-C：`ctx.control` 一级字段
- Phase 3.11-D：`ExecutionMetadata.control` 一级字段；`ctx.control` 作为 property alias
- Phase 3.11-E：验证不变量 `ctx.control is ctx.execution.control`

### 3.9 ExecutionRegistry：Orchestrator 内部状态

**规则**：`ExecutionRegistry` 是 Orchestrator 私有数据结构。

禁止：
- 写入 RuntimeContext / RuntimeEvent / ExecutionMetadata（除 parent_execution_id）
- 暴露到 Presentation Layer
- **不是历史数据库**（历史拓扑由 Trace / EventStore 承担）

### 3.10 children_ids Active Topology References（v0.3 新约束）

**规则**：`parent.children_ids` 是 historical topology references（保留历史引用），不保证强一致。

```
v0.2: cleanup 时 parent.children_ids.remove(child_id)   # 强一致
v0.3: cleanup 时不修改 parent.children_ids              # active references
```

**读取语义**：active query 通过 `_nodes` filter 实现：
- `get_children(execution_id)` 返回仍在 `_nodes` 中的 child
- `get_descendants(execution_id)` 返回仍在 `_nodes` 中的 descendant
- 已清理的 child 不出现在查询结果中

**理由**：保留历史引用供 Trace / EventStore 重放；避免 cleanup 修改历史 topology 破坏重放。

### 3.11 Cleanup Safe Predicate（v0.3 新增）

**规则**：节点 cleanup safe ⟺ 三条件同时满足：

```
node.terminated_at ≠ None
∧ all_active_descendants.terminated
∧ now ≥ cleanup_eligible_at
```

**`cleanup_eligible_at = terminated_at + retention_seconds`**（默认 300s）。

**理由**：防止 parent 在 child 仍在执行时被清理（active topology 断开）。

### 3.12 ExecutionMetadata 零 graph 字段（v0.3 强化）

**规则**：`ExecutionMetadata` 仅允许持有以下 graph 相关字段：
- `parent_execution_id: Optional[str]`（**唯一** graph 字段，单一指向）

禁止：
- `children_ids: list[str]` — 写放大
- `execution_depth: int` — 可由 Registry 计算
- `root_execution_id: str` — 可由 Registry 追溯
- `sibling_count: int` — 可由 Registry 计算
- 任何 `_index` / `_tree` / `_graph` 字段

### 3.13 环路防御

`ExecutionRegistry.register()` 必须检测环路：`execution_id` 不能出现在 parent 的祖先链上。

### 3.14 Execution Graph Ownership（ADR-015 Decision #14，v0.3 新增）

```
Execution topology belongs exclusively to ExecutionRegistry.

ExecutionMetadata MUST NOT contain topology state.
```

**显式声明**：Registry 是 Execution Graph 唯一所有者；ExecutionMetadata 不持有任何 graph 字段（除 parent_execution_id 单向引用）。

### 3.15 Deadline Scheduler Evolution（ADR-015 Decision #15，v0.3 新增）

```
Current implementation may use per-execution timers.

Future Runtime SHOULD migrate to centralized DeadlineScheduler.
```

**未来演化**：
```
DeadlineScheduler
  heap: (deadline_at, execution_id)
       |
       v
  Cancellation Engine (单线程 timer wheel)
```

**迁移约束**：
- `ExecutionMetadata.deadline_at` API 不变
- 触发机制不变（仍发 cancel，type=DEADLINE_EXCEEDED）
- 仅内部实现替换

**避免**：未来优化变成 breaking change。

### 3.16 Trace Model 不变

`TracePresentationModel.parent_id` 字段已存在（Phase 3.10）。无需新增字段。

EventAdapter 内部 `_execution_index` / `_parent_index` 仅作内部查询，**不进入 contract**。

---

## 4. Consequences

### Positive

- 父子 Execution 关系语义清晰，可支撑 Workflow / Recursive Capability / Multi-Agent
- 取消与 deadline 传播规则显式，避免运行时未定义行为
- ExecutionMetadata 零 graph 字段约束防止 Execution 持有冗余数据
- CancellationPropagationContext 结构化传播链便于调试
- Context 是 invariant owner（depth/origin 双重保障）
- Registry active references 保留历史拓扑供 Trace 重放
- Cleanup safe predicate 防止 parent 在 child 执行时被清理
- Future DeadlineScheduler 记录演化方向

### Negative

- Orchestrator 内部状态增加（`_execution_registry` + `_cleanup_timers`）
- Cancel 传播是同步递归调用，深度过深时可能栈溢出（mitigation：chain depth ≤ 32 + 专用异常）
- Deadline 模型调用方需理解 duration → deadline_at 转换
- Cleanup timer 增加 daemon thread 数量（MVP 可接受）

### Risk

- Future PauseToken 引入时，本 ADR 需扩展为 "Pause propagation" 规则
- Future Retry 引入时，retry execution 的 parent 关系需明确定义
- Cleanup retention_seconds 配置需要根据场景调整
- Future DeadlineScheduler 迁移需确保 API 稳定性

---

## 5. Implementation Constraints

| 约束 | 说明 |
|------|------|
| `Orchestrator.cancel()` 必须递归 cancel active descendants | DFS 后序 |
| Child cancel 必须遵守 ADR-014 终态守卫 | 已 COMPLETED 跳过 |
| `Orchestrator.cancel()` 必须使用 CancellationPropagationContext | |
| `extend()` 必须内部 enforce depth | 不依赖调用方 |
| `extend()` 超限抛 `CancellationPropagationLimitExceeded` | |
| `__post_init__` 必须验证 chain[0] == origin_execution_id | |
| `submit_child()` 必须校验 parent 存在 | 防止悬挂引用 |
| `ExecutionRegistry.register()` 必须检测环路 | |
| `_compute_effective_deadline()` 必须取 min | |
| `_start_deadline_timer()` 必须使用 deadline_at | |
| Deadline 到期必须用 `DEADLINE_EXCEEDED` 上下文 | v0.3 统一命名 |
| `_is_cleanup_safe()` 必须三条件守卫 | terminal + descendants + retention |
| `_remove_node()` 不修改 parent.children_ids | v0.3 active references |
| `ctx.control is ctx.execution.control` 必须为 True | 不变量 |
| Registry.schedule_cleanup 仅在终态调用 | |
| `Orchestrator.shutdown()` 必须调用 `registry.cleanup_all()` | |
| `PARENT_TIMEOUT` 不再使用 | v0.3 移除 |

---

## 6. Test Guards

### 6.1 Basic

| 测试 | 验证 |
|------|------|
| `test_submit_child_sets_parent_execution_id` | parent 关系正确建立 |
| `test_execution_metadata_no_graph_fields` | 零 graph 字段约束 |
| `test_event_adapter_parent_id_from_execution` | Trace parent_id 正确填充 |
| `test_ctx_control_is_ctx_execution_control` | 不变量 |

### 6.2 Cancellation

| 测试 | 验证 |
|------|------|
| `test_cancel_propagates_to_children` | DFS 后序覆盖所有 active descendants |
| `test_cancel_skips_completed_children` | ADR-014 终态守卫 |
| `test_cancel_chain_depth_limit` | chain depth ≤ 32 |
| `test_cancellation_propagation_context_frozen` | 不可变性 |
| `test_propagation_extend_creates_new_instance` | extend 语义 |
| `test_origin_chain_invariant` | chain[0] == origin_execution_id |
| `test_extend_enforces_depth_internally` | extend() 内部 enforce |

### 6.3 Deadline

| 测试 | 验证 |
|------|------|
| `test_deadline_propagation_min` | effective deadline = min |
| `test_deadline_expiration_triggers_cancel` | deadline 到期触发 cancel |
| `test_deadline_exceeded_propagation_type` | DEADLINE_EXCEEDED 类型 |
| `test_parent_timeout_removed` | PARENT_TIMEOUT 不再使用 |

### 6.4 Registry Lifecycle

| 测试 | 验证 |
|------|------|
| `test_execution_registry_no_cycle` | 环路防御 |
| `test_registry_lifecycle_cleanup` | schedule_cleanup + 自动清理 |
| `test_registry_cleanup_all` | Orchestrator 销毁时全量清理 |
| `test_cleanup_safe_predicate` | 三条件守卫 |
| `test_cleanup_blocks_when_descendants_active` | descendants 未终态时阻止 cleanup |
| `test_children_ids_preserved_after_cleanup` | v0.3 active references |
| `test_get_active_children_filters_cleaned` | active filter 正确 |

### 6.5 Registry Not History Database

| 测试 | 验证 |
|------|------|
| `test_historical_topology_queryable` | cleanup 后 children_ids 仍可读 |
| `test_trace_replay_uses_children_ids` | Trace 重放使用历史引用 |

---

## 7. References

- Phase 3.11-D Parent-Child Execution Model Design v0.3
- Phase 3.11-A Execution Identity Model Design v0.2
- ADR-014 — Cancellation Precedence Rule (ACCEPTED)
- ADR-013 — Runtime Lifecycle Event Extension (ACCEPTED)
- `v6/runtime/orchestrator.py` — cancel() / submit_child() / _start_deadline_timer()
- `v6/runtime/execution_registry.py` — ExecutionRegistry (新增, v0.3 active topology + cleanup safe)
- `v6/runtime/cancellation_propagation.py` — CancellationPropagationContext + CancellationPropagationLimitExceeded (新增)
- `v6/runtime/execution_metadata.py` — deadline_at + control (v0.3)