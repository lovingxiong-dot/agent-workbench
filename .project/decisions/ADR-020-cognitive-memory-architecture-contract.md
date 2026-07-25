# ADR-020 — Cognitive Memory Architecture Contract

> **Status**: ACCEPTED
> **Version**: v0.3 (MVP-Focused)
> **Date**: 2026-07-25
> **Scope**: Phase 3.16 — Cognitive Continuity Layer + Harness Integration
> **Depends on**: ADR-016/017/018/019 (Frozen Phase 3.12-3.15)
> **Supersedes**: ADR-020 v0.1, v0.2
> **Important**: Architecture Review → MVP Implementation

---

## Amendment Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-07-25 | Initial draft (Boundary-only) |
| v0.2 | 2026-07-25 | Refined: Cognitive Memory Architecture Contract (4 Types / 7 Lifecycle / 5 Importance / Context Reconstruction) |
| **v0.3** | 2026-07-25 | **MVP-Focused: Cognitive Continuity Layer + Harness Integration**（5 Lifecycle / 3 Importance / Harness 整合） |

---

## 1. Purpose

按 Phase 3.16 v0.3 Refinement（避免过度设计）：

> 我们不是在设计一个 "完美治理的 Memory 标准"，而是在给 AOS / Workbench / CAO 建立一个真正可用的 **Cognitive Continuity System（认知连续性系统）**。
> 
> 解决三个真实问题：
> 1. 上下文压缩导致项目连续性丢失
> 2. 长期项目知识无法自动恢复
> 3. Agent 每次启动像新人，需要重新学习

本 ADR 收敛为 **Cognitive Continuity Layer + Harness Integration**：
- **不是** Memory Governance System
- **不是** AI Brain
- **不是** Persistent Memory（避免暗示自主学习）
- **是** Context Provider

**核心原则**：
- Memory 是 Context Provider，**不**是 Decision Engine / Runtime Controller / Learning Controller
- 长期认知连续性
- 不越过 Runtime 控制边界
- **MVP First**：先实现，不治理

---

## 2. Context

### 2.1 当前 Frozen 状态

- Phase 3.11 Frozen：Execution Kernel
- Phase 3.12 Frozen（ADR-016）：Observation Foundation
- Phase 3.13 Frozen（ADR-017）：Presentation & Consumption
- Phase 3.14 Frozen（ADR-018）：Agent Runtime Insight
- Phase 3.15 Frozen（ADR-019）：Agent Decision Support

### 2.2 当前问题（Refinement Motivation）

当前 Runtime Cognitive Pipeline v1：
```
Runtime
  ↓ Observation
ObservationReport
  ↓ Presentation
ObservationViewModel
  ↓ Insight
InsightArtifact (Understanding)
  ↓ Decision Support
DecisionSupportArtifact (Recommendation)
  ↓ requires_human_approval = True
Human / Agent
  ↓ NEW Execution
Runtime
```

**问题**：
- Agent 每次启动无法稳定恢复历史理解
- 上下文压缩导致架构决策、项目状态、工作流程丢失
- 缺乏 "Experience → Meaning Extraction → Memory Formation → Context Reconstruction" 闭环

### 2.3 v0.1 → v0.2 Refinement 原因

v0.1（Boundary-only）的问题：
- 偏 "安全治理型 Memory"
- 容易退化成 "文档仓库"
- 缺少 "动态连续性"

v0.2 升级：
- 引入 4 类 Memory（认知科学模型）
- 引入 Lifecycle（动态）
- 引入 Importance Scoring（价值评估）
- 引入 Context Reconstruction（解决长上下文压缩）
- 引入 3-Layer Authority（Human / Agent / Validated）

---

## 3. 核心重新定义：Cognitive Memory System (CMS)

### 3.1 CMS 定位

> **Agent 的长期认知连续性系统。**

