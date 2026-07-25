# Phase 3 — Repository Alignment Plan

> **Status**: PLAN v0.1
> **Date**: 2026-07-25
> **Phase**: Phase 3 Consolidation - Batch 1
> **Goal**: `v6.17.0-alpha Foundation Snapshot`

---

## 1. Problem Statement

### 1.1 Git Reality vs Narrative 失衡

| 维度 | 实际 | 声称 |
|------|------|------|
| **Git HEAD** | `v6.15.0-alpha` | - |
| **Phase 状态** | 3.15 Frozen | 3.16 设计中 |
| **中间缺失** | 3.9 / 3.10 / 3.11 / 3.12 / 3.13 / 3.14 / 3.16 资产 | - |
| **ADRs 缺失** | ADR-016/017/018/019/020 未反映到 Git Tag | - |

### 1.2 文档分散

- `docs/v6/phase3-12-*` 至 `phase3-16-*` 已存在
- `CHANGELOG.md` 状态未对齐
- `PROJECT_BLUEPRINT.md` 状态未同步
- ADR Index 未更新

### 1.3 必须解决

```
v6.15.0-alpha
  ↓
  v6.16.0-alpha（Phase 3.12-3.15 Frozen Assets）
  ↓
  v6.17.0-alpha（Phase 3 Consolidation Snapshot）
```

---

## 2. Alignment Plan

### 2.1 CHANGELOG.md 更新

**新增条目**：

```markdown
## v6.16.0-alpha (2026-07-25) — Phase 3 Cognitive Foundation Freeze

### Frozen
- Phase 3.11: Execution Kernel (ADR-013/014/015)
- Phase 3.12: Observation Layer (ADR-016)
- Phase 3.13: Presentation & Consumption (ADR-017)
- Phase 3.14: Insight Understanding (ADR-018)
- Phase 3.15: Decision Support (ADR-019)

### Re-Entry Triggers Cumulative
- ADR-016: 8 项
- ADR-017: 6 项
- ADR-018: 6 项
- ADR-019: 6 项
- Total: 26 项

### Test Coverage
- Phase 3.11: 98 tests
- Phase 3.12: 59 tests
- Phase 3.13: 37 tests
- Phase 3.14: 45 tests
- Phase 3.15: 37 tests
- Total: 276 tests

## v6.17.0-alpha (2026-07-25) — Phase 3 Consolidation

### Goal
- Repository Alignment（Git / CHANGELOG / Blueprint / Tag）
- Architecture Snapshot
- Runtime Boundary Audit
- Harness Design (Review only)

### Status
- Phase 3.16 Memory → Pending (after Consolidation)
- ADR-020 v0.4 → Pending (Harness inclusion)
```

### 2.2 PROJECT_BLUEPRINT.md 更新

**新增 Phase 3 Foundation Index**：

```markdown
## Phase 3 — Cognitive Runtime Foundation

### Frozen
- v6.16.0-alpha: Phase 3.11-3.15 Frozen (Execution + Observation + Presentation + Insight + Decision Support)

### In Design
- v6.17.0-alpha: Phase 3 Consolidation (Repository Alignment + Runtime Audit + Harness Design)
```

### 2.3 docs/v6/PHASE-3-FOUNDATION-INDEX.md（新增）

```markdown
# Phase 3 Foundation Index

## Status: v6.17.0-alpha Foundation Snapshot

## Architecture

### Frozen Layers
- v6/runtime: Phase 3.11 Execution Kernel (Frozen)
- v6/presentation: Phase 3.10 Renderer Contract (Frozen)
- tools/observation: Phase 3.12 (Frozen, ADR-016)
- tools/presentation: Phase 3.13 (Frozen, ADR-017)
- tools/insight: Phase 3.14 (Frozen, ADR-018)
- tools/decision_support: Phase 3.15 (Frozen, ADR-019)

### In Design
- tools/memory: Phase 3.16 (Pending, ADR-020)
- tools/harness: Phase 3.16+ (Pending, ADR-020 v0.4)
- tools/context: Phase 3.16+ (Pending, ADR-020)

## ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| ADR-013 | Runtime Lifecycle Event Extension | Frozen |
| ADR-014 | Cancellation Precedence Rule | Frozen |
| ADR-015 | Parent-Child Execution Propagation v0.3 | Frozen |
| ADR-016 | Observation Layer Contract | Frozen |
| ADR-017 | Observation Presentation Boundary | Frozen |
| ADR-018 | Agent Runtime Insight Boundary | Frozen |
| ADR-019 | Agent Decision Support Boundary | Frozen |
| ADR-020 | Cognitive Continuity & Harness Architecture Contract | Pending (v0.4) |

## Re-Entry Triggers Cumulative
- Total: 32 项
  - ADR-016: 8
  - ADR-017: 6
  - ADR-018: 6
  - ADR-019: 6
  - ADR-020: 6
```

### 2.4 Git Tag

```bash
# 1. 创建 v6.16.0-alpha tag（Phase 3.12-3.15 Frozen Assets）
git tag -a v6.16.0-alpha -m "Phase 3.12-3.15 Frozen Foundation"

# 2. 创建 v6.17.0-alpha tag（Consolidation Snapshot）
git tag -a v6.17.0-alpha -m "Phase 3 Consolidation: Repository Alignment + Architecture Snapshot"
```

---

## 3. Validation

### 3.1 必须

- [ ] CHANGELOG.md 含 v6.16.0-alpha 和 v6.17.0-alpha 条目
- [ ] PROJECT_BLUEPRINT.md 同步 Phase 3 状态
- [ ] PHASE-3-FOUNDATION-INDEX.md 完整
- [ ] Git tag v6.16.0-alpha 创建
- [ ] Git tag v6.17.0-alpha 创建
- [ ] 所有 ADR 在 Git history 中可追溯

### 3.2 禁止

- ❌ 写新代码
- ❌ 改 Runtime
- ❌ 改 Frozen Layer
- ❌ 跳过 Runtime Audit

---

## 4. 风险

| 风险 | 应对 |
|------|------|
| Git tag 与 narrative 继续偏差 | 强制 tag + Changelog 同步 |
| Blueprint 与 Phase 状态不一致 | 强制 Blueprint 更新 |
| ADR 散落 | 创建 PHASE-3-FOUNDATION-INDEX.md 索引 |

---

## 5. References

- [Phase 3 Consolidation Design](phase3-consolidation-design.md)
- [Phase 3.15 Completion Report](phase3-15-completion-report.md)
- [Phase 3.11-E Freeze Validation Report](phase3-11-e-freeze-validation-report.md)
- [CHANGELOG.md](../../CHANGELOG.md)
- [PROJECT_BLUEPRINT.md](../../PROJECT_BLUEPRINT.md)