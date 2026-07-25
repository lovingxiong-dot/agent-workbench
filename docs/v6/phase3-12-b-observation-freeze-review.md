# Phase 3.12-B — Observation Foundation Freeze Review

> **Status**: REVIEW PENDING → ADR PENDING
> **Date**: 2026-07-25
> **Phase**: 3.12-B
> **Depends on**: Phase 3.12-A.6 Implementation (APPROVED)
> **Output**: ADR-Observation-001 (Observation Layer Contract)
> **Purpose**: 提升 Observation 事实架构为 Frozen Contract

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Freeze Review Document |

---

## 1. Purpose

Phase 3.12-A 实现已完成（59 tests + 253 regression + Architecture Review Approved），但事实架构尚未上升为 Contract。

本阶段目标：

- **确认** Phase 3.12-A 的代码架构反映的设计意图
- **冻结** Observation Layer 边界为 5 项核心规则
- **生成** ADR-Observation-001（Observation Layer Contract）
- **建立** Re-Entry Triggers（防止未来 Phase 3.13+ 越界）

---

## 2. Review Items

### 2.1 Observation 位置（✅ Confirmed）

```
tools/
└── observation/
    ├── adapters/    (4 files)
    ├── derived/     (6 files)
    ├── reports/     (3 files)
    └── collectors/  (2 files)
```

**Review**: Observation 位于 `tools/` 而非 `v6/`，避免成为 Runtime Kernel 的一部分。

**Decision**: ✅ Confirmed.

### 2.2 Boundary 5 项核心规则（待 ADR 化）

| # | 规则 | 来源 |
|---|------|------|
| 1 | Observation ≠ Monitoring | Architecture Review Section 8 |
| 2 | Observation ≠ Control | Architecture Review Section 8 |
| 3 | Observation ≠ Runtime Intelligence Loop | Architecture Review Section 8 |
| 4 | Windowed Metrics MUST filter events in window | Throughput Review Section 4 |
| 5 | `deadline_at` 在 `ExecutionMetadata` 而非 `ExecutionNode` | deadline Review Section 3 |

### 2.3 禁止 import 集合（待 ADR 化）

```python
REAL_FORBIDDEN = (
    "v6.runtime.orchestrator",
    "v6.runtime.engine_manager",
    "v6.runtime.planner_loop",
    "v6.runtime.capability_router",
    "agent_workbench.runtime.capability",
    "agent_workbench.runtime.decision",
    "agent_workbench.runtime.capability_registry",
    "agent_workbench.runtime.capability_router",
    "agent_workbench.runtime.decision_dispatcher",
)
```

**Review**: 与 Phase 3.11-E + v6.9.6 Frozen Contracts 严格保持一致。

**Decision**: ✅ Confirmed.

### 2.4 Pure Function Discipline（待 ADR 化）

| 规则 | 落地 |
|------|------|
| 输入：Frozen 数据 | `derived/*.py` 仅 import `v6.runtime.*` types |
| 输出：数值 / Snapshot | `float` / `FootprintSnapshot` |
| 无副作用 | 无文件 I/O / 无网络 / 无 publish |
| 无 I/O | 无 print / 无 logging 调用 Runtime |
| 异常处理 | 不抛异常，返回 None |

**Review**: 5 个 derived 函数全部满足。

**Decision**: ✅ Confirmed.

### 2.5 Schema Stability（待 ADR 化）

| 规则 | 落地 |
|------|------|
| `OBSERVATION_SCHEMA_VERSION = "observation.v0.1"` | `reports/observation_report.py` |
| backward compatible evolution | minor version add optional fields |
| major version requires new ADR | 字段重命名 / 语义变化必须 Re-Review |

**Review**: 当前 schema 稳定，无需 re-key。

**Decision**: ✅ Confirmed.

### 2.6 Re-Entry Triggers（待 ADR 化）

按 Architecture Review Section 9，列出 8 项 Re-Entry Triggers：
1. `v6/runtime/*.py` 修改需求
2. RuntimeEvent / RuntimeState / Task schema 演进
3. ExecutionRegistry 需要新增 API
4. EventBus 需要新增 metrics 字段
5. Trace 需要扩展字段
6. CapabilityRegistry 需要演进
7. Observation 启动 Runtime Worker
8. Observation 拥有 Runtime 生命周期引用

**Review**: 全部覆盖。

**Decision**: ✅ Confirmed.

---

## 3. ADR 化决策

### 3.1 ADR 提案：`ADR-Observation-001` Observation Layer Contract

**Title**: Observation Layer Contract & Boundary Freeze

**Status**: PROPOSAL → ACCEPTED（待 Phase 3.12-B 完成）

**Scope**: Phase 3.12-A Implementation（tools/observation/）

**5 项核心 Decision**：

1. **Observation Layer 位置** — `tools/observation/`，禁止进入 `v6/` 或 `agent_workbench/runtime/`
2. **禁止 import 集合** — 上述 9 个 module
3. **Pure Function discipline** — 5 项规则
4. **Schema Stability Rule** — `observation.v0.x` 版本规则
5. **Windowed Metric Rule** — 必须在 window 内 filter

**额外 Decision**：

6. **Adapter 边界** — 仅消费 Frozen Artifact，不持有 Runtime 引用
7. **Collect Policy** — 不启动 Worker，不修改 Runtime 状态
8. **Re-Entry Triggers** — 8 项触发器（见 §2.6）