**不是**：
- 数据库（Database）
- 知识库（Knowledge Base）
- 自动学习系统（Auto Learning System）
- Persistent Memory（避免暗示）

**是**：
```
Experience
    ↓
Meaning Extraction
    ↓
Memory Formation
    ↓
Context Reconstruction
    ↓
Better Understanding
```

### 3.2 总体架构

```
                         Human / CAO
                              |
                              |
                    Memory Governance Layer
                              |
================================================

                 Cognitive Memory System (CMS)

        ┌──────────────────────────────┐
        │      Memory Lifecycle        │
        │                              │
        │ Capture                      │
        │ Compress                     │
        │ Classify                     │
        │ Validate                     │
        │ Retrieve                     │
        │ Consolidate                  │
        │ Archive                      │
        └──────────────────────────────┘

        Memory Types (4 类)

        ┌────────────┐
        │ Working    │  临时上下文
        └────────────┘
        ┌────────────┐
        │ Episodic   │  事件经验
        └────────────┘
        ┌────────────┐
        │ Semantic   │  知识/规则
        └────────────┘
        ┌────────────┐
        │ Procedural │  Workflow经验
        └────────────┘

================================================

              Runtime
```

---

## 4. 4 类 Memory Types（认知科学模型）

### 4.1 Working Memory（工作记忆）

**内容**：当前任务上下文

**示例**：
```
当前任务: Phase 3.16 Architecture Review
当前约束: ADR-019 frozen
目标: 设计 Memory System
```

**生命周期**：小时级 / session 级

### 4.2 Episodic Memory（事件记忆）

**内容**："发生过什么"

**示例**：
```
2026-07-25
Phase 3.15 完成
Decision: Human Approval Boundary 保留
Reason: 避免 Runtime 自修改
```

**生命周期**：长期（人类经历式）

### 4.3 Semantic Memory（知识记忆）

**内容**："知道什么"

**包含**：
- ADR（如 ADR-016 / 017 / 018 / 019）
- Architecture Rule
- Frozen Contract
- Project State
- Open Questions

**示例**：
```
Observation Layer
位置: tools/observation
规则: 不得进入 Runtime Control Plane
来源: ADR-016
```

**生命周期**：长期（持久化知识）

### 4.4 Procedural Memory（流程记忆）

**内容**："如何完成事情"

**关键**：MetaFlow 位置

**示例**：
```
Architecture Change Workflow:
Requirement
  ↓
Architecture Review
  ↓
ADR
  ↓
Implementation Batch
  ↓
Validation
  ↓
Review
```

**生命周期**：长期（Workflow 经验）

**重要**：未来 Agent 能复用工程经验。

---

## 5. Memory Lifecycle（v0.3 简化）

### 5.1 v0.3 MVP 5 阶段

**v0.3 简化**：先 5 阶段 MVP，**不**实现 7 阶段。

```
Capture
   ↓
Classify
   ↓
Validate
   ↓
Store
   ↓
Retrieve
```

**未来扩展**（Phase 3.17+）：
- Compress
- Consolidate
- Archive

### 5.2 关键禁止

- 🚫 Memory Candidate 直接 Store（必须经 Validate）
- 🚫 Memory 自动修改 Runtime
- 🚫 Memory 形成 Self-reinforcing Loop

---

## 6. Memory Importance Scoring（v0.3 简化）

### 6.1 v0.3 MVP 3 维

**v0.3 简化**：先 3 维 MVP。

```yaml
MemoryScore:
  importance: 0.0-1.0
  stability: 0.0-1.0
  freshness: 0.0-1.0
```

**未来扩展**（Phase 3.17+）：
- relevance
- reuse_probability

### 6.2 3 维含义

| 维度 | 含义 |
|------|------|
| **importance** | Memory 本身的重要性（如 ADR 是 1.0） |
| **stability** | Memory 的稳定性（如 Frozen Contract = 1.0） |
| **freshness** | Memory 的新鲜度（时间衰减） |

### 6.3 评分示例

