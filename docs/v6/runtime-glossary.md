# V6 Runtime Glossary

> A single vocabulary for the V6 platform. If a term appears in architecture discussions, it must map to one of these definitions.

---

## Core Runtime Terms

| Term | Definition |
|---|---|
| **Runtime** | The V6 execution platform. It receives requests, plans tasks, routes capabilities, executes engines, and emits events. |
| **Runtime Kernel** | The stable six-layer execution contract: Request → Planning → Task → Capability → Engine → Provider. |
| **RuntimeContext** | The single public protocol passed between Runtime components. All state converges here. |
| **Request** | The external input protocol that enters the Runtime. Encapsulates text, attachments, origin, and metadata without expressing routing intent. |
| **Planning** | The process of converting a Request into a Task. Includes intent classification, capability resolution, and policy evaluation. |
| **Manager** | The default implementation of Planning. Responsible for `UserRequest → Capability → Task`. |
| **Decision Layer** | The Runtime Control Plane that produces a `RuntimeDecision` from a `UserRequest`. |
| **Task** | The unique execution unit inside the Runtime. Five fields: `id`, `capability`, `payload`, `metadata`, `created_at`. |
| **Capability** | A definition of what the system can do. Pure data: no Runtime state, no Provider details, no UI concepts. |
| **CapabilityContext** | The environment context a Capability needs to execute: workspace, selection, attachments, session, parameters, etc. |
| **CapabilityState** | The lifecycle state of a Capability execution: PENDING, RESOLVED, SCHEDULED, RUNNING, COMPLETED, FAILED, CANCELLED, TIMEOUT, SKIPPED. |
| **CapabilityRegistry** | The Runtime index for Capability definitions and their runtime references (state, context, provider binding). |
| **Engine** | The execution protocol for a Capability. Receives a single `RuntimeContext` and emits structured `RuntimeEvent`s. |
| **Provider** | The conceptual adapter layer that decides which external system executes a Capability. Managed by Provider Runtime. |
| **Adapter** | A concrete implementation of a Provider: `Runtime → External System`. |
| **Metadata** | A platform-agnostic description of a Runtime object: `id`, `type`, `name`, `icon`, `properties`, `statistics`, `actions`. Runtime uses it to expose objects to Workbench without UI coupling. |
| **Schema** | A declarative description of how to configure a Runtime object. Drives Dialog / Inspector / JSON Editor / Validator / Import / Export generation. |
| **PresentationModel** | The UI-facing translation of Metadata. Navigator / Inspector / StatusBar consume PresentationModel, never Metadata directly. |
| **Orchestrator** | The Runtime component that executes Tasks by selecting Engines and managing their lifecycle. |
| **EventBus** | The Runtime communication backbone. Components publish and subscribe to `RuntimeEvent`s. |
| **RuntimeTrace** | The structured execution record: Task → Capability → Engine → Provider → Execution → Request → Response. |
| **Replay** | The ability to reproduce a Task execution from its Trace record. |

---

## Interaction Terms

| Term | Definition |
|---|---|
| **Interaction** | The boundary between Runtime and UI. Converts external inputs into `RuntimeRequest`s and Runtime events into `InteractionEvent`s. |
| **RuntimeRequest** | The external input protocol. Contains `source` (origin), `text`, `attachments`, `action_id`, and `metadata`. |
| **source** | An environmental origin: `GLOBAL_CHAT`, `WORKSPACE_SESSION`, `COMMAND_BAR`, `MCP`, `LOCAL_AGENT`. Not a routing instruction. |
| **InteractionEvent** | The UI-facing event protocol. Carries `type`, `request_id`, `source`, `task_id`, and `payload`. |
| **UIEventRenderer** | The protocol that consumes `InteractionEvent`s and renders them in a UI framework (Qt, Web, CLI). |

---

## Workspace & Identity Terms

| Term | Definition |
|---|---|
| **Workspace** | A project context containing files, selection, terminal state, git branch, and running tasks. |
| **WorkspaceSession** | A session scoped to a specific Workspace, distinct from Global Chat. |
| **WorkspaceSnapshot** | A point-in-time summary of Workspace state used by Planning. |
| **Origin** | The source environment of a Request. Used for context, never for routing. |
| **Session** | A conversation context. One Runtime may host multiple Sessions. |

---

## Archive Terms

| Term | Definition |
|---|---|
| **Archive** | The post-execution process: verify, reflect, repair, replay, score, persist. |
| **Archive Runtime** | The future Runtime subsystem that archives code, images, video, browser sessions, and chat results uniformly. |
| **Reflection** | The step that evaluates whether a Task output meets expectations. |
| **Repair** | The step that attempts to fix a failed or suboptimal output. |
| **Persist** | The step that stores the verified output into long-term storage. |

---

## Governance Terms

| Term | Definition |
|---|---|
| **Single Source of Truth** | For every asset (document, model, configuration), there is exactly one official version in the workspace. |
| **Generated File** | A file that can be recreated from source: `__pycache__`, `build/`, `dist/`, `.pytest_cache/`. |
| **Repository Governance** | The rules that keep the workspace clean, navigable, and free of historical noise. |
| **Repository Map** | The auto-generated directory overview: `docs/v6/repository-map.md`. |

---

## Anti-Terms

These words must not appear inside the Runtime Kernel with UI-specific meanings:

| Term | Why Avoided |
|---|---|
| `QtSelection` | UI concept. Runtime uses `SelectionContext`. |
| `QtWorkspace` | UI concept. Runtime uses `WorkspaceContext`. |
| `ChatBox` | UI widget. Runtime sees `GLOBAL_CHAT` origin. |
| **Plugin** | Ambiguous at the Runtime Kernel level. Use `Capability` for runtime capability, or reserve `Plugin` for Workbench-level extension packaging in v6.13.x+. |
| `Function` | Ambiguous. Runtime uses `Capability` or `Tool`. |

---

## See Also

- [`runtime-kernel-spec.md`](./runtime-kernel-spec.md) — Runtime architecture and dependency rules.
- [`repository-governance.md`](./repository-governance.md) — Repository organization rules.
- [`repository-map.md`](./repository-map.md) — Auto-generated directory overview.
