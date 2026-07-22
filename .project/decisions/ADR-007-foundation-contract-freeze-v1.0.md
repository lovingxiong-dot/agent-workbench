# ADR-007 — Foundation Contract Introduction v0.5

> **Status**: PROPOSAL (Not Frozen)
> **Date**: 2026-07-22
> **Supersedes**: ADR-007 Foundation Contract Freeze v1.0 (reverted)
> **Scope**: Foundation Contract introduction — proposal stage

---

## 1. Decision Status

**v0.5 PROPOSAL — Not Frozen**

This ADR introduces Foundation Contract symbols as **proposal**, not as a frozen v1.0 contract. The previous version (ADR-007 v1.0 Frozen) was reverted based on Architecture Review.

**Reverted Status**:
- The previous Foundation Contract Freeze v1.0 was premature
- Real product behavior (Workbench v6 Runtime, Renderer, etc.) has not yet validated the contracts
- Data Contract duplicates already exist (`shell/protocol.py` has overlapping models)

**Current Status**:
- Symbols live at `presentation/protocols/foundation/`
- They are **proposals** — may change without major version bump
- Future v1.0 Freeze requires:
  1. Workbench v6 Runtime implements AgentRuntime
  2. Renderer consumes Gateway interface
  3. Data Contract duplication resolved
  4. Provider enumeration validated against real Provider needs

---

## 2. What Was Reverted

| Symbol | Previous Status | New Status | Reason |
|--------|----------------|-----------|--------|
| `AgentRuntime` | v1.0 Frozen Protocol | v0.5 Proposal | Runtime name conflicts with existing `v6.runtime.runtime.AgentRuntime` |
| `EventBus` | v1.0 Frozen Protocol | v0.5 Proposal | Real EventBus shape not validated |
| `AgentIdentity` | v1.0 Frozen dataclass | v0.5 Proposal | Overlaps with `shell/protocol.py` |
| `AgentSession` | v1.0 Frozen dataclass | v0.5 Proposal | Overlaps with `shell/protocol.py` |
| `WorkflowState` | v1.0 Frozen dataclass | v0.5 Proposal | Overlaps with `shell/protocol.py` |
| `CapabilityDefinition` | v1.0 Frozen dataclass | v0.5 Proposal | Not validated against real Capability Registry |
| `Gateway` | v1.0 Frozen Protocol | v0.5 Proposal | Mode enumeration (federation) not validated |
| `ProviderProtocol` | v1.0 Frozen Enum | v0.5 Proposal | Locked-in Provider enumeration is risky |

---

## 3. Risks Identified (Architecture Review)

### 3.1 Data Contract Duplication (HIGH)

Existing models in `shell/protocol.py`:
- `NavigationGroup`, `NavigationItem`, `WorkspaceMessage`, `WorkspaceState`, `InspectorState`, `CommandState`

Proposed models in `foundation/data.py`:
- `AgentIdentity`, `AgentSession`, `AgentMessage`, `WorkflowState`, `WorkflowStep`, `CapabilityDefinition`

Overlap risk: `AgentMessage` vs `WorkspaceMessage`. Both represent agent↔user messages but have different shapes. Unifying requires Architecture Review.

### 3.2 Runtime Name Conflict (MEDIUM)

The symbol name `AgentRuntime` collides with `v6.runtime.runtime.AgentRuntime` (the existing core Runtime). The Protocol symbol should be renamed to `RuntimeContract` or `AgentRuntimeProtocol` to avoid confusion.

### 3.3 Provider Enumeration Lock-in (MEDIUM)

`ProviderProtocol` enum hardcodes 7 providers (openai/anthropic/deepseek/gemini/qwen/kimi/echo). Future providers (new LLM vendors, custom APIs) would require Protocol updates. The enum should be replaced with `str` literal type or extensible registry.

### 3.4 Premature Freeze (HIGH)

v1.0 Freeze before Workbench v6 Runtime implements the contracts means:
- Real product feedback cannot influence the contract
- Any mistake becomes a frozen interface
- Future Agent Manager OS may inherit a flawed contract

### 3.5 Location Risk (MEDIUM)

Placing Foundation Contracts under `presentation/protocols/` is unusual. Foundation is meant to be product-agnostic, but Presentation is Workbench v6's domain. Consider relocating to `agent_workbench/foundation/` (a shared ancestor namespace).

---

## 4. What Remains

The Foundation Contract **concept** is correct:
- Workbench v6 and future Agent Manager OS should share ancestor contracts
- Runtime / Event / Data / Gateway are the right dimensions
- Products must consume, not fork, the ancestor

The Foundation Contract **implementation details** are still proposal:
- Symbol names may change
- Data models may merge or split
- Provider enumeration may become extensible

---

## 5. Next Step

**Phase 2-D.2 Renderer Migration — Workbench v6 closure.**

After Workbench v6 has a working closed loop:
- Runtime implements Foundation.AgentRuntime
- Renderer consumes Foundation.Gateway
- Data Contract duplication resolved

Then:
- ADR-008 Foundation Contract Freeze v1.0 (after Workbench v6 validation)

---

## 6. Architecture Position

```
Foundation Identity (FOUNDATION.md)
    ↓
Foundation Contract PROPOSAL v0.5 (this ADR)
    ↓
Workbench v6 implementation validates contracts
    ↓
Foundation Contract v1.0 FREEZE (ADR-008 future)
```

---

## 7. Version

| Version | Date | Change |
|---------|------|--------|
| v0.5 | 2026-07-22 | Reverted v1.0 Freeze. Status: PROPOSAL. |
| v1.0 (reverted) | 2026-07-22 | Initial v1.0 Freeze — reverted by Architecture Review. |