# ADR-008 — Runtime Closure Validation

> **Status**: ACTIVE — In Progress
> **Date**: 2026-07-22
> **Supersedes**: None
> **Scope**: Workbench v6 Runtime closure validation before any Foundation Freeze

---

## 1. Purpose

This ADR defines the **validation gate** that must pass before any Foundation Contract can be frozen at v1.0.

**Critical principle**: Protocol must be extracted from real Runtime, not designed ahead of Runtime.

The order is:
```
Reality Implementation
    ↓
Observed Pattern
    ↓
Contract Extraction
    ↓
Freeze
```

This ADR enforces that order.

---

## 2. Validation Gate

Foundation Contract v1.0 Freeze requires **all four validation loops** to close:

### 2.1 Runtime Identity Loop

Validates: `Agent Identity → Agent Runtime → Capability Runtime`

Test criteria:
- Each Agent has a unique, stable Identity (name, type, version, system_prompt)
- Runtime can spawn, pause, resume, terminate individual Agents
- Capabilities can be discovered, invoked, and routed within an Agent context

Pass condition: All four lifecycle operations (spawn/pause/resume/terminate) work end-to-end.

### 2.2 Event Flow Loop

Validates: `InteractionEvent → Gateway → Runtime`

Test criteria:
- Every user interaction produces exactly one InteractionEvent
- Gateway forwards event to correct Runtime instance
- Runtime processes event and produces response events
- Event correlation IDs preserve causality

Pass condition: Multi-turn conversation preserves context across Gateway hops.

### 2.3 Provider Boundary Loop

Validates: `Provider Adapter → Provider Registry → LLM Backend`

Test criteria:
- Provider Adapter wraps any LLM backend (OpenAI / DeepSeek / Claude / etc.)
- Provider Registry discovers and routes to correct Adapter
- Provider lifecycle (register/unregister/health) works without Runtime restart

Pass condition: Switching Provider mid-session does not break Runtime state.

### 2.4 Data Flow Loop

Validates: `Input → Context → Execution → Output`

Test criteria:
- User Input is normalized into Context
- Context drives Execution (single Agent or Workflow)
- Execution produces structured Output
- Output is consumable by both Renderer and other products

Pass condition: Data flow can be replayed end-to-end from Input to Output with deterministic shape.

---

## 3. Where to Validate

The validation happens inside **Workbench v6**. Workbench v6 is the experiment field where these loops are tested against real users.

```
Workbench v6 (experiment field)
    ↓
Real users exercise all four loops
    ↓
Observed patterns inform Foundation Contract
```

If a loop cannot be closed in Workbench v6, it cannot be frozen in Foundation Contract.

---

## 4. Validation Records

Each closed loop must produce a validation record:

| Loop | Status | Record Location |
|------|--------|-----------------|
| 2.1 Runtime Identity | pending | TBD after Phase 2-D.2 |
| 2.2 Event Flow | pending | TBD after Phase 2-D.2 |
| 2.3 Provider Boundary | pending | TBD after Phase 2-D.2 |
| 2.4 Data Flow | pending | TBD after Phase 2-D.2 |

When all four loops have a record marked `closed`, this ADR is complete and `ADR-009 Foundation Contract v1.0 Freeze` can be proposed.

---

## 4.1 Phase 2-D.2.1 Renderer Migration Validation Records

Per the review feedback, validation records must record **evidence**, not declare completion. Each record names the question, the evidence, and the status.

### Validation Record Status

```
ADR-008 Runtime Closure Validation

Status: VALIDATING

Validation Records:

ADR-008.1
Renderer Boundary Validation
Result: PASS

ADR-008.2
Gateway Path Validation
Result: PASS (de facto, all session ops now route through interaction_layer)

ADR-008.3
Runtime Independence Validation
Result: PASS

ADR-008.4
State Ownership Validation
Result: PASS
```

### ADR-008.1 — Renderer Boundary Validation

**Question**: Is Renderer purely Presentation?

**Evidence**:
- `presentation/renderers/v6_ui/event_renderer.py`: only imports `InteractionEvent`, `InteractionEventType`, and v6/ui panel references. Zero `agent_workbench.runtime.*` import. Zero Agent Logic.
- `presentation/renderers/v6_ui/shell_adapter.py`: only imports `ShellContract` and v6/ui public APIs (`update_sessions`, `set_title`, `reset_workspace`, `append_user`, `append_ai`, `show_file`, `append_terminal`).

