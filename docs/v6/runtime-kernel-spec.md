# V6 Runtime Kernel Specification

> The Runtime Kernel is the stable execution contract of the V6 platform.
>
> Everything above the Kernel may evolve.
> Everything below the Kernel must preserve backward compatibility.

This document defines the architectural layers, ownership, responsibilities, and dependency rules of the V6 Runtime Kernel. It is not tied to any single release (e.g., v6.9.x); it serves as the long-term design contract for the entire V6 lifecycle.

---

## 1. Runtime Layer Diagram

```text
User / UI / MCP / Local Agent / Remote Agent
                    │
                    ▼
            RuntimeRequest
                    │
                    ▼
            Planning Layer
    (ManagerAI → Interpreter → Resolver → Policy)
                    │
                    ▼
              RuntimeDecision
                    │
                    ▼
                 Task Layer
                    │
                    ▼
           Capability Layer
                    │
     ┌──────────────┼──────────────┐
     │              │              │
     ▼              ▼              ▼
CapabilityContext  CapabilityExecutionState  ProviderBinding
     │              │              │
     └──────────────┼──────────────┘
                    │
                    ▼
           CapabilityRegistry
                    │
                    ▼
               Engine Layer
                    │
                    ▼
              Provider Layer
                    │
                    ▼
            External System
                  (LLM / Tool / MCP / Agent)
```

---

## 2. Layer Ownership & Responsibilities

| Layer | Owner | Responsibility | Forbidden |
|---|---|---|---|
| Request | Interaction Layer | Define external input protocol (`RuntimeRequest` / `UserRequest`) and map origin to `CapabilityContext.origin`. | Must not parse capability or make routing decisions. |
| Planning | Manager / Decision Layer | Generate `Task` from `RuntimeRequest` and produce `RuntimeDecision`. | Must not execute Engine or directly operate Provider. |
| Task | Runtime Core | Represent the execution contract: `id` / `capability` / `payload` / `metadata` / `created_at`. | Must not save UI state or UI concepts. |
| Capability | Runtime Core | Describe what a capability is (`CapabilityDefinition`), what context it needs (`CapabilityContext`), and what state it is in (`CapabilityState`). | Must not make routing decisions or execute Engine. |
| Engine | Runtime Core | Execute a capability according to the Engine Protocol and emit structured `RuntimeEvent`s. | Must not perform planning or choose Provider. |
| **Provider** | Adapter Layer | Adapt Runtime calls to external systems (LLM / Tool / MCP / Local Agent / Remote Agent). | Must not know about Capability routing or UI. |
| **Metadata** | Workbench Layer | Platform-agnostic description of Runtime objects exposed to Workbench. | Must not contain UI concepts or configuration schema. |

---

## 3. Runtime Dependency Rule

Dependencies must flow downward only. Higher layers may depend on lower layers; lower layers must never depend on higher layers.

```text
UI
 │
 ▼
Workbench Layer (Metadata → PresentationModel)
 │
 ▼
Interaction
 │
 ▼
Request
 │
 ▼
Planning
 │
 ▼
Task
 │
 ▼
Capability
 │
 ▼
Engine
 │
 ▼
Provider
 │
 ▼
External System
```

### Allowed dependencies

- Workbench Layer → Interaction
- Workbench Layer → Metadata (Runtime objects expose Metadata upward)
- Planning → Task
- Task → Capability
- Capability → Engine
- Engine → Provider
- Provider → External System

### Forbidden dependencies

- Provider → Planning
- Engine → Request
- Capability → UI
- Provider → Capability routing logic
- Engine → Decision logic
- Task → UI concepts (`QtSelection`, `QtWorkspace`, etc.)
- Metadata → UI concepts (`editor: slider`, `layout: horizontal`, etc.)

---

## 4. Capability Runtime Contract

Every capability integrated into the V6 Runtime must answer the following four questions:

1. **What is it?** — `CapabilityDefinition` (static description)
2. **What context does it need?** — `CapabilityContext` (typed sub-contexts)
3. **What is its lifecycle state?** — `CapabilityState` / `CapabilityExecutionState`
4. **How does Runtime manage it?** — `CapabilityRegistry` (state / context / provider binding references)

No capability is allowed to introduce a dedicated Runtime flow. All capabilities must register through the same contract.

---

## 5. Source vs. Capability Routing

`RuntimeRequest.source` (e.g., `GLOBAL_CHAT`, `WORKSPACE_SESSION`, `COMMAND_BAR`, `MCP`) is an **origin** environmental context. It may be copied to `CapabilityContext.origin`, but it must never influence:

- Capability selection
- Engine selection
- Provider selection
- Planning decisions

---

## 6. Registry Is an Index, Not a Database

`CapabilityRegistry` manages:

- Capability definitions (the capability tree)
- References to current execution state
- References to current execution context
- References to provider bindings

It must not store:

- Execution history
- Trace logs
- Statistics / metrics
- UI state
- Prompt templates
- Memory entries

---

## 7. Stability Guarantee

The following contracts are frozen and must preserve backward compatibility across V6 releases:

- `RuntimeRequest` external input protocol
- `Task` five-field model
- `CapabilityDefinition` static fields
- `CapabilityContext` typed sub-contexts
- `CapabilityState` lifecycle states
- `CapabilityRegistry` runtime index API
- Engine Protocol (single `RuntimeContext` input)

Everything else (UI rendering, Provider implementations, specific Planners, Archive strategies) may evolve above or below these contracts, but the Kernel contracts themselves must remain stable.

---

## 8. Workbench Layer Relationship

The Workbench Layer sits above the Runtime Kernel and is the product boundary:

- Runtime objects expose `Metadata` to Workbench.
- Workbench translates `Metadata` into `PresentationModel` via `MetadataAdapter`.
- UI consumes `PresentationModel`, not Metadata directly.
- Schema (v6.12.x) will describe how to configure objects; it lives in Workbench Layer, not Runtime Kernel.

This preserves Runtime Kernel stability while allowing Workbench to evolve independently.

## 9. Relationship to Other Documents

- [`PROJECT_BLUEPRINT.md`](../../PROJECT_BLUEPRINT.md) — Project lineage, current task, and Workbench evolution roadmap.
- [`CHANGELOG.md`](../../CHANGELOG.md) — Version-by-version changelog, including the v6.9.x Kernel Freeze Series note.
- `docs/v6/SPEC.md` — UI component signal contracts and interface boundaries.
- `docs/v6/runtime-glossary.md` — Definitions for Metadata, Schema, and PresentationModel.
