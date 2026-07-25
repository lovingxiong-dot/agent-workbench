# Changelog

> **Repository Narrative Migration 2026-07-25** — Version numbers (e.g. v6.18) do **not** equal Milestone numbers (e.g. Phase 3.11). They are independent dimensions.
>
> **Tag ordering note**: Version numbers reflect commit order and may not match architectural phase order. Phase 3.10 (Presentation) is `v6.17.0-alpha`; Phase 3.11 (Runtime Kernel) is `v6.16.0-alpha`. This is intentional to keep stable line on `main` (`v6.12.0-beta.15`) untouched.

## v6.20.0-alpha (2026-07-25) — Phase 3.13 Presentation & Consumption Complete

> **Milestone**: Phase 3.13 Presentation & Consumption Complete. First platform-agnostic Presentation Contract.
> - Frozen `ObservationViewModel` (10 fields, schema "presentation.v0.1")
> - Pure function Adapter: `ObservationArtifact → ObservationViewModel`
> - Read-only Consumer: `produce()` / `produce_json()`
> - 100/100 Presentation tests PASS, 100/100 Runtime tests unchanged
> - Strict NOT in scope: UI / Renderer / Storage / Memory / EventBus new channel / AI Summary
> - Coexistence: prototype (view_models/, adapters/) preserved
> - Next: Phase 3.14 Insight Understanding

### Added

- `tools/presentation/contract/observation_view_model.py` (Frozen, 10 fields: id/title/summary/category/severity/timestamp/source/metrics/metadata/schema_version)
- `tools/presentation/adapter/observation_presentation_adapter.py` (pure function: ObservationArtifact → ObservationViewModel)
- `tools/presentation/consumer/observation_consumer.py` (read-only: produce() / produce_json())

### Architecture (ADR)

- **ADR-017**: Observation Presentation Boundary (Frozen Phase 3.13)

### Tests

- 100/100 Presentation tests PASS (34 Contract + 28 Adapter + 16 Consumer + 22 Integration)
- 100/100 Runtime tests unchanged (Phase 3.11 B/C/D)

### Success Criteria (verified)

- ✅ Runtime 不知道 Presentation 存在 (no v6.runtime import in NEW subdirs)
- ✅ Presentation 不知道 UI 平台 (no PySide/PyQt/QML/react/vue)
- ✅ Consumer 只读 (no mutation)
- ✅ Contract 可冻结 (frozen dataclass)
- ✅ 下一阶段 Insight / Memory 不被污染

---

## v6.19.0-alpha (2026-07-25) — Phase 3.12 Observation Layer Complete

> **Milestone**: Phase 3.12 Observation Layer Complete. First Cognitive Layer Frozen.
> - Contract Schema (ADR-016) Frozen at `observation.v0.1`
> - Read-only RuntimeEvent Consumer
> - Minimal in-memory Registry (3 methods only)
> - 88/88 Observation tests PASS, 100/100 Runtime tests unchanged
> - Coexistence: prototype (reports/collectors/adapters/derived) preserved
> - Next: Phase 3.13 Presentation & Consumption

### Added

- `tools/observation/contract/observation_artifact.py` (Frozen, 10 fields, schema_version = "observation.v0.1")
- `tools/observation/consumer/runtime_event_consumer.py` (read-only Adapter, 5→3 type mapping, pure function)
- `tools/observation/registry/observation_registry.py` (minimal in-memory, 3 methods: register / query_by_id / query_by_execution_id)
- `.project/PROJECT_CONTEXT.md` (Execution Context Snapshot, <200 lines)

### Architecture (ADR)

- **ADR-016**: Observation Layer Contract (Frozen Phase 3.12)

### Tests

- 88/88 Observation tests PASS (38 Contract + 29 Consumer + 19 Registry + 2 __init__)
- 100/100 Runtime tests unchanged (Phase 3.11 B/C/D)

### Principle

> **Observation records what happened. Memory remembers what matters.**
> 两者不要提前合并。Memory features (persistence, schema registry, governance) are Phase 3.16+ scope.

---

## v6.18.0-alpha (2026-07-25) — Phase 3.11 Finalization HEAD

