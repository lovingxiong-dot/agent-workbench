# Phase 3 — Consolidation Milestone

> **Status**: DESIGN v0.1
> **Date**: 2026-07-25
> **Phase**: Phase 3 Consolidation Gate
> **Depends on**: Phase 3.15 Frozen (ADR-019)
> **Output**: Foundation Snapshot + Architecture Map + ADR-020 v0.4
> **Mode**: **收敛 (NOT 开发)**

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial Consolidation Milestone Design |

---

## 1. Purpose

按 Architecture Reconciliation：

> 现在最大风险不是 Memory 设计，而是 **能力增长 > 架构同步能力**。

Phase 3 Consolidation 目标：

```
不是开发
   ↓
是收敛（Consolidation）
   ↓
目标：让项目从 "Phase 3.15 命名" 回到 "Git v6.17.0-alpha Foundation Snapshot"
```

**核心原则**：
- 不写新功能
- 不进入 Phase 3.16 Implementation
- 先审计、对齐、快照、冻结

---

## 2. Workbench v6 重新定位

### 2.1 当前层级

```
CENTRE Engineering Office
          |
          v
AOS Runtime Foundation
          |
          v
Agent Workbench v6 (Official Product Validation Platform)
          |
          +-- Runtime（Kernel Infrastructure，Frozen）
          |
          +-- Presentation（Renderer Contract，Frozen）
          |
          +-- tools/*（Cognitive Capability Layer，演进空间）
```

### 2.2 tools/ 重新定位

```
tools/
├── observation/        # Phase 3.12 ADR-016 (Frozen)
├── presentation/       # Phase 3.13 ADR-017 (Frozen)
├── insight/            # Phase 3.14 ADR-018 (Frozen)
├── decision_support/   # Phase 3.15 ADR-019 (Frozen)
├── memory/             # Phase 3.16 (Pending Consolidation)
├── harness/            # Phase 3.16+ (NEW, Pending Design)
└── context/            # Phase 3.16+ (Pending Consolidation)
```

---

## 3. 关键问题（Reconciliation 揭示）

### 3.1 Git Reality vs Narrative 失衡

| 维度 | 实际 | 声称 |
|------|------|------|
| Git HEAD | v6.15.0-alpha | - |
| Phase | 3.15 Frozen | 3.16 设计中 |
| 中间 | 缺失 3.9-3.16 资产 | - |

**问题**：大量架构资产（ADR-016/017/018/019/020）未反映到 Git Tag / CHANGELOG / Project Blueprint。

### 3.2 Runtime Frozen 矛盾

Phase 3.12-3.16 声称 **Runtime Frozen**，但 `v6/runtime/*` 有大量修改：

- orchestrator
- event_bus
- context
- enums
- execution_*

**必须审计**：这些修改属于：
- **A**: Phase 3.11 Execution Kernel 合法修改 → ✅ 接受
- **B**: 后续 Cognitive Layer 越界修改 → 🚫 必须回滚 / 重新 ADR

### 3.3 Harness 缺失

Memory 不能单独存在（按 Reconciliation）：
- Harness = Cognitive Runtime Coordinator
- 不存在 Harness → Memory 无法整合
- 必须先设计 Harness，再设计 Memory

### 3.4 专家团 vs Harness 重叠

```
Expert Team
   |
Harness

合并为：

Harness + Roles (Configuration)
   |
   +-- Architect
   +-- Reviewer
   +-- Developer
   +-- Researcher
   +-- Validator
```

---

## 4. Phase 3 Consolidation 5 Batches

### Batch 1 — Repository Alignment

**目标**：Git / CHANGELOG / Blueprint / Tag / Branch 对齐。

**输出**：
- `v6.17.0-alpha Foundation Snapshot`（Git Tag）
- `CHANGELOG.md` 完整更新（3.9-3.16 资产）
- `PROJECT_BLUEPRINT.md` 同步
- `docs/v6/PHASE-3-FOUNDATION-INDEX.md`（新增）

**检查项**：
- [ ] CHANGELOG 完整
- [ ] Blueprint 同步
- [ ] Git tag 准确
- [ ] Branch 状态清晰
- [ ] Phase 3.x 文档索引

### Batch 2 — Architecture Map Update

**目标**：新增 `current-architecture.md`。

**输出**：
- `docs/v6/current-architecture.md`

**内容**：
- Runtime Kernel
- Presentation Contract
- Cognitive Layer（Observation / Insight / Decision Support / Memory / Harness / Context）
- 关系图
- ADR 索引
- Frozen 状态

### Batch 3 — Cognitive Layer Boundary

**目标**：冻结 tools/ 7 模块关系。

