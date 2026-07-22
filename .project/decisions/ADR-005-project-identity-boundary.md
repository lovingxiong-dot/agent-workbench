# ADR-005 — Project Identity Boundary

> **Status**: FROZEN
> **Date**: 2026-07-22
> **Supersedes**: None
> **Scope**: Product identity separation within the CENTRE ecosystem

---

## 1. Context

The repository `agent-workbench` has been treated as a single product ("Agent Workbench OS"). However, the architecture has evolved to support two distinct products:

1. **Workbench v6** — Agent Workspace (single-agent, workflow, chat UI)
2. **Agent Manager OS** — Governance & Control Plane (multi-agent, routing, dashboard)

Both share a common ancestor: the CENTRE / AOS Foundation (Protocol, Runtime, Data Contract, Gateway).

The risk: if these two products remain conflated under a single name, future agents and contributors will:
- Add governance features to the workspace UI
- Add workspace features to the governance layer
- Fork the shared runtime instead of reusing it
- Create cross-boundary dependencies that are hard to undo

---

## 2. Decision

**Create explicit product identity boundaries.**

### 2.1 Repository Identity

The repository `agent-workbench` contains:
- **Workbench v6** — the active product
- **CENTRE/AOS design documents** — architecture reference
- **Future Agent Manager OS** — separate product boundary

### 2.2 Shared Ancestor

`FOUNDATION.md` defines the shared ancestor (CENTRE / AOS):

| Capability | Shared | Workbench v6 | Agent Manager OS |
|------------|:------:|:------------:|:----------------:|
| Protocol | ✅ | ✅ | ✅ |
| Runtime | ✅ | ✅ | ✅ |
| Event Bus | ✅ | ✅ | ✅ |
| Data Contract | ✅ | ✅ | ✅ |
| Gateway | ✅ | ✅ | ✅ |
| Workflow Engine | ✅ | ✅ | Can invoke |
| Chat UI | ❌ | ✅ | ❌ |
| Dashboard UI | ❌ | ❌ | ✅ |

### 2.3 Product Boundaries

Each product has its own constitution:
- Workbench v6 → `PROJECT_DECLARATION.md`
- Agent Manager OS → `PROJECT_DECLARATION_MANAGER.md` (future)

Shared ancestor rules → `FOUNDATION.md`

### 2.4 Agent Entry Rule

Every agent entering the repository must first identify which target system they are modifying:

```
Target System Checklist:

[ ] FOUNDATION (Shared Ancestor) — Requires Architecture Review
[ ] Workbench v6 — Current active product
[ ] Agent Manager OS — Future product
[ ] Documentation Only — No code changes
```

---

## 3. Consequences

### Positive

- Clear separation between workspace and governance concerns
- Shared ancestor explicitly defined and protected
- Future Agent Manager OS can reuse Runtime without forking
- Agents cannot accidentally modify the wrong product

### Negative

- Added governance overhead (FOUNDATION.md, Target System Checklist)
- Repository naming may cause confusion until Agent Manager OS is extracted

### Neutral

- Repository name `agent-workbench` remains for historical continuity
- Long-term: may need to rename to `centre-platform` and extract products

---

## 4. Implementation

### 4.1 Files Created

- `FOUNDATION.md` — Shared ancestor definition

### 4.2 Files Updated

- `PROJECT_DECLARATION.md` — Clarified as Workbench v6 Constitution
- `ROOT_INDEX.md` — Reflects CENTRE ecosystem structure
- `AGENT_ENTRY.md` — Added Target System Checklist, updated reading order
- `PROJECT_STATE.md` — Added Product Identity section

### 4.3 No Code Changes

This is a documentation-only decision. No code was modified.

---

## 5. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial decision. Project Identity Boundary. |