# ADR-006 — Workbench v6 Identity Freeze

> **Status**: FROZEN
> **Date**: 2026-07-22
> **Supersedes**: None
> **Scope**: Workbench v6 product scope and non-goals

---

## 1. Context

After Project Identity Separation (ADR-005), the repository now contains CENTRE / AOS Foundation plus one active product: Workbench v6. To prevent scope creep, the boundaries of Workbench v6 must be explicitly frozen.

Without this freeze, future agents and contributors will:
- Add multi-agent scheduling features to Workbench v6
- Add federation or routing logic to Workbench v6
- Add global agent registry to Workbench v6
- Add tenant governance to Workbench v6

These features belong to Agent Manager OS, not Workbench v6.

---

## 2. Decision

**Workbench v6 Identity is frozen.**

### 2.1 Belongs to Workbench v6

| Capability | Description |
|------------|-------------|
| Chat Workspace | User ↔ Agent single conversation |
| Agent Runtime Interaction | Single agent execution context |
| Workflow Execution | Single workflow / task running |
| Tool Use | Single agent calling tools |
| Memory Interaction | Single agent reading/writing memory |
| User Experience | Local UI, single user, single session |

### 2.2 Does NOT Belong to Workbench v6

| Capability | Why Not | Belongs To |
|------------|---------|------------|
| Multi Agent Scheduling | Workbench serves single agent | Agent Manager OS |
| Federation | Cross-runtime coordination | Agent Manager OS |
| Global Registry | Multi-runtime agent lookup | Agent Manager OS |
| Tenant Governance | Multi-tenant isolation | Agent Manager OS |
| Permission Control Plane | Cross-agent authorization | Agent Manager OS |

---

## 3. Consequences

### Positive

- Workbench v6 cannot absorb governance features by accident
- Agent Manager OS has a clear scope for future development
- Shared ancestor (FOUNDATION) is the only layer that can be modified without product-specific review

### Negative

- Some features requested by users may not fit in Workbench v6
- Future Agent Manager OS must be designed carefully to avoid overlap

### Neutral

- This ADR defines scope, not implementation timeline
- Workbench v6 can invoke shared Foundation capabilities (Protocol, Runtime, etc.)

---

## 4. Implementation

### 4.1 Files Created

- This ADR (`.project/decisions/ADR-006-workbench-v6-identity-freeze.md`)

### 4.2 Files Updated

- [PROJECT_DECLARATION.md](../../PROJECT_DECLARATION.md) — Added Workbench v6 Scope section

### 4.3 No Code Changes

This is a documentation-only decision. No code was modified.

---

## 5. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Workbench v6 identity freeze. |