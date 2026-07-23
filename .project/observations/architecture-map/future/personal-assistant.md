# Personal Assistant Agent (Future Application Layer Candidate)

> **Type**: Future Application Layer Candidate (NOT part of Workbench v6 Foundation)
> **Status**: NOT DESIGNED — placeholder only

---

## Classification (Per OD-EX0-003)

| Aspect | Classification |
|--------|----------------|
| Personal Assistant Agent Layer | **Future Application Layer Candidate** |
| Long-term user identity | Future Application |
| User preference tracking | Future Application |

## Why This is NOT a Runtime Concern

If Personal Assistant Agent were added, **possible locations**:

| Option | Position | v6 Constitution Compliance |
|--------|----------|---------------------------|
| Option A | Runtime-level module | ❌ Violates P2 (Runtime Kernel Freeze) |
| Option B | Application-level entry | ✅ Consistent with P3 (Presentation Contract) |
| Option C | Identity Configuration | ✅ Consistent with P5 (Configuration-Driven) |

**Insight**: Option B or C align with v6 Constitution. Option A would require Constitution revision.

## Required Evidence for Future Decision

1. ✅ Tier A evidence from second consumer (per ADR-009)
2. ✅ Multi-round Architecture Review
3. ✅ Resolution of open questions:
   - Personal Assistant 是否是 Workbench 的唯一入口？
   - Agent Manager 放在哪一层？
   - Agent 与 Skill 的边界？
   - Memory 如何绑定 Agent？
   - 自动委派的状态机如何设计？

## Current State

```
Personal Assistant Agent: NOT IN WORKBENCH V6
Not because v6 is incomplete.
But because v6 has correctly bounded itself as Runtime Validation Platform.

Personal Assistant Agent is a FUTURE APPLICATION.
It will be built on top of Workbench v6, not inside it.
```

## Position in 5-Layer Model

```
Layer 4 Applications / Renderers
    ↓
[Future: Personal Assistant Application (built on Workbench v6)]
    ↓
Consumer of Workbench v6 InteractionEvent stream
```

## Reference

- [OD-EX0-003 v6 Constitution + External Synthesis §Section 2 External Gap](../../OD-EX0-003-v6-constitution-external-synthesis.md)
- [ADR-DRAFT-010 (NOT SUBMITTED)](../../OD-EX0-003-v6-constitution-external-synthesis.md#section-5-candidate-adr-draft-draft-only-not-submitted)