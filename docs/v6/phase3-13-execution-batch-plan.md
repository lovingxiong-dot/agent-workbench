# Phase 3.13 — Execution Batch Plan

> **Status**: PLAN v0.1
> **Date**: 2026-07-25
> **Phase**: 3.13-B (Execution Batch)
> **Depends on**: Phase 3.13-A (Architecture Gate) Approved
> **Governance**: Architecture Gate（人工）/ Execution Batch（Agent 批量）

---

## 1. Purpose

定义 Phase 3.13 的 Execution Batch Plan：

- **Architecture Gate**（人工控制）：Review / Boundary / Contract / Long-term Direction / ADR
- **Execution Batch**（Agent 控制）：Implementation / Tests / Refactor / Documentation / Migration / Validation

本 Batch 进入条件：
- ✅ Phase 3.13-A.1 Scope Definition Approved
- ✅ Phase 3.13-A.2 ADR-017 Accepted
- ✅ Phase 3.13-A.3 UI Boundary Design Approved
- ✅ Phase 3.13-A.4 Execution Batch Plan Approved（本）

---

## 2. Architecture Gate vs Execution Batch

| 类别 | 模式 | 控制者 |
|------|------|--------|
| Architecture Review | Architecture Gate | 人类用户 |
| Boundary Decision | Architecture Gate | 人类用户 |
| ADR Creation | Architecture Gate | 人类用户 |
| Long-term Direction | Architecture Gate | 人类用户 |
| Implementation | Execution Batch | Agent |
| Tests | Execution Batch | Agent |
| Refactor | Execution Batch | Agent |
| Documentation | Execution Batch | Agent |
| Migration | Execution Batch | Agent |
| Validation | Execution Batch | Agent |

**原则**：大节点把关（Architecture Gate），小节点让 Agent 执行（Execution Batch）。

---

## 3. Batch 拆分

### 3.1 Batch 1: Presentation Adapter & ViewModel

**目标**：建立 ObservationReport → ObservationViewModel 转换。

**文件**：
- `tools/presentation/__init__.py`
- `tools/presentation/view_models/observation_view_model.py`
- `tools/presentation/view_models/runtime_status_view.py`
- `tools/presentation/view_models/performance_view.py`
- `tools/presentation/view_models/resource_view.py`
- `tools/presentation/view_models/lifecycle_view.py`
- `tools/presentation/adapters/observation_to_view_model.py`

**测试**：
- `tests/tools/presentation/test_view_model.py`
- `tests/tools/presentation/test_adapter.py`

**验收标准**：
- ViewModel frozen dataclass
- Adapter 单向数据流
- 单元测试 100% 覆盖
- Forbidden import 集合通过

### 3.2 Batch 2: Export Module

**目标**：JSON / Markdown / Snapshot Export。

**文件**：
- `tools/presentation/exports/__init__.py`
- `tools/presentation/exports/json_export.py`
- `tools/presentation/exports/markdown_export.py`
- `tools/presentation/exports/snapshot_export.py`

**测试**：
- `tests/tools/presentation/test_json_export.py`
- `tests/tools/presentation/test_markdown_export.py`
- `tests/tools/presentation/test_snapshot_export.py`

**验收标准**：
- 3 种格式稳定输出
- Schema = observation.v0.1
- File write 路径可配置
- 单元测试 + integration test

### 3.3 Batch 3: Runtime Observation Panel

**目标**：Read-only UI 集成。

**文件**：
- `v6/presentation/observation/__init__.py`
- `v6/presentation/observation/observation_panel.py`
- `v6/presentation/observation/observation_renderer.py`

**测试**：
- `tests/v6/presentation/test_observation_panel.py`
- `tests/v6/presentation/test_observation_renderer.py`

**验收标准**：
- 0 modification to v6/presentation/models.py
- Panel 不持有 Runtime 引用
- Panel 不 subscribe write event
- 单元测试 + 集成测试

### 3.4 Batch 4: Boundary Compliance & Integration

**目标**：完整 Boundary Compliance + Integration Tests。

**文件**：
- `tests/tools/presentation/test_boundary_compliance.py`

**验收标准**：
- 静态 import 检查通过
- v6/presentation 零修改验证
- Forbidden import 集合通过
- 全量回归 253+ 测试