**Result**: PASS.

### ADR-008.2 — Gateway Path Validation

**Question**: Is there a single Gateway entry, and is every Presentation path routed through it?

**Evidence (Phase 2-D.2.1)**:
- Before: `application/v6_ui_application.py` directly accessed `runtime.module_registry.get("session")` and `session_module.manager.get(sid)`, bypassing the InteractionLayer.
- After: `WorkbenchInteractionLayer` now provides 4 session/operation methods:
  - `list_conversation_groups()`
  - `create_conversation()`
  - `delete_conversation()`
  - `get_session_metadata()`
- `v6_ui_application.py` now calls only `interaction_layer.*` for both request submission and session operations.
- Grep verification: `runtime\.module_registry|orchestrator\.|session_module\.` in `application/` returns zero matches (excluding `from agent_workbench.runtime.interaction.request` which is a Protocol dataclass, not Runtime Implementation).
- CLI: `controller.interaction_layer.set_renderer(...)` + `controller.chat(text)` → `interaction_layer`.
- GUI: signal handlers → `interaction_layer.submit_request(RuntimeRequest(...))`.
- All UI signals (ChatArea / LeftPanel / RightPanel) converge to `interaction_layer.submit_request`.

**Result**: PASS (de facto — `WorkbenchInteractionLayer` is the single entry, not yet named Gateway).

### ADR-008.3 — Runtime Independence Validation

**Question**: Is Runtime truly self-governing, independent of UI?

**Evidence**:
- `AgentWorkbenchRuntime.__init__` takes only `config_path`. No UI dependency.
- `runtime/agent_runtime.py` imports: `v6.runtime.*`, `engines.*`, `runtime.capability.*`, `runtime.modules.*`. No `v6.ui.*`, no `PySide6`, no `WorkbenchUIController`.
- Runtime can be constructed and started without any UI component (CLI launches Runtime, GUI adds Presentation layer on top).
- `WorkbenchController` constructs Runtime internally — UI layer never touches Runtime directly.
- After Phase 2-D.2.1, no Presentation code path accesses `runtime.module_registry` or `session_module.manager` — Runtime's internal module registry is no longer a public surface.

**Result**: PASS.

### ADR-008.4 — State Ownership Validation

**Question**: Does State belong to Runtime, not UI or Foundation?

**Evidence**:
- Session State: `SessionModule` (Runtime kernel). Owner is Runtime.
- Decision State: `DecisionManager` (Runtime kernel). Owner is Runtime.
- Orchestrator State: `CoreAgentRuntime` (Runtime kernel). Owner is Runtime.
- UI State (Navigation / Workspace / Inspector): `ShellContract` (Presentation layer). Owner is Presentation.
- Foundation State: not defined (Candidate only — avoids premature abstraction).
- `ConversationService` is now accessed exclusively through `interaction_layer`, not directly from Application. Session ownership remains in Runtime.

**Result**: PASS.

---

## 4.2 Implication for ADR-007 / ADR-009

Phase 2-D.2.1 observations and migration confirm that Workbench v6 has **already** built the architectural pattern Foundation Contract v0.5 was trying to extract.

The interaction layer now exposes 4 session operation methods that match the `Foundation.Gateway` pattern (read/write operations on Conversation domain). Whether to extract these into a formal `Foundation.Gateway` Protocol depends on whether Agent Manager OS would need the same operations. Until that product exists, these methods stay on `WorkbenchInteractionLayer`.

**No new Contract / Protocol / Schema added during Phase 2-D.2.1.**

---

## 4.1 Phase 2-D.2 Implementation Observation

Phase 2-D.2 enters **Implementation Observation Mode**. No new Contract / Protocol / Schema introduced. Only four questions answered by reading current code:

### Q1: Is Renderer purely Presentation?

**Answer: YES (with evidence)**

Evidence:
- `presentation/renderers/v6_ui/event_renderer.py`: only imports `InteractionEvent`, `InteractionEventType`, and the v6/ui panel references. No `agent_workbench.runtime.*` import. No Agent Logic.
- `presentation/renderers/v6_ui/shell_adapter.py`: only imports `ShellContract` and v6/ui public APIs (`update_sessions`, `set_title`, `reset_workspace`, `append_user`, `append_ai`, `show_file`, `append_terminal`).