### 3.2 ADR 与现有 ADR 关系

| 现有 ADR | 与 ADR-Observation-001 关系 |
|---------|--------------------------|
| ADR-013 Runtime Lifecycle Event Extension | Observation 消费其 TASK_CANCELLED 事件 |
| ADR-014 Cancellation Precedence Rule | Observation 仅观察结果，不参与 |
| ADR-015 Parent-Child Execution Propagation v0.3 | Observation 消费其 CancellationPropagationContext payload.initiated_at |
| **ADR-Observation-001（NEW）** | Observation Layer 边界冻结 |

### 3.3 ADR 不重复内容

ADR-Observation-001 **不重复** Phase 3.11-E 冻结内容，仅补充 Observation 特定规则。

---

## 4. Frozen Boundary 状态

### 4.1 已冻结（Phase 3.11-E + v6.9.6 + Phase 3.12-B）

| 类别 | 状态 | 来源 |
|------|------|------|
| RuntimeEvent schema | ✅ Frozen | Phase 3.11-E |
| RuntimeState ABI | ✅ Frozen | Phase 3.11-E |
| Task Contract | ✅ Frozen | Phase 3.11-E |
| RuntimeContext 一级字段 | ✅ Frozen | Phase 3.11-E |
| TracePresentationModel | ✅ Frozen | Phase 3.11-E |
| ExecutionMetadata schema | ✅ Frozen | Phase 3.11-D v0.3 |
| ExecutionRegistry public API | ✅ Frozen | Phase 3.11-D v0.3 |
| CancellationPropagationContext | ✅ Frozen | Phase 3.11-D v0.3 |
| CapabilityDefinition/Context/State/Registry | ✅ Frozen | v6.9.6 |
| **Observation Layer Contract** | 🟡 **Freeze Pending** | **Phase 3.12-B → ADR-001** |
| **Observation Schema v0.x** | 🟡 **Freeze Pending** | **Phase 3.12-B → ADR-001** |
| **Windowed Metric Rule** | 🟡 **Freeze Pending** | **Phase 3.12-B → ADR-001** |

### 4.2 Observation 演进后 Future 不可越界项

| 未来可能越界项 | 禁止 |
|--------------|------|
| Observation + Performance Dashboard | 🚫 |
| Observation + Alert Engine | 🚫 |
| Observation + Auto Optimizer | 🚫 |
| Observation + Runtime Intelligence Loop | 🚫 |
| Observation + Adaptive Runtime Tuning | 🚫 |

---

## 5. Test Strategy Future Considerations（Review Section 6）

按 Review 建议：
- 当前 `tests/tools/observation/` 单一目录结构 OK（59 tests）
- 未来 Observation 资产增加时可考虑：
  ```
  tests/
  ├── contract/         # Frozen Contract 验证
  ├── boundary/         # Boundary compliance
  ├── derived/          # Pure Functions
  └── integration/      # 集成测试
  ```
- 不立即重构（避免过度工程，遵循 OD-G0-001）

---

## 6. Phase 3.12-B Plan

| Stage | 内容 | 状态 |
|-------|------|------|
| 3.12-B.1 | Freeze Review Document（本文） | 🟡 Pending Review |
| 3.12-B.2 | ADR-Observation-001 创建 | ⏳ Next |
| 3.12-B.3 | ADR-Observation-001 接受 + 索引更新 | ⏳ Next |
| 3.12-B.4 | ADR Index 更新（governance） | ⏳ Next |
| 3.12-B.5 | Phase 3.12-B Completion Report | ⏳ Final |

---

## 7. Re-Entry Conditions

Phase 3.12-B 进入 Phase 3.13+ 必须满足：

- [x] Phase 3.12-A.6 Implementation Approved
- [x] Phase 3.12-A.7 Implementation Report Complete
- [ ] Phase 3.12-B.1 Freeze Review Document Approved
- [ ] Phase 3.12-B.2 ADR-Observation-001 Accepted
- [ ] Phase 3.12-B.3 ADR Index Updated
- [ ] Phase 3.12-B.4 Phase 3.12-B Completion Report

---

## 8. References

- [Phase 3.12-A Implementation Report](phase3-12-a-implementation-report.md) (APPROVED)
- [Phase 3.12-A Design](phase3-12-a-runtime-observation-design.md)
- [Phase 3.12-A Observation Contract](phase3-12-a-observation-contract.md)
- [Phase 3.12-A Derived Metrics Spec](phase3-12-a-derived-metrics-spec.md)
- [Phase 3.12-A Report Schema](phase3-12-a-observation-report-schema.md)
- [Phase 3.11-E Freeze Validation Report](phase3-11-e-freeze-validation-report.md)
- [ADR-013 Runtime Lifecycle Event Extension](../decisions/ADR-013-runtime-lifecycle-event-extension.md)
- [ADR-014 Cancellation Precedence Rule](../decisions/ADR-014-cancellation-precedence-rule.md)
- [ADR-015 Parent-Child Execution Propagation v0.3](../decisions/ADR-015-parent-child-execution-propagation.md)
- Tool: [tools/observation/README.md](../../tools/observation/README.md)
- Tests: [tests/tools/observation/](../../tests/tools/observation/)