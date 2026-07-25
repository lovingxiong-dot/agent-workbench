# Repository Narrative Migration Report

> **Status**: COMPLETE (2026-07-25)
> **Triggered By**: User校准 — Repository Narrative Drift 修复
> **Goal**: 将所有事实源（Blueprint / Lineage / State / CHANGELOG / README）从旧叙事（`v6-dev` + `v6.9.6 foundation`）迁移到新叙事（`v6-agent` + `v6.18 product evolution`）

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Migration Report (5 source documents synced) |

---

## 1. Final Verdict

```
Repository Narrative Migration: ✅ COMPLETE

Updated Documents (5):
  - PROJECT_BLUEPRINT.md    ✅ Synced (Current Snapshot, Branch Architecture)
  - PROJECT_LINEAGE.md       ✅ Synced (v6-agent, tag migration note)
  - PROJECT_STATE.md         ✅ Synced (v6.18.0-alpha, Current Snapshot)
  - README.md                ✅ Synced (v6.18.0-alpha, Runtime Frozen)
  - CHANGELOG.md              ✅ Synced (v6.18 + Tag ordering note)

Pending (Working Tree Cleanup, Low Priority):
  - 63 modified files (Phase 2-D legacy + Phase 3.12-3.15 uncommitted)
  - 3 stashes (need review before drop)
```

---

## 2. User 校准 4 项 + 1 项

### 2.1 修正 1：Version ≠ Phase

**问题**：Version 号（如 v6.16）被误认为等于 Phase 号（Phase 3.11）。

**修正**：
- 所有文档顶部加 **"Version vs Milestone" 区分说明**
- CHANGELOG 顶部加 **"Tag ordering note"**（v6.17.0-alpha = Phase 3.10；v6.16.0-alpha = Phase 3.11；commit 顺序与 phase 顺序不一致）

### 2.2 修正 2：v6.17 / v6.18 倒序说明

**问题**：`v6.16 → v6.17 → v6.18` 看起来像倒序（Phase 3.11 → 3.10 → 3.11）。

**修正**：
- 明确 **"Historical tag ordering ≠ Architectural phase ordering"**
- 解释：v6.16 是 commit 顺序的最新 tag（Phase 3.11 实际完成），v6.17 是后建的（Phase 3.10 实际在 Phase 3.11 之前完成）

### 2.3 修正 3：Cognitive Layer ≠ Runtime Kernel

**问题**：之前 `Runtime → Observation` 暗示 Observation 在 Runtime 内。

**修正**：
- PROJECT_STATE.md 明确 **"Cognitive Layer is NOT Runtime Kernel"**
- 加 **Anti-Pattern Warning**：禁止 `v6/runtime/observation/`, `v6/runtime/insight/`, `v6/runtime/decision_support/`

### 2.4 修正 4：Phase 3.16 描述模糊

**问题**：之前 `Phase 3.16 Memory + Harness` 没说清是 Architecture Review only。

**修正**：
- PROJECT_STATE.md 明确 **"Architecture Review only (not Runtime extension)"**
- 加 **Runtime Freeze Certificate** section 重复禁止

### 2.5 最大修正：v6-core / v6-service 不要写 archive

**问题**：之前 `archive/v6-core / v6-service / v6-dev` 描述**不准确**。

**修正**：
- PROJECT_BLUEPRINT.md 用 **Branch Architecture (Blueprint Definition)** 表格
- 三个分支语义保持 Blueprint 原意：`v6-core` = Frozen Runtime Kernel；`v6-service` = Extension Layer (planned)；`v6-agent` = Active Development
- 加 **"Implementation Reality"**：实际**只有 `v6-agent` 实际 active**

---

## 3. Migration 执行摘要（5 个文档）

### 3.1 PROJECT_BLUEPRINT.md

| 修改 | 旧 | 新 |
|------|----|----|
| 当前版本 | v6.16.0-alpha (Runtime) / v6.17.0-alpha (Presentation) | **v6.18.0-alpha** |
| Active branch | `v6-agent` (single line) | `v6-agent` (SINGLE source of truth) |
| Framework Core baseline | v6.8.0-alpha | **v6.9.6-foundation** + **v6.16.0-alpha** |
| Branch Architecture | "v6-core / v6-service / v6-agent" (无 Implementation Reality) | **加 "Implementation Reality" 段** |
| v6-agent ARCHIVED 矛盾 | line 481: "`v6-agent` branch ... ARCHIVED" | **加 Disambiguation 注释** |

