# Project State — Workbench v6

> **Current Development Snapshot** — Repository Governance v1.0
> **Last Updated**: 2026-07-22
> **Audience**: Contributors, AI agents, reviewers

---

## Product Identity

| Field | Value |
|-------|-------|
| Repository | `agent-workbench` (lovingxiong-dot/agent-workbench) |
| Active Product | **Workbench v6** — Agent Workspace |
| Future Product | Agent Manager OS — Governance Plane |
| Shared Ancestor | CENTRE / AOS — see [FOUNDATION.md](./FOUNDATION.md) |

---

## Version

| Field | Value |
|-------|-------|
| Current Version | `v6.14.0-alpha` |
| Stable Line | `main` (v6.12.0-beta.15) |
| Development Line | `v6-agent` |
| Framework Baseline | `v6.8.0-alpha` |
| Runtime Freeze | `v6.9.6-foundation` |

---

## Repository Status

| Indicator | Status |
|-----------|--------|
| Build | Passes |
| Tests | Passes |
| CLI Mode | `python -m agent_workbench.app --mode cli` |
| GUI Mode (Legacy) | `python -m agent_workbench.app --mode gui` |
| GUI Mode (v6/ui) | `python -m agent_workbench.app --mode gui-v6` |
| Multi Renderer Proof | Passes |

---

## Active Modules

| Module | Path | Status |
|--------|------|--------|
| Runtime Kernel | `agent_workbench/runtime/` | Active |
| Interaction Protocol | `agent_workbench/presentation/protocols/` | Active |
| Presentation Runtime | `agent_workbench/presentation/runtime.py` | Active |
| Renderer Registry | `agent_workbench/presentation/renderers/registry.py` | Active |
| v6/ui Foundation | `v6/ui/` (22 files) | Active |
| V6UIRenderer | `agent_workbench/presentation/renderers/v6_ui/` | Active |
| CLI Renderer | `agent_workbench/presentation/renderers/cli_renderer.py` | Active |
| Application Layer | `agent_workbench/application/` | Active |
| Agent Packages | `packages/` (3 agents) | Active |
| Provider Integrations | `agent_workbench/services/` (7 providers) | Active |

---

## Frozen Modules

| Module | Path | Freeze Point |
|--------|------|-------------|
| Runtime Kernel | `agent_workbench/runtime/` | v6.9.6-foundation |
| v6/ui Foundation | `v6/ui/` (22 files) | Phase 2-B.2 |
| Shell Contract | `agent_workbench/presentation/shell/protocol.py` | Phase 1-B |
| Interaction Protocol | `agent_workbench/presentation/protocols/` | Phase 2-C.1 |
| Legacy Workbench UI | `agent_workbench/ui/workbench/` (32 files) | Phase 2-D.1 (deprecated) |
| V5 Architecture | `_archive/v5/` | Frozen |
| Old Agent Engine | `_archive/agent_engine/` | Frozen |
| Old Core | `_archive/old_core/` | Frozen |

---

## Known TODO

| # | Item | Priority | Phase |
|---|------|----------|-------|
| 1 | InteractionCommand 集成到 WorkbenchInteractionLayer | Medium | 2-C.3 |
| 2 | `PresentationRuntime` 替换 `V6UIApplication` 中的 `PresentationPipeline` 直接调用 | Done | 2-D.1 |
| 3 | RendererProtocol 从 `registry.py` 提取到 `protocols/renderer.py` | Low | Cleanup |
| 4 | 旧 `WorkbenchUIController` 完全移除 | Low | Post 2-D |
| 5 | v6/ui 批量消息渲染性能优化 | Low | Post 2-D |

---

## Current Milestone

```
Phase 2-D: Renderer Migration
├── 2-D.0 Migration Audit           ✅
├── 2-D.1 Application Boundary      ✅
├── 2-D.2 Renderer Migration         ← Next
└── 2-D.3 Legacy Removal
```

---

## Last Architecture Decision

[ADR-003 Phase 2-D Migration Audit](.project/decisions/ADR-003-phase-2d-migration-audit.md)

**Decision**: Gate Check passed. Phase 2-D.1 can proceed. V6UIApplication must use PresentationRuntime + RendererRegistry before v6/ui Renderer Migration.

---

## Git Tags

| Tag | Phase | Description |
|-----|-------|-------------|
| `presentation-foundation-freeze` | 2-B.2 | Architecture Declaration Sync |
| `phase-2c-contract-freeze` | 2-C.0 | Presentation RFC frozen |
| `v6.13-freeze` | 2-B | Architecture Freeze |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [FOUNDATION.md](./FOUNDATION.md) | **Shared ancestor — CENTRE ecosystem** |
| [PROJECT_DECLARATION.md](./PROJECT_DECLARATION.md) | Workbench v6 Constitution |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture navigation |
| [AGENT_ENTRY.md](./AGENT_ENTRY.md) | Agent onboarding |
| [ROOT_INDEX.md](./ROOT_INDEX.md) | Repository navigation |
| [CHANGELOG.md](./CHANGELOG.md) | Version history |

---

## Version

| Version | Date | Change |
|---------|------|--------|
| v1.0 | 2026-07-22 | Initial snapshot. Repository Governance v1.0. |