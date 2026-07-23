# Runtime Kernel Boundary

> **Layer**: 0 — Foundation Runtime
> **Status**: Frozen since v6.9.6-foundation (2026-07-09)

---

## Source Evidence

- [ADR-008 Runtime Closure Validation](../../decisions/ADR-008-runtime-closure-validation.md) — v2.0 closed
- [Architecture Constitution v6.13](../../../../agent_workbench/docs/v6/architecture-constitution-v6.13.md) — Principle 2

## Frozen Modules (from Constitution P2)

| Module | Path | Freeze Date |
|--------|------|-------------|
| `AgentRuntime` | `agent_workbench/runtime/agent_runtime.py` | v6.9.6-foundation |
| `ModuleRegistry` | `agent_workbench/runtime/module_registry.py` | v6.9.6-foundation |
| `BaseRuntimeModule` | `agent_workbench/runtime/modules/base.py` | v6.9.6-foundation |
| `ConfigStore` | `agent_workbench/runtime/config_store.py` | v6.9.6-foundation |
| `CapabilityRouter` | `agent_workbench/runtime/capability_router.py` | v6.9.6-foundation |
| `CapabilityRegistry` | `agent_workbench/runtime/capability/` | v6.9.6-foundation |
| `InteractionEvent` | `agent_workbench/runtime/interaction/event.py` | v6.9.5-alpha |
| `InteractionLayer` | `agent_workbench/runtime/interaction/layer.py` | v6.9.5-alpha |
| `DecisionManager` | `agent_workbench/runtime/manager/decision_manager.py` | v6.9.4-alpha |
| `ProviderRegistry` | `agent_workbench/runtime/provider_registry.py` | v6.9.6-foundation |
| `MetadataDefinition` | `agent_workbench/metadata/model.py` | v6.11.0-beta.4 |
| `MetadataAdapter` | `agent_workbench/metadata/adapter.py` | v6.11.0-beta.4 |

## 14 RuntimeModules (all frozen)

`runtime / agent / model / prompt / tool / skill / mcp / memory / session / profile / trace / workflow / strategy / config`

## Irreversible Dependency Direction

```
Agent → Skill → Capability → Engine → Provider → Tool
```

- Capability 不知道 Skill 的存在
- Engine 不知道 Agent 的存在
- Runtime 不知道 UI 的存在
- UI Shell 不知道 Runtime 的存在

## Validation Status (ADR-008 v2.0)

| Loop | Status | Evidence |
|------|--------|----------|
| 2.1 Runtime Identity | PASS | ADR-008.3 |
| 2.2 Event Flow | PASS | 008.1, 008.2.2, 008.2.3 |
| 2.3 Provider Boundary | STRUCTURAL CHECK ONLY | 008.4.5 |
| 2.4 Data Flow | PASS | 008.4.1-4 (Phase 2-D.3) |

## Position

Workbench v6 Runtime is **Android Framework**. Application / UI Shell is **System UI**.

Runtime is platform. Workbench is first validating product.