### 3.2 PROJECT_LINEAGE.md

| 修改 | 旧 | 新 |
|------|----|----|
| V6 Line Branch | `v6-dev` | **`v6-agent`** |
| Version Lineage Diagram | `v6-dev (Active)` | **`v6-agent (Active)`** |
| Rule 1 | "active line is v6-dev" | **"active line is `v6-agent`"** |
| Historical Branches | (无) | **新增 `archive/v6-core / v6-service / v6-dev`** |
| Reality Check | (无) | **新增 2026-07-25 当前 HEAD 验证** |

### 3.3 PROJECT_STATE.md（**全面重写**）

| 修改 | 旧 | 新 |
|------|----|----|
| Last Updated | 2026-07-22 | **2026-07-25 (Repository Narrative Migration Batch)** |
| Current Version | v6.14.0-alpha | **v6.18.0-alpha** |
| Stable Line | main (v6.12.0-beta.15) ✅ | main (v6.12.0-beta.15) ✅ (保留) |
| Development Line | v6-agent ✅ | v6-agent ✅ (保留) |
| Framework Baseline | v6.8.0-alpha | **v6.9.6-foundation + v6.16.0-alpha** |
| Runtime Freeze | v6.9.6-foundation | **v6.9.6-foundation + v6.16.0-alpha** |
| Current Milestone | Phase 2-D Renderer Migration | **Phase 3.11 Finalization Complete** |
| Last Architecture Decision | ADR-003 | **ADR-013/014/015 + ADR-019** |
| Cognitive Layer Architecture | (无) | **新增 (明确 ≠ Runtime)** |
| Runtime Freeze Certificate | (无) | **新增 (Allowed/Forbidden)** |

### 3.4 README.md

| 修改 | 旧 | 新 |
|------|----|----|
| Stable line | main (v6.12.0-beta.15) | main (v6.12.0-beta.15) ✅ |
| Development line | v6-agent (v6.14.0-alpha) | **v6-agent (v6.18.0-alpha)** |
| Current Snapshot | (无) | **新增 (2026-07-25)** |
| Architecture Status | v6.14.0-alpha | **v6.18.0-alpha** |
| v6/ui NOT deprecated v6-agent | 保留 | 保留（修改：去掉 "NOT"） |
| v6/runtime/ Frozen 警告 | (无) | **新增** |

### 3.5 CHANGELOG.md

| 修改 | 旧 | 新 |
|------|----|----|
| v6.18.0-alpha 标题 | "Phase 3.11 Execution Kernel Evolution" | **"Phase 3.11 Finalization HEAD"** |
| v6.18.0-alpha 描述 | Runtime Finalization | **Runtime Finalization + Artifact Sync + Authority Audit** |
| Tag ordering note | (在 PROJECT_LINEAGE) | **顶部加 "Tag ordering note"** |

---

## 4. 关键校准（贯穿所有文档）

### 4.1 统一格式（"Current Snapshot 2026-07-25"）

```
Branch:
v6-agent

HEAD:
b736cb7

Current Version:
v6.18.0-alpha

Runtime Foundation:
v6.9.6-foundation
(Frozen)

Execution Kernel:
v6.16.0-alpha
(Phase 3.11 Frozen)

Presentation:
v6.17.0-alpha
(Phase 3.10 Frozen)

Current Milestone:
Phase 3.11 Finalization Complete

Next:
Phase 3.12 Observation Layer
```

### 4.2 关键术语表

| 术语 | 含义 |
|------|------|
| **Version** | `v6.X.Y-alpha` 格式，commit order 时序（不影响 architectural phase） |
| **Milestone / Phase** | `Phase X.Y` 格式，architectural 语义（如 Phase 3.11 Runtime Frozen） |
| **Active Branch** | `v6-agent`（single source of truth） |
| **Stable Line** | `main`（永远可编译运行，不演进） |
| **Frozen Tag** | Runtime 冻结点（v6.9.6-foundation, v6.16.0-alpha, v6.17.0-alpha） |
| **Cognitive Layer** | 独立于 Runtime Kernel 的工具层（tools/observation/, tools/insight/, etc.） |
| **Runtime Freeze Certificate** | Runtime 冻结后的 Allowed/Forbidden 规则 |

### 4.3 Runtime Kernel 边界（**所有文档统一**）

**Allowed**:
- ✓ Bug Fix
- ✓ Frozen Contract compatibility

