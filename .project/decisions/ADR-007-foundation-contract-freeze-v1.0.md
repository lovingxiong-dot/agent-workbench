# ADR-007 — Foundation Contract Freeze v1.0

> **Status**: FROZEN
> **Date**: 2026-07-22
> **Supersedes**: None
> **Scope**: Cross-product shared ancestor contracts

---

## 1. Context

After Project Identity Separation (ADR-005) and Workbench v6 Identity Freeze (ADR-006), the repository has clear product boundaries. However, the **shared ancestor** (CENTRE / AOS Foundation) is still undefined at the interface level.

Without explicit contracts:
- Workbench v6 may develop its own Runtime interface
- Future Agent Manager OS may develop its own Runtime interface
- Both products will need to be retrofitted to a shared contract

This ADR freezes the **shared ancestor interfaces** as v1.0 contracts.

---

## 2. Decision

**Freeze Foundation Contract v1.0** — four protocol packages in `presentation/protocols/foundation/`.

### 2.1 Runtime Contract (`runtime.py`)

| Symbol | Type | Purpose |
|--------|------|---------|
| `AgentRuntime` | Protocol | Agent Runtime interface (start/stop/execute/pause/resume/terminate) |
| `AgentRuntimeInfo` | dataclass | Runtime instance metadata |
| `ExecutionHandle` | dataclass | Reference to a submitted task |
| `RuntimeLifecycleState` | Enum | Runtime lifecycle (initializing/ready/running/paused/stopping/stopped/error) |

### 2.2 Event Contract (`event.py`)

| Symbol | Type | Purpose |
|--------|------|---------|
| `EventEnvelope` | dataclass | Cross-boundary event container |
| `EventChannel` | Enum | Channel classification (runtime/interaction/agent/workflow/system) |
| `EventBus` | Protocol | Publish/subscribe API |

### 2.3 Data Contract (`data.py`)

| Symbol | Type | Purpose |
|--------|------|---------|
| `AgentIdentity` | dataclass | Agent unique identification |
| `AgentType` | Enum | chat/coder/research/personal/custom |
| `AgentSession` | dataclass | Conversation session state |
| `AgentMessage` | dataclass | Single message in session |
| `WorkflowState` | dataclass | Workflow execution state |
| `WorkflowStep` | dataclass | Single step in workflow |
| `WorkflowPhase` | Enum | pending/planning/executing/paused/completed/failed/cancelled |
| `CapabilityDefinition` | dataclass | Capability description |
| `CapabilityParameter` | dataclass | Capability parameter |
| `CapabilityCategory` | Enum | tool/skill/workflow/memory/provider/custom |

### 2.4 Gateway Contract (`gateway.py`)

| Symbol | Type | Purpose |
|--------|------|---------|
| `Gateway` | Protocol | Provider/Model/Capability routing |
| `GatewayMode` | Enum | single_runtime/multi_runtime/federation |
| `GatewayRequest` | dataclass | Capability invocation request |
| `GatewayResponse` | dataclass | Capability invocation response |
| `ProviderEndpoint` | dataclass | Provider connection config |
| `ProviderProtocol` | Enum | openai/anthropic/deepseek/gemini/qwen/kimi/echo/custom |

---

## 3. Rules

### 3.1 Shared Ancestor Contract Rule

Any product (Workbench v6, future Agent Manager OS) MUST consume the Foundation Contract. Products cannot fork these interfaces.

### 3.2 Reverse Boundary Rule

Foundation Contracts define interfaces, not implementations. Adding implementations requires a separate ADR (ADR-008+).

### 3.3 Forbidden Imports

Foundation Contracts MUST NOT import:
- Any Runtime Implementation (`agent_workbench/runtime/`)
- Any UI Framework (`v6/ui/`, `PySide6`)
- Any Product-specific module (`WorkbenchController`, `V6UIApplication`)

### 3.4 Backward Compatibility

Foundation Contract is frozen at v1.0. Breaking changes require a new major version (v2.0) and Architecture Review.

---

## 4. Implementation

### 4.1 Files Created

- `presentation/protocols/foundation/__init__.py` — Package declaration + re-exports
- `presentation/protocols/foundation/runtime.py` — Runtime Contract
- `presentation/protocols/foundation/event.py` — Event Contract
- `presentation/protocols/foundation/data.py` — Data Contract
- `presentation/protocols/foundation/gateway.py` — Gateway Contract

### 4.2 No Code Changes Outside `protocols/`

This ADR defines interfaces only. No existing Runtime/UI files were modified.

### 4.3 Verification

```
✓ All Foundation symbols importable
✓ All dataclasses instantiable (smoke test)
✓ Zero Runtime Implementation import
✓ Zero UI framework import
✓ Multi Renderer Proof still passes
```

---

## 5. Consequences

### Positive

- Workbench v6 has a stable ancestor to consume
- Future Agent Manager OS can consume the same contracts
- No accidental interface drift between products
- Foundation Contract is now reviewable before implementation

### Negative

- Adding new capabilities requires updating contracts
- Future products cannot request contract changes after v1.0 freeze

### Neutral

- Foundation Contract v1.0 is the minimum viable surface
- Future versions (v1.1, v2.0) will extend based on product needs

---

## 6. Architecture Position

```
FOUNDATION.md (Identity — what is shared)
    ↓
ADR-007 (Contract — how is shared)
    ↓
presentation/protocols/foundation/ (Implementation — protocols)
    ↓
Workbench v6 / Agent Manager OS (Products — consume)
```

---

## 7. Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial Foundation Contract Freeze. |