> **Milestone**: Phase 3.11 Runtime Finalization Complete (post-Phase 3.11 Runtime Frozen `v6.16.0-alpha`).
> - 8 Runtime components frozen at `v6.16.0-alpha`
> - 372 tests PASS
> - Runtime Boundary Audit (8/8 A, 0 B)
> - Handoff document generated
> - Artifact Sync: PROJECT_BLUEPRINT / PROJECT_LINEAGE / PROJECT_STATE / Handoff all synchronized
> - Repository Authority Audit completed: 5 source documents migrated to `v6-agent` (single active development branch)
> - Next: Phase 3.12 Observation Layer Implementation (after Phase 3.12-3.15 Asset Sync)

### Added

- `v6/runtime/orchestrator.py`: Phase 3.11-D v0.3 — Parent-Child Execution (`submit_child()`) + Top-down DFS Cancellation (`cancel()`) + Deadline model (`DEADLINE_EXCEEDED`)

> **里程碑语义**：Phase 3.11 Execution Kernel Evolution Complete。Runtime Foundation + Execution Kernel Frozen。
> - Runtime Foundation (`v6.9.6-foundation`) + Execution Kernel Evolution (`v6.16.0-alpha`) 同时冻结
> - Runtime Kernel 不再扩展（仅 bug fix / contract compatibility）
> - 下一阶段：Phase 3 Consolidation 收口 + Phase 3.12 Observation Layer

### Added

- `v6/runtime/orchestrator.py`: Phase 3.11-D v0.3 — Parent-Child Execution (`submit_child()`) + Top-down DFS Cancellation (`cancel()`) + Deadline model (`DEADLINE_EXCEEDED`)
- `v6/runtime/event_bus.py`: `TASK_CANCELLED` RuntimeEvent + 异步 loop bug fix (Phase 3.10+)
- `v6/runtime/context.py`: 双状态模型 (`lifecycle: LifecycleState` + `activity: ActivityState`) + `attach_execution()` 统一绑定入口
- `v6/runtime/enums.py`: `LifecycleState` (CREATED/QUEUED/PLANNING/EXECUTING/...) + `ActivityState` (IDLE/RUNNING/STREAMING/WAITING) 双状态枚举
- `v6/runtime/cancellation_propagation.py` (NEW): `CancellationPropagationContext` (frozen + invariants) + `PropagationType` + `CancellationPropagationLimitExceeded`
- `v6/runtime/execution_control.py` (NEW): `ExecutionControl` (聚合 CancellationToken 等控制令牌) + `TaskCancelledError`
- `v6/runtime/execution_metadata.py` (NEW): `ExecutionMetadata` (frozen)
- `v6/runtime/execution_registry.py` (NEW): `ExecutionRegistry` (topology owner)

### Architecture (ADR Frozen)

- **ADR-013**: Runtime Lifecycle Event Extension (TASK_CANCELLED event)
- **ADR-014**: Cancellation Precedence Rule (ExecutionControl 聚合)
- **ADR-015**: Parent-Child Execution Propagation v0.3 (ExecutionRegistry + CancellationPropagation + Deadline)

### Tests

- `tests/v6/runtime/test_phase3_11_b_lifecycle.py`: Lifecycle state machine (98 tests total)
- `tests/v6/runtime/test_phase3_11_c_cancellation.py`: Cancellation precedence + propagation
- `tests/v6/runtime/test_phase3_11_d_parent_child.py`: Parent-child submit_child + DFS cancel

### Runtime Boundary Audit (Batch 0)

> 8/8 modifications classified as **Category A** (Phase 3.11 Execution Kernel Evolution). 0 Category B (Cognitive Layer Leakage). Frozen Boundary verified.

### Runtime Freeze Certificate (`v6.16.0-alpha`)

After this tag, `v6/runtime/` is **frozen with explicit boundaries**:

**Allowed**:
- ✓ Bug Fix
- ✓ Frozen Contract compatibility

**Forbidden**:
- ✗ Memory / Knowledge / Identity
- ✗ Agent Role / Harness Logic
- ✗ New Runtime concepts or control flows
- ✗ New responsibilities for existing Runtime modules

### Tag Migration Note

> **Important**: v6.16.0-alpha was previously declared in narrative for Phase 3.9 Presentation Contract. After Phase 3.11 Finalization Batch (2026-07-25), this tag has been **migrated** to point to the Phase 3.11 Runtime commit. v6.18.0-alpha replaces the previous v6.16.0-alpha (Phase 3.9) tag position. v6.17.0-alpha (Phase 3.10 Presentation) is unchanged.

---

## v6.17.0-alpha (2026-07-25) — Phase 3.10 Runtime Presentation Integration