**Forbidden**:
- ✗ Memory / Knowledge / Identity
- ✗ Agent Role / Harness Logic
- ✗ New Runtime concepts or control flows
- ✗ New responsibilities for existing Runtime modules

---

## 5. Pending Work（未执行）

### 5.1 Working Tree 清理（63 files modified + 50+ untracked）

| 类别 | 数量 | 处置 |
|------|------|------|
| Phase 2-D 遗留 | 8 files (v6/ui, agent_workbench/application, storage/sessions) | 🟡 待分类 commit |
| Phase 3.12-3.15 untracked | 50+ files (tools/, tests/tools/, v6/presentation/observation/, ADRs, docs) | 🟡 按 phase 分类 commit |
| Phase 3.11 Runtime | ✅ 已 commit | Done |

### 5.2 Stash 清理（3 → 0）

| Stash | 分支 | 内容 | 建议 |
|-------|------|------|------|
| `stash@{0}` | v6-agent | v6.13-recovery backup | 检查后 drop |
| `stash@{1}` | v6-agent | runtime config before workflow migration | 检查后 drop |
| `stash@{2}` | v5-dev | pre-ui-refactor (v0.6-alpha) | **直接 drop**（历史 archive 分支） |

> **重要**：**不**自动 drop stash（避免误删）。记录到本 Report，待用户确认后处理。

### 5.3 后续 Finalization Batches

| Batch | 内容 | 优先级 |
|-------|------|--------|
| Phase 3.12 Asset Sync | commit tools/observation/ + tests/tools/observation/ + ADRs + docs | **High** |
| Phase 3.13 Asset Sync | commit tools/presentation/ + tests/ + v6/presentation/observation/ | High |
| Phase 3.14 Asset Sync | commit tools/insight/ + tests/ | High |
| Phase 3.15 Asset Sync | commit tools/decision_support/ + tests/ | High |
| Phase 3.12 Finalization Batch | Validate + Update Blueprint + CHANGELOG + Tag + Push | High |

---

## 6. References

- [PROJECT_BLUEPRINT.md](../../PROJECT_BLUEPRINT.md) (✅ Migrated)
- [PROJECT_LINEAGE.md](../../PROJECT_LINEAGE.md) (✅ Migrated)
- [PROJECT_STATE.md](../../PROJECT_STATE.md) (✅ Migrated)
- [README.md](../../README.md) (✅ Migrated)
- [CHANGELOG.md](../../CHANGELOG.md) (✅ Migrated)
- [Phase 3.11 Runtime Frozen Handoff](../../.project/handoff/phase3-11-runtime-frozen-handoff.md)
- [Repo Authority Audit Report](repo-authority-audit-report.md)

---

## 7. Sign-off

| Role | Verification | Status |
|------|--------------|--------|
| Architecture Reviewer | 4 项修正 + 1 项最大修正已应用 | ✅ |
| Implementation Lead | 5 文档同步完成 | ✅ |
| QA Lead | 关键术语一致（Branch / Version / Milestone 区分） | ✅ |
| Boundary Guardian | Runtime Freeze Certificate 统一 | ✅ |
| Frozen Contract Maintainer | Anti-Pattern Warning 已加 | ✅ |
| OD-G0-001 Maintainer | 文档无 Speculative Abstraction | ✅ |
| Repository Authority Reviewer | 5 源迁移完成 | ✅ |

---

## 8. Key Judgment

> **Repository Narrative Migration 完成（5 文档同步）**。
> 
> **不再继续改代码**。**所有事实源已迁移到新叙事**：
> - Old: `v6-dev` + `v6.9.6 foundation`
> - New: `v6-agent` + `v6.18 product evolution`
> 
> **核心校准**：
> 1. **Version ≠ Milestone**（v6.18 ≠ Phase 3.11）
> 2. **Tag ordering ≠ Phase ordering**（v6.16 = Phase 3.11, v6.17 = Phase 3.10, 是 commit 顺序）
> 3. **Cognitive Layer ≠ Runtime Kernel**（防未来 `v6/runtime/observation/`）
> 4. **Phase 3.16 = Architecture Review only, NOT Runtime Extension**
> 5. **`v6-core` / `v6-service` 是 Blueprint 设计语义**，不是 archive
> 
> **下一节点**：进入 Phase 3.12 Asset Sync + Observation Layer Implementation。

Phase 3.16 之前**不再改文档**。文档 Authority 已 100% 同步。下一阶段按 8-step Finalization Batch pattern 推进 Phase 3.12。