**ADR-019**：
```yaml
importance: 1.0
stability: 1.0  # Frozen
freshness: 0.8  # 近期
```

**普通聊天**：
```yaml
importance: 0.1
stability: 0.1
freshness: 0.5
```

### 6.4 Threshold

| 条件 | 动作 |
|------|------|
| `importance < 0.2` | Discard Candidate |
| `importance >= 0.7` + `stability >= 0.7` | 直接 Semantic Memory |
| `importance < 0.5` | 仅 Working / Episodic |

---

## 7. Context Reconstruction（核心）

### 7.1 旧 vs 新

**旧**（直接压缩 Conversation）：
```
100万 token 历史聊天
    ↓
直接压缩
    ↓
丢失架构决策
```

**新**（Memory → Context Reconstruction）：
```
历史交互
    ↓
Memory Extraction
    ↓
Structured Memory
    ↓
Context Loader
    ↓
Agent Startup Context
```

### 7.2 启动 AOS 项目时

**不是**加载"昨天所有聊天"，而是加载：

```
Relevant Cognitive Context:

Foundation Freeze v3.4
ADR-016 Observation
ADR-019 Decision Boundary
Current Milestone: Phase 3.16
Open Questions:
  - Memory Authority
  - Context Reconstruction
```

### 7.3 关键原则

**压缩的是 Memory，不是 Conversation。**

Memory 是 Structured（已提取 / 已压缩 / 已分类）。
Conversation 是 Raw（未压缩 / 容易丢失关键信息）。

---

## 8. Memory Authority 模型（3 层）

### 8.1 3 层结构

```
Layer 1: Human Memory
    → 直接写
    → 由 Human 提供

Layer 2: Agent Proposed Memory
    → 提出候选
    → 必须经 Validation

Layer 3: Validated Memory
    → 进入长期系统
    → 需 Human Approval (for critical) 或 Auto (for low-risk)
```

### 8.2 流程

```
Agent
    ↓
Memory Candidate
    ↓
Validation
    ↓
Memory Store
```

**不是**：
```
Agent
    ↓
Memory
```

### 8.3 Authority 模型

| Writer | Direct Write | Via Approval |
|--------|--------------|--------------|
| **Human** | ✅ Working / Episodic / Semantic / Procedural | N/A |
| **Agent** | ⚠️ Working only (low-risk) | ⚠️ Episodic / Semantic via Validation |
| **Insight** | 🚫 Prohibited | ⚠️ Approval Required (rare) |
| **Runtime** | 🚫 **永久禁止** | 🚫 **永久禁止** |

### 8.4 关键修正（vs v0.1）

**v0.1 错误**：Agent 完全不能写。

**v0.2 修正**：
- Agent 可写 Working Memory（低风险）
- Agent 可写 Episodic / Semantic **必须经 Validation**
- Runtime 写永久禁止（保持）

---

## 9. Memory 与 Decision Support 关系

### 9.1 保持默认 DISABLED

```
Memory
   ↓
Insight Context（仅 Context Reconstruction）
   ↓
Decision Support
   ↓
Human Approval（ADR-019 强制）
   ↓
Runtime
```

**禁止**：
```
Memory
   ↓
Decision
   ↓
Runtime
```

### 9.2 显式 Enable 流程

```
Human
  ↓
Architecture Review（必须）
  +
Human Approval（必须）
  ↓
Define influence scope
  ↓
Memory → Decision Support Enabled
```

### 9.3 Influence Scope（继承 v0.1）

| Memory → Decision | 状态 |
|-------------------|------|
| Historical Insight | ✅ 允许 |
| Preference（需 scope 限定） | ⚠️ |
| Knowledge / Semantic | 🚫 默认禁止 |
| Critical Decision | 🚫 永久禁止 |

---

## 10. Boundary Rules（继承 + 新增）

### 10.1 继承 ADR-016/017/018/019

