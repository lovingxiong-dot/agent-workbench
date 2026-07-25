# Phase 3.11-E — Freeze Validation Checklist

> **Status**: DRAFT
> **Date**: 2026-07-25
> **Phase**: 3.11-E
> **Purpose**: Phase 3.11 Frozen Gate 前的最终一致性验证清单

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial checklist (基于 3.11-D v0.3) |

---

## 1. Purpose

在 Phase 3.11-D v0.3 设计冻结前，对所有交付物进行最终一致性验证。本 checklist 是 Freeze Gate 的入口检查，所有项目必须通过才能进入 Phase 3.11 Frozen 状态。

---

## 2. Cross-Document Consistency

### 2.1 Design Document ↔ ADR-015

| 关键决策 | Design Doc 章节 | ADR-015 章节 | 一致 |
|---------|----------------|-------------|------|
| Cancellation Propagation Top-down | §8.1 | §3.1 | ✅ |
| Terminal State 守卫（ADR-014） | §8.4 | §3.2 | ✅ |
| CancellationPropagationContext frozen | §5.1 | §3.3 | ✅ |
| PropagationType 枚举（v0.3） | §5.2 | §3.4 | ✅ |
| chain depth ≤ 32（extend enforce） | §5.2 | §3.5 | ✅ |
| chain[0] == origin invariant | §5.2 | §3.5 | ✅ |
| Deadline 模型 effective = min | §6.2 | §3.6 | ✅ |
| Deadline 触发 DEADLINE_EXCEEDED | §6.3 | §3.7 | ✅ |
| ExecutionControl 归属 | §10 | §3.8 | ✅ |
| ExecutionRegistry 内部状态 | §4.1 | §3.9 | ✅ |
| children_ids active references | §4.2 | §3.10 | ✅ |
| Cleanup safe predicate 三条件 | §4.2 | §3.11 | ✅ |
| ExecutionMetadata 零 graph 字段 | §3.1 | §3.12 | ✅ |
| 环路防御 | §4.2 | §3.13 | ✅ |
| Execution Graph Ownership | §3.2 | §3.14 | ✅ |
| Deadline Scheduler Evolution | §6.4 | §3.15 | ✅ |
| Trace Model 不变 | §9 | §3.16 | ✅ |

### 2.2 Design Doc ↔ 3.11-A v0.2 / 3.11-C

| 引用项 | 一致 |
|--------|------|
| `parent_execution_id` 唯一 graph 字段 | ✅ |
| `ctx.execution` 一级字段 | ✅ |
| 双状态模型 LifecycleState / ActivityState | ✅ |
| ExecutionControl 抽象 | ✅ |
| ADR-014 Cancellation Precedence | ✅ |
| ADR-013 TASK_CANCELLED | ✅ |

---

## 3. Do Not Touch Verification

### 3.1 禁止修改项确认

| 契约 | 状态 | 检查方法 |
|------|------|---------|
| `RuntimeEvent` schema | ✅ 不修改 | grep RuntimeEvent schema |
| `Task` | ✅ 不修改 | Task dataclass 未变 |
| `RuntimeState` ABI | ✅ 不修改 | 枚举未增减 |
| `RuntimeContext` ABI（一级字段） | ✅ 不修改 | `control` 由 property 实现，不破坏 ABI |
| `TracePresentationModel` schema | ✅ 不修改 | parent_id 字段已存在 |
| Capability Contract | ✅ 不修改 | frozen |
| Decision Layer | ✅ 不修改 | frozen |
| UI Layer | ✅ 不修改 | frozen |
| Provider Layer | ✅ 不修改 | frozen |

### 3.2 新增文件清单

| 文件 | 内容 | 是否 Contract 边界外 |
|------|------|-------------------|
| `v6/runtime/execution_registry.py` | ExecutionRegistry + ExecutionNode | ✅ 是（Orchestrator 内部） |
| `v6/runtime/cancellation_propagation.py` | CancellationPropagationContext | ✅ 是（值对象） |
| `docs/v6/phase3-11-d-parent-child-execution-design.md` | 设计文档 | ✅ 是 |
| `.project/decisions/ADR-015-...` | ADR | ✅ 是 |
| `docs/v6/phase3-11-e-freeze-checklist.md` | Freeze Checklist | ✅ 是 |
| `tests/v6/runtime/test_phase3_11_d_parent_child.py` | 测试 | ✅ 是 |