> **里程碑语义**：Phase 3.10 Runtime Presentation Integration Complete。Workbench 已从"UI 外壳"正式成为 Runtime Client。
> - 修复 EventBus Dispatch Loop 被同步 Task Execution 阻塞的 Blocking Callback Problem
> - 建立第一条完整 RuntimeRequest → Decision → Task → Engine → RuntimeEvent → Presentation 黄金链路
> - 新增 TracePresentationModel（Model only，不做 UI）
> - 5 个 Frozen Contract 零修改（RuntimeRequest / RuntimeEvent / InteractionEvent / Presentation Contract / Renderer Protocol）
> - 全量回归 94/94 PASS（Phase 3.8 + 3.9 + 3.10）

### Fixed

- `v6/runtime/orchestrator.py`: `_on_task_started()` 改用 `threading.Thread` 异步执行 `_execute_task()`，分离事件通知与任务执行。EventBus 恢复纯通知职责。
- `v6/runtime/event_bus.py`:
  - `_dispatch()`: 支持通配符 `"*"` 订阅，InteractionLayer 等全局监听者能收到所有事件
  - `_run_loop()`: 修复 `stop()` 与 `finally` 块的竞态条件（本地 loop 引用）
  - `_dispatch_loop()`: 捕获 `_dispatch` 异常，防止单个回调崩溃导致事件循环退出

### Added

- `v6/presentation/models.py`: `TracePresentationModel` dataclass，包含 `trace_id/parent_id/task_id/phase/source/event_type/payload_summary/timestamp` 字段，`from_runtime_event()` 工厂方法，`is_task_boundary/is_engine_event/is_stream_event` 属性
- `tests/v6/presentation/test_phase3_10_runtime_integration.py`: 41 个测试覆盖 4 个子任务（Event Source Binding / Agent Task Golden Path / Trace Presentation Model / Freeze Validation）
- `.project/decisions/ADR-012-runtime-execution-isolation.md`: 记录从 `threading.Thread` 到 `TaskScheduler` + `ExecutionPool` 的长期演进策略（PROPOSAL，不实现）

### Architecture Decisions

- **EventBus 职责分离**：EventBus = Notification only，Task Execution 由独立线程执行
- **Thread 方案作为 Phase 3.10 最小修复**：在 Single Runtime Process 阶段合理，未来演进至 TaskScheduler + ExecutionPool（见 ADR-012）
- **TracePresentationModel 仅 Model**：不做 UI 实现，不修改 RuntimeTrace，不依赖 Qt

---

## v6.16.0-alpha (2026-07-24) — Phase 3.9 Presentation Contract Stabilization

> **里程碑语义**：Phase 3.9 Presentation Contract Stabilization Complete。
> - Presentation Contract Frozen（Model/Renderer/Adapter 三层契约冻结）
> - Presentation Runtime Boundary Verified（Golden Path 验证 InteractionEvent → PresentationModel → UI 链路）
> - Renderer Backend Migration Deferred to Phase 4（QtRendererBase 接口就绪，迁移延后）
> - Golden Path validated at Interaction Boundary level（非 Real Runtime Task Execution）

### Added

- `v6/presentation/contracts/` 三层契约添加 `FROZEN_VERSION = "v6.14-phase3.9"` 冻结标记：
  - `model_contract.py`: `BasePresentationModel` 冻结字段 model_id/timestamp/metadata/model_type
  - `renderer_contract.py`: `Renderer` 冻结方法 initialize/render/dispose/supported_models
  - `adapter_contract.py`: `Adapter` 冻结方法 set_callback/reset；`EventAdapterContract`: render；`StateAdapterContract`: adapt
- `v6/presentation/renderers/qt_renderer_base.py`: `QtRendererBase` 抽象基类，实现 `Renderer` ABC，为 Qt 平台 Renderer 提供统一生命周期管理（Phase 4 迁移现有函数式 Renderer）
- `v6/presentation/golden_path_demo.py`: `GoldenPathDemo` 完整验证链路，产出 InteractionEvent → EventAdapter → PresentationModel → RendererRegistry → ChatScene（非 fake Model）
- `tests/v6/presentation/test_phase3_9_contracts.py`: 17 个契约验证测试（Model/Renderer/Adapter/Integrity）
- `tests/v6/presentation/test_phase3_9_golden_path.py`: 14 个 Golden Path 验证测试（Analysis/Streaming/ToolChain/Error 流程）

### Changed

- `v6/ui/chat_area.py`: `__main__` 块替换为 GoldenPathDemo（替代 DemoProvider）
- `v6/presentation/__init__.py`: 导出 `GoldenPathDemo`、`QtRendererBase`
- `v6/presentation/renderers/__init__.py`: 导出 `QtRendererBase`