```python
PHASE_3_16_FORBIDDEN = (
    # Runtime 写边界
    "v6.runtime.orchestrator", "v6.runtime.engine_manager",
    "v6.runtime.planner_loop", "v6.runtime.capability_router",
    # v6.9.6 Capability Frozen
    "agent_workbench.runtime.capability", "agent_workbench.runtime.decision",
    "agent_workbench.runtime.capability_registry",
    "agent_workbench.runtime.capability_router",
    "agent_workbench.runtime.decision_dispatcher",
)
```

### 10.2 新增 5 类禁止方向

| 方向 | 状态 |
|------|------|
| Memory → Runtime direct | 🚫 永久禁止 |
| Memory → Runtime via Decision Support | 🚫 默认 DISABLED + 需 Approval |
| Insight → Memory auto-write | 🚫 需 Approval |
| Runtime → Memory auto-write | 🚫 永久禁止 |
| Memory → Autonomous Learning | 🚫 永久禁止 |
| Memory → Self Modification | 🚫 永久禁止 |

---

## 11. Decision

### Decision 1 — CMS 命名

**规则**：Phase 3.16 正式名称为 **"Cognitive Memory System (CMS)"**。

**不命名为** "Persistent Memory" / "Learning System" / "Database"。

### Decision 2 — 4 类 Memory Types

**规则**：Phase 3.16 Memory 仅 4 类（认知科学模型）：

| Type | 内容 | 生命周期 |
|------|------|---------|
| Working | 当前任务上下文 | 小时/session |
| Episodic | 历史事件 | 长期 |
| Semantic | 知识/规则/ADR | 长期 |
| Procedural | Workflow 经验 | 长期 |

### Decision 3 — Memory Lifecycle

**规则**：7 阶段 Lifecycle：
1. **Capture** - 提取 Memory Candidate
2. **Compress** - 压缩内容
3. **Classify** - 分类到 4 类之一
4. **Validate** - Provenance 验证 / 边界检查
5. **Retrieve** - 按 query / context 检索
6. **Consolidate** - 周期性合并 / 升级
7. **Archive** - 长期不用的归档

**禁止**：
- Memory Candidate 自动 Store
- Memory 自动修改 Runtime
- Memory 形成 Self-reinforcing Loop

### Decision 4 — Importance Scoring

**规则**：每条 Memory 必须含 5 维评分：

```python
@dataclass(frozen=True)
class MemoryScore:
    importance: float  # 0.0-1.0
    relevance: float
    stability: float
    reuse_probability: float
    freshness: float
```

### Decision 5 — 3-Layer Authority

**规则**：
- **Layer 1 (Human)**: 直接写 4 类 Memory
- **Layer 2 (Agent)**: Working 直接写；Episodic / Semantic 经 Validation
- **Layer 3 (Validated)**: 进入长期系统

### Decision 6 — Memory Artifact Schema

**规则**：

```python
@dataclass(frozen=True)
class MemoryArtifact:
    """Phase 3.16 Memory Artifact（frozen）。"""
    id: str
    memory_type: MemoryType  # Working / Episodic / Semantic / Procedural
    content: Any
    score: MemoryScore  # 5 维评分
    source: MemorySource  # Human / Agent / Insight / Runtime
    created_at: float
    created_by: str
    provenance: ProvenanceRecord
    schema_version: str = "memory.v0.1"
```

### Decision 7 — Provenance Schema 强制

每个 Memory Entry 必须含 Provenance：

```python
@dataclass(frozen=True)
class ProvenanceRecord:
    """强制 Provenance 信息。"""
    source: MemorySource
    created_at: float
    created_by: str
    decision_support_artifact_id: Optional[str]
    approval_record: Optional[ApprovalRecord]
    trace_id: Optional[str]
```

**禁止**：
- 匿名 Memory
- 来源不明的 Memory
- 缺 Provenance 字段的 Memory

### Decision 8 — Context Reconstruction