### 3.3 修改文件清单

| 文件 | 变更类型 | 是否破坏契约 |
|------|---------|------------|
| `v6/runtime/execution_metadata.py` | 新增 `deadline_at` + `control` | ✅ additive only |
| `v6/runtime/orchestrator.py` | 新增方法 + 内部状态 | ✅ additive only |
| `v6/runtime/context.py` | `control` 改为 property | ✅ ABI 不变（语义委托） |

---

## 4. Implementation Constraints 落地检查

| 约束 | 落地位置 | 验证 |
|------|---------|------|
| `Orchestrator.cancel()` 递归 cancel active descendants | `orchestrator.py::cancel` | DFS 后序实现 |
| Child cancel 遵守 ADR-014 终态守卫 | `orchestrator.py::cancel` | lifecycle 检查 |
| 使用 `CancellationPropagationContext` | `orchestrator.py::cancel` | 参数类型 |
| `extend()` 内部 enforce depth | `cancellation_propagation.py::extend` | `CancellationPropagationLimitExceeded` |
| `__post_init__` 验证 chain[0] | `cancellation_propagation.py` | `ValueError` |
| `submit_child()` 校验 parent | `orchestrator.py::submit_child` | ValueError |
| `register()` 检测环路 | `execution_registry.py::register` | ValueError |
| `_compute_effective_deadline()` 取 min | `orchestrator.py` | 实现 |
| `_start_deadline_timer()` 使用 deadline_at | `orchestrator.py` | 实现 |
| Deadline 到期用 `DEADLINE_EXCEEDED` | `orchestrator.py::_cancel_with_deadline` | 实现 |
| `_is_cleanup_safe()` 三条件 | `execution_registry.py` | 实现 |
| `_remove_node()` 不修改 parent.children_ids | `execution_registry.py` | 实现 |
| `ctx.control is ctx.execution.control` | `context.py` | property 委托 |
| `Registry.schedule_cleanup` 仅终态 | `execution_registry.py` | 守卫 |
| `Orchestrator.shutdown()` 调 cleanup_all | `orchestrator.py` | 实现 |
| `PARENT_TIMEOUT` 不再使用 | 全文 | grep 验证 |

---

## 5. Test Guards 覆盖检查

### 5.1 必须存在的测试

| 类别 | 测试数 | 必含项 |
|------|-------|--------|
| Basic | 4 | submit_child / no_graph_fields / parent_id / control invariant |
| Cancellation | 7 | propagate / skip_completed / depth_limit / frozen / extend / origin_invariant / extend_enforce |
| Deadline | 4 | propagation_min / expiration / deadline_exceeded / parent_timeout_removed |
| Registry Lifecycle | 7 | no_cycle / lifecycle_cleanup / cleanup_all / safe_predicate / cleanup_blocks / preserved_after / active_filter |
| Registry Not History DB | 2 | historical_queryable / trace_replay |

### 5.2 Test Guard 数量统计

| 类别 | v0.2 | v0.3 |
|------|------|------|
| Basic | 4 | 4 |
| Cancellation | 6 | **7** (+origin_invariant, +extend_enforce) |
| Deadline | 4 | 4 |
| Registry Lifecycle | 4 | **7** (+safe_predicate, +cleanup_blocks, +preserved_after, +active_filter) |
| Registry Not History DB | 0 | **2** (新增) |
| **Total** | 18 | **24** |

---

## 6. ADR Coverage

### 6.1 ADR 索引

| ADR | 标题 | 状态 | 覆盖 Phase |
|-----|------|------|-----------|
| ADR-013 | Runtime Lifecycle Event Extension | ACCEPTED | 3.11-C |
| ADR-014 | Cancellation Precedence Rule | ACCEPTED | 3.11-C |
| ADR-015 | Parent-Child Execution Propagation | ACCEPTED v0.3 | 3.11-D |