### 3.5 Batch 5: Documentation & Completion Report

**目标**：Documentation 完整 + Completion Report。

**文件**：
- `docs/v6/phase3-13-completion-report.md`
- `tools/presentation/README.md`
- `v6/presentation/observation/README.md`

**验收标准**：
- 所有 README 完整
- Completion Report 含 Boundary 验证 + Test Results
- 状态更新：Phase 3.13 COMPLETE

---

## 4. Test Strategy

### 4.1 60% Primitive Tests

| 模块 | 测试数 | 状态 |
|------|--------|------|
| ViewModel（4 组） | 15+ | 计划 |
| Adapter | 5+ | 计划 |
| Export（3 格式） | 10+ | 计划 |

### 4.2 40% Integration Tests

| 模块 | 测试数 | 状态 |
|------|--------|------|
| Panel UI Component | 5+ | 计划 |
| End-to-End ObservationReport → ViewModel → Panel | 3+ | 计划 |
| Boundary Compliance | 4+ | 计划 |

### 4.3 Total Estimated

- Primitive: 30+
- Integration: 12+
- Boundary: 4+
- **Total Phase 3.13: 46+ tests**

---

## 5. File Structure

```
tools/presentation/                    # NEW
├── __init__.py
├── view_models/                       # 4 ViewModel
├── adapters/                          # 1 Adapter
├── exports/                           # 3 Export
└── README.md

v6/presentation/observation/           # NEW (UI 集成)
├── __init__.py
├── observation_panel.py
├── observation_renderer.py
└── README.md

tests/tools/presentation/              # NEW
├── test_view_model.py
├── test_adapter.py
├── test_json_export.py
├── test_markdown_export.py
├── test_snapshot_export.py
└── test_boundary_compliance.py

tests/v6/presentation/                 # NEW (UI tests)
├── test_observation_panel.py
└── test_observation_renderer.py

docs/v6/phase3-13-*                    # 4 docs
├── phase3-13-presentation-consumption-design.md
├── phase3-13-ui-boundary-design.md
├── phase3-13-execution-batch-plan.md (本文)
└── phase3-13-completion-report.md
```

---

## 6. Do Not Touch

| 类别 | 状态 |
|------|------|
| v6/runtime/* | 🚫 Frozen |
| v6/presentation/models.py | 🚫 Frozen |
| v6/presentation/contracts/ | 🚫 Frozen |
| v6/presentation/renderers/ | 🚫 Frozen |
| v6/presentation/design/ | 🚫 Frozen |
| agent_workbench/runtime/ | 🚫 Frozen v6.9.6 |
| tools/observation/* | 🚫 Frozen ADR-016 |
| CapabilityRegistry | 🚫 Frozen |

---

## 7. Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| ViewModel 反向依赖 Runtime | R0 | Static import check |
| Panel 启动 Runtime Worker | R0 | Boundary test |
| Export 改变 Schema | R0 | Version tag + 单元测试 |
| UI 越界进入 Runtime | R0 | v6/presentation/observation/ 边界 |
| 范围膨胀到 Performance Intelligence | R1 | ADR-017 + Review Re-Entry |

---

## 8. Re-Entry Triggers

若未来触发以下任一情况，**立即暂停并重新 Architecture Review**：

- 任何 v6/presentation/models.py 修改需求
- Panel 引入 Polling / Worker
- Adapter 修改 ObservationReport
- Export schema 修改
- 引入 Alert / Auto Optimization / Runtime Feedback
- 任何 Forbidden Import 集合触发

---

## 9. Success Criteria

- [ ] 46+ tests PASS
- [ ] 253+ 全量回归 PASS
- [ ] v6/presentation/models.py 零修改（git diff）
- [ ] v6/presentation/observation/ 仅新增（git status）
- [ ] Forbidden Import 集合通过
- [ ] Documentation 完整
- [ ] Completion Report 生成

---

## 10. References

- [Phase 3.13 Scope Definition](phase3-13-presentation-consumption-design.md)
- [Phase 3.13 UI Boundary Design](phase3-13-ui-boundary-design.md)
- [ADR-017 Observation Presentation Boundary](../../.project/decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../../.project/decisions/ADR-016-observation-layer-contract.md)