### Architecture Debt

- **DEBT-004**: Renderer 直接依赖 chat_items（Phase 4 迁移到 `QtRendererBase` 子类）
- **DEBT-005**: Legacy design_tokens compatibility layer（`design_tokens.py` 与 `design/` 包并行存在，Phase 4 移除兼容层）
- **DEBT-006**: `MessageViewModel` 未继承 `BasePresentationModel`（Phase 4 统一迁移）

---

## v6.15.0-alpha (2026-07-24) — Product Shell Integration Milestone

> **里程碑语义**：Phase 2-D Product Shell Integration 完成。CLI 与 GUI 共享统一 WorkbenchController，建立 Preflight Check Provider 就绪检查系统，CLI 命令系统完整覆盖。所有 Frozen Contract 边界保持，v6-core 零回归。

### Added

- `WorkbenchController.get_agent_name()`：返回工作台名称（替代直接访问 `runtime.config`）。
- `WorkbenchController.get_session_info()`：返回 Session 摘要信息（替代直接访问 `module_registry`）。
- `WorkbenchController.get_status()`：返回 Runtime 综合状态摘要（Agent/Provider/Model/Session/Modules/Agents）。
- `WorkbenchController.get_config_summary()`：返回当前配置摘要（Temperature/MaxTokens/MaxHistory）。
- `WorkbenchController.preflight_check()`：Provider 就绪检查系统，验证凭证、Provider 可用性、模型可用性。失败不产生 Task 失败，只返回结构化状态。
- CLI 命令：`/status`、`/config`、`/providers`。
- `tests/v6_10/test_product_shell_integration.py`：17 个集成测试，覆盖 Gate 2 (Runtime Path)、Gate 3 (Multi Shell)、Gate 4 (Boundary Integrity)、Preflight Check、CLI DataSource。
- `.project/decisions/ADR-010-package-action-execution-boundary.md`：记录 `execute_agent_action()` 绕过 Runtime 的已知架构债务。
- `.project/decisions/ADR-011-controller-api-surface-freeze.md`：定义 `WorkbenchController` 公共 API 面冻结规则。
- `docs/v6/product-shell-phase-report.md`：Phase 2-D Product Shell Integration Final Report。

### Changed

- `agent_workbench/app.py`：`run_cli()` 重构，移除直接 Runtime 访问（`runtime.config`、`runtime.module_registry`），改用 Controller 公共 API。启动时执行 Preflight Check，凭证缺失输出友好提示。
- `agent_workbench/app.py`：`_handle_cli_command()` 新增 `/status`、`/config`、`/providers` 命令。
- `tests/test_controller_interaction.py`：`test_controller_chat_routes_general_query_to_chat_capability` 添加 `pytest.mark.skipif`（openai 包未安装时跳过），标记为环境依赖问题。

### Fixed

- 标记 openai dependency test environment issue：`pytest.mark.skipif` 跳过需要 openai 包的测试，明确属于环境依赖问题，非代码缺陷。

---

## v6.14.0-alpha (2026-07-20) — Dogfooding Phase: D5 Agent Selector

> **里程碑语义**：D5 完成 Agent 选择器。支持在 CLI 中通过 `/agent` 命令切换 Agent Identity（Personal/Coding/Research），每个 Agent 有独立的 system_prompt、provider、model 配置。

### Added

- `packages/personal_agent/manifest.yaml`：个人助手 Agent 包。
- `packages/coding_agent/manifest.yaml`：编程助手 Agent 包。
- `packages/research_agent/manifest.yaml`：研究助手 Agent 包。
- `agent_workbench/runtime/modules/agent_module.py`：Agent Identity 模块（AgentModule），扫描 packages/ 目录发现 Agent 包，管理 Active Agent 选择和切换。
- `AgentIdentity` 数据类：封装 Agent 的 id/name/system_prompt/provider/model。
- `WorkbenchController.switch_agent()` / `list_agents()` / `get_active_agent()` / `get_active_agent_name()` / `get_system_prompt()`：Controller 级别 Agent 管理 API。
- `tests/v6/test_v6_agent.py`：10 个 AgentModule 测试，覆盖发现、切换、System Prompt、失败场景。
- CLI 命令：`/agent <id>` 切换 Agent，`/agents` 查看列表，`/model` 切换模型，`/provider` 切换 Provider。