### 6.2 ADR-015 Decision 完整性

| # | Decision | 状态 |
|---|---------|------|
| 1 | Cancellation Propagation Top-down | ✅ |
| 2 | Terminal State 守卫 | ✅ |
| 3 | CancellationPropagationContext frozen | ✅ |
| 4 | PropagationType 枚举 | ✅ |
| 5 | Context Invariants (depth + origin) | ✅ |
| 6 | Deadline 模型 effective = min | ✅ |
| 7 | Deadline 触发走 cancel 路径 | ✅ |
| 8 | ExecutionControl 归属 ExecutionMetadata | ✅ |
| 9 | ExecutionRegistry 内部状态 | ✅ |
| 10 | children_ids Active References | ✅ |
| 11 | Cleanup Safe Predicate | ✅ |
| 12 | ExecutionMetadata 零 graph 字段 | ✅ |
| 13 | 环路防御 | ✅ |
| 14 | Execution Graph Ownership | ✅ |
| 15 | Deadline Scheduler Evolution | ✅ |
| 16 | Trace Model 不变 | ✅ |

---

## 7. Frozen Boundary Summary

### 7.1 已冻结（不可变）

- RuntimeEvent schema
- Task 模型
- RuntimeState ABI
- RuntimeContext ABI（一级字段）
- TracePresentationModel schema
- Capability / Decision / UI / Provider Contract
- ADR-013 / ADR-014 内容

### 7.2 3.11-D v0.3 新冻结（Phase 3.11 Frozen 后不可变）

- ExecutionMetadata 零 graph 字段约束
- ExecutionRegistry 唯一 topology owner
- children_ids active references 语义
- CancellationPropagationContext invariants（depth + origin）
- PropagationType.DEADLINE_EXCEEDED 命名
- Cleanup safe predicate 三条件
- Registry 不是历史数据库
- Future DeadlineScheduler 演化方向（决策保留）
- Cancel chain depth ≤ 32
- PARENT_TIMEOUT 移除

---

## 8. Phase 3.11 Frozen Gate

### 8.1 进入条件

- [ ] 本 checklist 全部 ✅
- [ ] Implementation Constraints 100% 落地
- [ ] Test Guards 100% 覆盖
- [ ] Do Not Touch 项零修改
- [ ] ADR-015 v0.3 ACCEPTED

### 8.2 Frozen 后状态

```
Phase 3.11 Status:

3.11-A.1 Design Amendment     ✅ Frozen
3.11-B Lifecycle Activation   ✅ Complete
3.11-C Execution Control      ✅ Complete
3.11-D Parent-Child Execution  ✅ Complete (v0.3)
3.11-E Freeze Validation      ✅ Complete
─────────────────────────────────────────────
Phase 3.11                   🟢 FROZEN
```

### 8.3 Frozen 后允许

- Phase 3.12（下一阶段）进入 Design
- ADR-016+ 新增（需新 ADR 流程）

### 8.4 Frozen 后禁止

- 修改 3.11-A / 3.11-B / 3.11-C / 3.11-D 任何已冻结契约
- 修改 ADR-013 / ADR-014（除非新 ADR 替代）
- 修改 ADR-015 任何决策（除非新 ADR 替代）
- 修改 RuntimeEvent / RuntimeState / RuntimeContext / Task 任何字段

---

## 9. Sign-off

| 角色 | 验证项 | 状态 |
|------|--------|------|
| Architecture Reviewer | 6 项 polish 修改落地 | ⏳ Pending |
| Implementation Lead | Implementation Constraints 100% | ⏳ Pending |
| QA Lead | Test Guards 100% 覆盖 | ⏳ Pending |
| Documentation Lead | Cross-Doc Consistency | ⏳ Pending |
| ADR Maintainer | ADR-015 v0.3 ACCEPTED | ✅ |

---

## 10. References

- Phase 3.11-D Parent-Child Execution Model Design v0.3
- ADR-015 — Parent-Child Execution Propagation v0.3
- Phase 3.11-A Execution Identity Model Design v0.2
- ADR-013 — Runtime Lifecycle Event Extension
- ADR-014 — Cancellation Precedence Rule