**规则**：Agent 启动时按 Context Loader 重建上下文：

```python
def reconstruct_context(query: str, working_set: List[MemoryArtifact]) -> ContextSnapshot:
    """从 Memory 重建 Agent Context。"""
    # 1. 按 query 检索相关 Memory
    # 2. 按 score 排序
    # 3. 按 importance 过滤
    # 4. 输出 ContextSnapshot
```

**禁止**：直接压缩 Conversation。

### Decision 9 — Memory Store Interface 抽象

**规则**：Phase 3.16-B 必须定义 MemoryStore Interface（不绑定具体存储）：

```python
class MemoryStore(Protocol):
    """Memory Store 抽象接口。"""
    def store(self, artifact: MemoryArtifact) -> None: ...
    def retrieve(self, query: str, limit: int) -> List[MemoryArtifact]: ...
    def delete(self, artifact_id: str) -> None: ...
    def update(self, artifact: MemoryArtifact) -> None: ...
```

**未来可支持**：
- Local
- Vector DB
- Graph DB
- Hybrid

### Decision 10 — AI OS Cognitive Boundary Firewall 继承

按 Refinement 建议，**所有高级 Agent 能力必须继承**：

```text
Cognitive Authority Escalation

任何模块获得：
- Runtime Mutation
- Policy Mutation
- Execution Control
- Autonomous Action

=> Architecture Re-review
```

### Decision 11 — 位置约束

```
允许路径:
  - tools/memory/                    # Phase 3.16 主位置
  - tools/context/                   # Context Reconstruction
  - tests/tools/memory/              # 测试位置
  - docs/v6/phase3-16-*              # 设计与报告

禁止路径:
  - v6/runtime/*                     # Runtime Kernel Frozen
  - v6/presentation/models.py        # Frozen
  - v6/presentation/contracts/       # Frozen
  - agent_workbench/runtime/         # v6.9.6 Frozen
  - tools/observation/*              # Frozen ADR-016
  - tools/presentation/*             # Frozen ADR-017
  - tools/insight/*                  # Frozen ADR-018
  - tools/decision_support/*         # Frozen ADR-019
```

### Decision 12 — Re-Entry Triggers（v0.3 不变，32 项）

**v0.3 决策**：**保持 v0.2 的 32 项 Re-Entry Triggers，不新增**（避免 ADR 数量膨胀）。

**继承 26 项**：
- ADR-016 8 项
- ADR-017 6 项
- ADR-018 6 项
- ADR-019 6 项（含 Cognitive Authority Escalation）

**ADR-020 v0.2 新增 6 项**（v0.3 保留）：

| # | Trigger | 类型 |
|---|---------|------|
| 27 | Memory → Runtime direct read/write | 越界 |
| 28 | Insight → Memory auto-write (without approval) | 越界 |
| 29 | Memory → Decision Support default enabled | 越界 |
| 30 | Memory without provenance metadata | 越界 |
| 31 | Memory 影响 Critical Decision | 越界 |
| 32 | Memory 形成 self-reinforcing loop | 越界 |

**Total**: **32 项 Re-Entry Triggers（保持不变）**

### Decision 13 — Phase 3.16 MVP Implementation（v0.3 转入）

**规则**：Phase 3.16 v0.3 **进入 MVP Implementation**（不治理）。

- ✅ CMS Contract (v0.3)
- ✅ 4 Memory Types / 5 Lifecycle (v0.3 简化) / 3 Importance
- ✅ Context Reconstruction 抽象
- ✅ Harness Integration
- ✅ 32 项 Re-Entry Triggers（保持）
- ✅ MVP 5 Batches Implementation
- 🚫 不新增 ADR
- 🚫 不增加 Trigger
- 🚫 不治理化

---

## 12. 跨 Phase 边界

