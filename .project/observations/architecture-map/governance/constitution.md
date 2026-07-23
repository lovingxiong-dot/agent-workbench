# Architecture Constitution (v6.13-frozen)

> **Layer**: 1 — Architecture Governance
> **Status**: Frozen (2026-07-21)
> **Priority**: Highest (above CHANGELOG, above Spec, above Task List)

---

## Source

[Architecture Constitution v6.13](../../../../agent_workbench/docs/v6/architecture-constitution-v6.13.md)

## 5 Principles

### Principle 1: Workbench OS Identity

Workbench OS is an AI Agent OS. Desktop UI (PySide6) is the **first reference Shell**, not product essence.

### Principle 2: Runtime Kernel Freeze

Runtime Kernel is frozen. UI needs cannot cause Runtime changes.

### Principle 3: Presentation Contract

Presentation Layer has 3-layer structure:
- Protocol (capability contract)
- ViewModel (data structure)
- Adapter (translation logic)

### Principle 4: UI Shell Boundary

UI Shell is visual shell. No business logic. No Runtime imports. Only consumes Presentation Contract.

### Principle 5: Configuration-Driven Workbench

All extensions (Provider / Model / MCP / Skill / Tool / Workflow / Prompt / Memory) supported via UI registration, no source modification.

## Layer Architecture (Constitution Defined)

```
Workbench OS
├── Runtime Kernel       (Frozen)
├── Core Foundation      (Frozen: Agent/Capability/Event/Registry/Lifecycle)
├── Presentation Layer   (Protocol + ViewModel + Adapter)
├── UI Shell             (Replaceable: qt / web / mobile / cli)
└── Adapter Ecosystem    (Runtime → UI translation)
```

## Refined 5-Layer Architecture Model (Insight from OD-EX0-003)

```
                  Governance
                       |
        +--------------+--------------+
        |              |              |
   Layer 0         Layer 1        Layer 1.5
   Foundation    Architecture    Protocol Contracts
   Runtime       Governance     (CIP/CAP/Event/Request)
        |              |              |
        +--------------+--------------+
                       |
                  Layer 2
              Agent Behavior Contract
                       |
                       v
                  Layer 3
            Runtime Execution Workflow
                       |
                       v
                  Layer 4
            Applications / Renderers
```

**Layer 1.5 Addition**: Protocol Contracts explicitly separated from Agent Behavior (per OD-EX0-003).

## Dependency Direction (Irreversible)

```
Agent → Skill → Capability → Engine → Provider → Tool
```

## Enforcement

- Violating code MUST NOT be merged.
- Violating Architecture Decision is invalid.