Renderer consumes InteractionEvent + Gateway (ShellContract). No Agent Logic.

### Q2: Is there a single Gateway entry?

**Answer: YES (de facto, not yet by name)**

Evidence:
- CLI: `controller.interaction_layer.set_renderer(...)` + `controller.chat(text)` (in `app.py:44-50`)
- GUI: `il.set_renderer(self._presentation)` + signal handlers call `il.submit_request(RuntimeRequest(...))` (in `v6_ui_application.py:107-141`)
- All UI signals (ChatArea / LeftPanel / RightPanel) converge to `interaction_layer.submit_request(RuntimeRequest)`
- All CLI text inputs converge to `controller.chat(text)` → `runtime.submit_request`

`WorkbenchController.interaction_layer` acts as the de facto Gateway. Future Mobile / IDE Plugin should also route through this single layer.

### Q3: Is Runtime truly self-governing?

**Answer: YES (with current evidence)**

Evidence:
- `AgentWorkbenchRuntime.__init__` takes only `config_path`. No UI dependency.
- `runtime/agent_runtime.py` imports: `v6.runtime.*`, `engines.*`, `runtime.capability.*`, `runtime.modules.*`. No `v6.ui.*`, no `PySide6`, no `WorkbenchUIController`.
- Runtime can be constructed and started without any UI component.
- `WorkbenchController` constructs Runtime internally — UI layer never touches Runtime directly.

Runtime is decoupled from Workbench UI. It can run headless.

### Q4: Does State belong to Runtime, not UI or Foundation?

**Answer: PARTIAL**

Evidence:
- Session State: `SessionModule` (Runtime 内核) ✅ — Owner is Runtime
- Decision State: `DecisionManager` (Runtime 内核) ✅ — Owner is Runtime
- Orchestrator State: `CoreAgentRuntime` (Runtime 内核) ✅ — Owner is Runtime
- UI State (Navigation / Workspace / Inspector): `ShellContract` (Presentation) ✅ — Owner is Presentation
- Foundation State: not defined yet (Candidate only) ✅ — Avoid premature abstraction

Risk observed:
- `ConversationService` (in `services/`) is called from `V6UIApplication._on_session_selected` to bridge Runtime Session data → Shell Workspace. This is acceptable as long as `ConversationService` does not own Session State — it only formats. Confirmed: `ConversationService` delegates to `SessionService` → `SessionModule.manager`. State ownership remains in Runtime.

### Observation Summary

| Question | Status | Risk |
|----------|--------|------|
| Q1 Renderer = Presentation | PASS | None |
| Q2 Single Gateway | PASS (de facto) | Future Mobile/Plugin must also route through interaction_layer |
| Q3 Runtime self-governing | PASS | None currently |
| Q4 State ownership | PASS | ConversationService is a bridge, not an owner |

### Implication for ADR-007 / ADR-009

The observation confirms that Workbench v6 has **already** built the architectural pattern Foundation Contract v0.5 was trying to extract. The remaining work is:

1. Complete Renderer Migration so all UI signal paths route through `interaction_layer.submit_request`
2. Validate that Provider switching mid-session preserves Runtime state
3. Validate that Data Flow (Input → Context → Execution → Output) is replayable
4. Then extract the observed patterns into `ADR-009 Foundation Contract v1.0 Freeze`

**No new Contract / Protocol / Schema added during Phase 2-D.2.**

---

## 5. What This ADR Does NOT Do

This ADR does **not** freeze Foundation Contract. It defines the gate, not the contract.

| Concern | This ADR | Foundation Freeze |
|---------|----------|------------------|
| Symbol shapes | No | Yes |
| Runtime name ownership | No | Yes |
| Provider enumeration | No | Yes |
| Data contract unification | No | Yes |

---

## 6. Foundation Status After This ADR

```
Foundation Contract v0.5: Candidate (non-binding)

Authority: NONE
Binding: NON-BINDING
Validation: PENDING (this ADR)
Next Milestone: Phase 2-D.2 Renderer Migration
```

The Foundation Contract at `presentation/protocols/foundation/` is a **candidate**, not a contract. Workbench v6 implementation is the source of truth until validation records close.

---

## 7. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Runtime Closure Validation ADR. |