```
Phase 3.15 (Frozen ADR-019)
Agent Decision Support
    |
    v
Phase 3.16 (本文)
Cognitive Memory Architecture Contract
    |
    v (Phase 3.16-B)
Memory Lifecycle Engine (Capture/Compress/Classify/Validate/Retrieve/Consolidate/Archive)
    |
    v (Phase 3.17)
Context Reconstruction System
    |
    v (Phase 3.18)
CAO Memory Integration
    |
    v (Future)
Memory → Decision Support (显式 enable only)
    |
    v (Future)
Phase 4 Adaptive Runtime (if ever)
```

**禁止跨 Phase 越界**：
- 3.16 不得做 3.17+ 的事
- Memory Lifecycle Implementation 必须独立 ADR
- Context Reconstruction 必须独立 ADR

---

## 13. 与未来方向整合

| 方向 | 与 Phase 3.16 整合 |
|------|-------------------|
| **CAO** | 使用 Semantic + Episodic + Procedural |
| **AISE** | Memory Governance + Validation Rules |
| **MetaFlow** | Procedural Memory（Workflow 经验） |
| **上下文压缩** | Memory Consolidation |
| **MiniMax 借鉴** | Compression + Retrieval + Long Context Management |
| **Observation / Insight** | Experience Source |

---

## 14. 与现有 ADR 关系

| 现有 ADR | 与 ADR-020 关系 |
|---------|---------------|
| ADR-016-019 (Phase 3.12-3.15 Frozen) | Phase 3.16 消费其 output（间接） |
| **ADR-020 v0.2 Cognitive Memory Architecture Contract** | **NEW: Phase 3.16 Memory Contract（本 ADR）** |

---

## 15. 未来扩展

- **Phase 3.16-B**: Memory Lifecycle Engine（需新 ADR-021）
- **Phase 3.17**: Context Reconstruction System（需新 ADR-022）
- **Phase 3.18**: CAO Memory Integration（需新 ADR-023）
- **Phase 3.19+**: Memory → Decision Support Enable（需新 ADR-024）
- **Phase 4**: Adaptive Runtime（需独立 ADR + Runtime Re-Validation）

**未来 ADR 必须**：
- 不得违反 ADR-016/017/018/019/020 边界
- 触发 Re-Entry Trigger 时重新 Review
- Phase 3.16 当前 **不预创建** 任何 Memory Implementation / Learning / Adaptive 模块

---

## 16. Sign-off

| 角色 | 验证项 | 状态 |
|------|--------|------|
| Architecture Reviewer | CMS ≠ Boundary-only + 4 Types + Lifecycle + 3-Layer Authority | ✅ |
| Implementation Lead | Phase 3.16 Contract Defined (Architecture Review ONLY) | ✅ |
| QA Lead | Plan 可执行 | ✅ |
| Boundary Guardian | 26+8 = 34 Re-Entry Triggers | ✅ |
| Frozen Contract Maintainer | Zero modification | ✅ |
| OD-G0-001 Maintainer | No Speculative Abstraction | ✅ |
| AI OS Firewall Guardian | 全部高级 Agent 能力继承 | ✅ |
| Cognitive Continuity Reviewer | Context Reconstruction 抽象完成 | ✅ |

---

## 17. References

- [Phase 3.16 Cognitive Memory Design](../../docs/v6/phase3-16-cognitive-memory-design.md)
- [Phase 3.16 Architecture Review Report](../../docs/v6/phase3-16-architecture-review-report.md)
- [Phase 3.15 Completion Report](../../docs/v6/phase3-15-completion-report.md)
- [ADR-019 Agent Decision Support Boundary](ADR-019-agent-decision-support-boundary.md)
- [ADR-018 Agent Runtime Insight Boundary](ADR-018-agent-runtime-insight-boundary.md)
- [ADR-017 Observation Presentation Boundary](ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](ADR-016-observation-layer-contract.md)
- [Phase 3.11-E Freeze Validation Report](../../docs/v6/phase3-11-e-freeze-validation-report.md)