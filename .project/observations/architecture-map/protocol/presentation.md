# Presentation Contract

> **Layer**: 1.5 — Protocol Contracts
> **Type**: 3-layer presentation structure
> **Source**: Architecture Constitution v6.13 P3

---

## 3-Layer Structure

```
Runtime
   │
   │ metadata() / InteractionEvent
   ▼
Presentation Protocol     ← 能力契约 (defines "what can be done")
   │
   ▼
Presentation ViewModel    ← 数据结构 (carries "what it is")
   │
   ▼
Presentation Adapter      ← 翻译逻辑 (Runtime → ViewModel)
   │
   ▼
UI Shell                  ← consumes ViewModel, emits signals
```

## Directory Structure

```
agent_workbench/presentation/
├── protocols/              # 能力契约 (Protocol)
│   ├── foundation/        # Layer 1.5 Protocol (CIP/CAP/Event/Request)
│   │   ├── data.py
│   │   ├── event.py
│   │   ├── gateway.py
│   │   └── runtime.py
│   └── interaction/       # Layer 1.5 UI-facing Protocol
│       ├── command.py
│       ├── event.py
│       └── renderer.py
├── view_models/            # 数据结构 (dataclass)
│   ├── agent.py
│   ├── conversation.py
│   ├── capability.py
│   ├── session.py
│   ├── message.py
│   ├── memory.py
│   ├── settings.py
│   └── tab.py
├── adapters/               # 翻译逻辑
│   ├── agent_adapter.py
│   ├── conversation_adapter.py
│   ├── capability_adapter.py
│   ├── session_adapter.py
│   ├── message_adapter.py
│   ├── memory_adapter.py
│   └── settings_adapter.py
├── renderers/              # UI Shell implementations
│   ├── cli_renderer.py
│   ├── multi_renderer_proof.py
│   └── v6_ui/
│       ├── event_renderer.py
│       ├── renderer.py
│       └── shell_adapter.py
├── shell/                  # Shell framework
│   ├── transformers/
│   ├── integration.py
│   └── protocol.py
├── runtime.py              # Presentation Runtime (event dispatch)
└── view_models/
```

## Key Constraints (Constitution P3.4)

1. **Protocol defines capability, ViewModel carries data.** Two cannot be merged.
2. **UI Shell consumes Protocol + ViewModel only.** No Runtime imports.
3. **Adapter is the single translation point.** Runtime → ViewModel conversion ONLY in Adapter.
4. **Presentation Layer does not know UI implementation.** Same ViewModel can be consumed by Qt / Web / CLI.

## Position in 5-Layer Model

```
Layer 0 Runtime (metadata() / InteractionEvent source)
    ↓
Layer 1.5 Protocol (Presentation Protocol + ViewModel + Adapter)    ← THIS
    ↓
Layer 4 Application (UI Shell consumes ViewModel)
```

## Foundation Contract v0.5 Status

| Symbol | Tier | Status |
|--------|------|--------|
| `PresentationProtocol` | Tier B (structural) | Candidate |
| `ViewModel` dataclasses | Tier A (validated) | Workbench-validated |
| `Adapter` pattern | Tier A (validated) | Workbench-validated |
| `Renderer` Protocol | Tier A (validated) | Workbench-validated |

Per [ADR-009 Foundation Contract Promotion Proposal](../../decisions/ADR-009-foundation-contract-promotion-proposal.md).