**冻结**：
```
tools/
├── observation/        # Phase 3.12 (Frozen)
├── presentation/       # Phase 3.13 (Frozen)
├── insight/            # Phase 3.14 (Frozen)
├── decision_support/   # Phase 3.15 (Frozen)
├── memory/             # Phase 3.16 (Pending)
├── harness/            # Phase 3.16+ (Pending)
└── context/            # Phase 3.16+ (Pending)
```

**关系**：
```
Memory
   ↓ (Context Provider)
Context Manager
   ↓
Insight
   ↓
Decision Support
   ↓
Harness (Coordinator)
   ↓
Runtime
```

### Batch 4 — Harness Design Review（仅设计）

**目标**：设计 Harness Architecture。

**输出**：
- `ADR-020 v0.4: Cognitive Continuity & Harness Architecture Contract`
- `tools/harness/` 架构设计
- `docs/v6/phase3-16-harness-design.md`

**不实现**（仅设计）。

### Batch 5 — Runtime Boundary Audit（关键）

**目标**：审计 `v6/runtime/*` 修改。

**审计问题**：
- 每个修改属于 A（合法）还是 B（越界）？
- B 类修改必须回滚 / 重新 ADR

**输出**：
- `docs/v6/phase3-runtime-boundary-audit.md`
- A 类修改：列表 + 接受
- B 类修改：列表 + 回滚方案

---

## 5. 未来路线

```
Phase 3.15 Complete (Approved)
    ↓
Phase 3 Consolidation Gate ← 现在最高价值
    |
    +-- Runtime Boundary Audit
    |
    +-- Git Alignment
    |
    +-- Architecture Snapshot
    |
    +-- Harness Design (仅设计)
    |
    v
Phase 3.16 Cognitive Continuity + Harness Architecture
    |
    v
Memory MVP
    |
    v
Context Reconstruction
    |
    v
CAO Integration
```

---

## 6. ADR-020 v0.4 重命名

| 旧 | 新 |
|----|----|
| Cognitive Memory Architecture Contract | **Cognitive Continuity & Harness Architecture Contract** |

理由：Memory 是其中一个能力，**不是**全部。

---

## 7. Harness 重新定义

**不是** Expert Team，是 **Cognitive Runtime Coordinator**。

```
Agent Harness
    |
Context Manager
    |
Memory System
    |
Role System
    |
Skill Runtime
    |
Workflow Engine
    |
Validation Layer
    |
Decision Support Adapter
```

**专家 = Role Configuration**：

```
Roles:
  - Architect:
      capabilities: [architecture_review, adr_analysis]
      memory_access: {semantic: true, episodic: true}
  - Reviewer: ...
  - Developer: ...
  - Researcher: ...
  - Validator: ...
```

---

## 8. 关键能力归属

| 能力 | 归属 |
|------|------|
| Memory | Agent Harness → Cognitive Continuity Layer |
| Context Reconstruction | Harness → Startup Recovery |
| MetaFlow | Procedural Memory（Workflow 经验） |
| MiniMax 借鉴 | Compression + Retrieval Strategy |
| AISE | Validation / Provenance |
| Observation | Experience Source |
| Decision Support | Agent Harness → Adapter |

---

## 9. 验收标准

### 必须

- ✅ Repository Alignment（v6.17.0-alpha Tag）
- ✅ Architecture Map Update
- ✅ Cognitive Layer Boundary 冻结
- ✅ Harness Design（仅设计，不实现）
- ✅ Runtime Boundary Audit 完成
- ✅ A / B 类修改分类清晰
- ✅ B 类越界修改回滚

### 禁止

- ❌ 写新功能
- ❌ 进入 Phase 3.16-B Memory Implementation
- ❌ 新增 ADR（除非 Runtime Audit 发现 B 类）
- ❌ 治理化扩张

---

## 10. 关键判断

> **Phase 3 Consolidation Gate = 现在最高价值节点**。
> 
> 不是开发，是收敛。
> 
> 关键风险：
> 1. Git Reality vs Narrative 失衡
> 2. Runtime Frozen 矛盾（必须审计）
> 3. Harness 缺失（Memory 无法整合）
> 4. 专家团与 Harness 重叠
> 
> Phase 3.15 → 3.16 → 3.17 → 3.18 单线推进是错误的。
> 
> 正确路线：
> Phase 3.15 → Phase 3 Consolidation → Phase 3.16
> 
> 解决 Reconciliation 4 个问题后，再进入 Memory Implementation。

---

## 11. References

- [Phase 3.15 Completion Report](phase3-15-completion-report.md)
- [ADR-020 v0.3 Cognitive Memory Architecture Contract](../decisions/ADR-020-cognitive-memory-architecture-contract.md)
- [ADR-019 Agent Decision Support Boundary](../decisions/ADR-019-agent-decision-support-boundary.md)
- [Phase 3.12-3.15 Frozen ADRs](../decisions/)
- [Phase 3.11-E Freeze Validation Report](phase3-11-e-freeze-validation-report.md)