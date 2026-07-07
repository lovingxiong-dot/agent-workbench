---
generated: 2026-07-07T14:45:00+08:00
agent: Kimi-K2.7-Code
schema_version: 3.1

## Current Development Authority

> **The active development line is `v6-dev` at version `v6.6.2-alpha`.**
> **Public baseline: `v6.0.0-alpha`.**

| Item | Value |
|---|---|
| Active branch | `v6-dev` |
| Current development version | `v6.6.2-alpha` |
| Public baseline | `v6.0.0-alpha` |
| Internal migration checkpoint | `v6.5.8-alpha` (historical, on `v5-dev`) |
| Frozen archive | `v5-dev` |
| AI rule | Do not modify `v5-dev`. All new work goes to `v6-dev`. |

See [`PROJECT_LINEAGE.md`](../PROJECT_LINEAGE.md) for the full V5 / V6 identity map.

## Mission
完成 V6 Step 5.3：建立 Runtime Execution Replay Foundation。新增 `ReplayRecord` / `ReplayLog` / `ReplayService`，让 Runtime 执行轨迹可记录、可导出、可查看；明确第一版只做 Deterministic Trace Replay，不重新执行 LLM/Tool/Memory。

## Current Architecture State

### Runtime Communication Layer
**READY** — `v6/runtime/event_bus.py` 已升级为 Runtime Event Bus。

### Capability Discovery Layer
**READY** — `v6/runtime/capability_registry.py` 已落地。

### Runtime Replay Layer
**READY** — `v6/runtime/replay.py` 已落地（Deterministic Trace Replay Foundation）。

### Event Flow
```
Engine
  |
  v
RuntimeEventBus
  |
  +------> RuntimeTrace (via Trace Hook)
  |
  +------> ReplayService
  |
  +------> Subscribers
```

### Capability Flow
```
Caller Requirement
  |
  v
CapabilityQuery
  |
  v
CapabilityRegistry
  |
  +------> EngineMatch[] (sorted)
  |
  +------> selected engine name
  |
  v
EngineManager.execute(name, ctx)
```

### Guarantees
- Engine 不直接访问 `RuntimeTrace`；生命周期事件通过 `RuntimeEventBus` 路由。
- Engine 间通信使用标准 `RuntimeEvent`，禁止直接互相调用。
- `EngineManager` 负责 Engine 生命周期；`EventBus` 负责运行时通信；`CapabilityRegistry` 负责 Engine 选择；`ReplayService` 负责执行轨迹记录与回放基础；四者职责分离。
- `ReplayService` 不是 Engine，不替代 `EngineManager` 或 `EventBus`。
- 调用者不再硬编码 Engine 名称，而是描述能力需求。
- 第一版 Replay 只做轨迹记录、导出、查看，不重新执行 LLM/Tool/Memory。

## Progress
- [x] Step 3 已归档：`v6/runtime/engine_state.py` 定义 `EngineState`；`v6/runtime/engines/protocol.py` 定义 `Engine` Protocol、`EngineDescriptor`、`EngineNotReadyError`；`EngineManager` 支持完整生命周期；标签 `v6.5.7-alpha`。
- [x] Step 4 已归档：新增 `BaseEngine` 与八大 Engine 空壳（LLM/Tool/Memory/Planner/Workflow/Code/Vision/Knowledge），Runtime Kernel 集成测试通过；标签 `v6.5.8-alpha`（内部迁移）。
- [x] V6 独立产品线立项：新增 `PROJECT_LINEAGE.md` 与 `Current Development Authority` 认知层；标签 `v6.0.0-alpha`（公开 baseline）；当前开发版本 `v6.6.0-alpha`。
- [x] Step 5.1 已归档：`v6/runtime/event_bus.py` 升级为 Runtime Event Bus Foundation；标签 `v6.6.0-alpha`。
- [x] Step 5.2 已归档：新增 `CapabilityRegistry`，八大 Engine 声明 capabilities；`EngineManager` 支持按能力选择；标签 `v6.6.1-alpha`。
- [x] Step 5.3 完成：新增 `ReplayRecord` / `ReplayLog` / `ReplayService`，Runtime Execution Replay Foundation 落地；标签 `v6.6.2-alpha`。
- [ ] Step 5.4 / V6.7：基于 Event Bus + Capability Registry + Replay 的自治 Agent 编排（待规划）。

## Step 5.3 Details
- [x] 新增 `v6/runtime/replay.py`：
  - `ReplayRecord`：trace_id / task_id / timestamp / component / component_type / event_type / input_snapshot / output_snapshot / metadata。
  - `ReplayLog`：线程安全的 ReplayRecord 容器，支持 filter / timeline / export。
  - `ReplayService`：订阅 EventBus 事件生成 ReplayRecord；支持从 `RuntimeTrace` 批量导入。
- [x] `ReplayService` 作为 EventBus 订阅者接入事件流，不直接耦合 Engine。
- [x] 明确 `ReplayRecord` 与 `TraceStep` 职责分离：
  - TraceStep = 发生了什么。
  - ReplayRecord = 如何重新发生（含 input/output snapshot）。
- [x] 明确第一版只做 Deterministic Trace Replay：记录、导出、查看；不重新执行 LLM/Tool/Memory。
- [x] 新增 `tests/v6/test_v6_replay.py` 共 9 个测试。
- [x] V6 全量测试 `pytest tests/v6/` **159/159 通过**。

## Blocker
无。

## Decision Log
1. **决策**：Step 4 只做 Engine Runtime 骨架（空壳），不接入 OpenAI / Gemini / LangChain / MCP / 向量库 / 浏览器等具体实现。
   - 排除：直接实现八大 Engine 业务逻辑——会提前绑定外部依赖，且 Runtime Kernel 本身的发现、生命周期、Trace 链路尚未充分验证。
   - 状态：已执行。

2. **决策**：`BaseEngine` 提供默认生命周期与 `_placeholder_result()`，子类只需设置 `name` 即可参与 Runtime 验证。
   - 排除：每个 Engine 都手写完整状态机——重复代码多，且 Step 4 重点是验证 Runtime 骨架而非业务差异。
   - 状态：已执行。

3. **决策**：`PlannerEngine` 通过构造函数注入 `EngineManager`，不通过 `RuntimeContext` 反向依赖 Runtime。
   - 排除：在 `RuntimeContext` 中携带 `EngineManager` 引用——会破坏 Context 作为纯 Facts Container 的边界。
   - 状态：已执行。

4. **决策**：从 `v5-dev` 切出 `v6-dev` 作为干净主线，并在文档中明确声明。
   - 排除：继续在 `v5-dev` 上打 `v6.x` 标签——会造成版本号、分支名、架构文档的严重混淆。
   - 状态：已执行。

5. **决策**：`health_check()` 暂时返回 `EngineState`，不升级为 `EngineHealth` 对象。
   - 排除：Step 4 引入 `EngineHealth`——当前没有真实 API 超时 / 降级场景，升级时机不成熟。
   - 状态：搁置，待 Step 5/6 有真实 Engine 实现后再评估。

6. **决策**：新增独立的 `CapabilityRegistry`，不把它合并进 `EngineManager`。
   - 排除：直接在 `EngineManager` 中硬编码能力映射——会混淆"生命周期管理"与"能力选择"两个职责。
   - 状态：已执行。

7. **决策**：Capability Registry 只维护 `EngineDescriptor`，不持有 Engine 实例。
   - 排除：Registry 直接管理 Engine 实例——会造成与 EngineManager 的双生命周期管理。
   - 状态：已执行。

8. **决策**：Replay 以 `ReplayService` 形式作为 Runtime Infrastructure，不实现为 Engine。
   - 排除：把 Replay 做成 Engine——会混淆业务能力与 Runtime 基础设施。
   - 状态：已执行。

9. **决策**：Step 5.3 只做 Deterministic Trace Replay（记录 / 导出 / 查看），不做真正的重新执行。
   - 排除：立即实现 `replay(task)` 重新调用 LLM/Tool——会带来随机性、外部状态变化、Memory 漂移等不可控因素。
   - 状态：已执行；真正的 Replay Execution 待 checkpoint + snapshot + engine sandbox 成熟后再推进。

10. **决策**：`ReplayRecord` 与 `TraceStep` 保持独立模型。
   - 排除：直接复用 `TraceStep` 作为 Replay 数据——Trace 关注"发生了什么"，Replay 关注"如何重新发生"，字段诉求不同。
   - 状态：已执行。

## Key Files
- `v6/runtime/replay.py` — Runtime Execution Replay Foundation（ReplayRecord / ReplayLog / ReplayService）。
- `v6/runtime/event_bus.py` — Runtime Event Bus（神经系统）。
- `v6/runtime/capability_registry.py` — Engine 能力注册表（Capability Discovery）。
- `v6/runtime/engine_manager.py` — Engine 生命周期管理 + Capability 选择桥接。
- `v6/runtime/engines/base.py` — `BaseEngine` 统一生命周期与占位结果。
- `v6/runtime/engines/{llm,tool,memory,planner,workflow,code,vision,knowledge}.py` — 八大 Engine 空壳。
- `v6/runtime/engines/__init__.py` — 统一导出八大 Engine。
- `v6/runtime/engine_state.py` — `EngineState` 枚举（CREATED → ... → STOPPED）。
- `v6/runtime/engines/protocol.py` — `Engine` Protocol、`EngineDescriptor`、`EngineNotReadyError`。
- `tests/v6/test_v6_runtime_kernel.py` — Runtime Kernel 集成测试（发现 / 生命周期 / Trace / Planner 编排）。
- `tests/v6/test_v6_engine_manager.py` — EngineManager 生命周期测试。
- `tests/v6/test_v6_capability_registry.py` — Capability Registry 测试。
- `tests/v6/test_v6_replay.py` — Replay Foundation 测试。
- `tests/v6/test_engine_protocol.py` — Engine Protocol、Descriptor、异常测试。
- `README.md` / `PROJECT_BLUEPRINT.md` — V6 主线声明与项目状态。
- `docs/v6/SPEC.md` — V6 架构 SPEC（Runtime Interface Principle、Adapter Boundary 等）。

## Error Log
No error.

## Environment Snapshot
- branch: v6-dev
- python: Python 3.14.6
- venv: none
- last_commit: ff39c74 feat(runtime): Step 5.2 Engine Capability Registry [test:150/150] [hint:v6,runtime,capability-registry,step5.2] (by AI-Kimi-K2.7-Code)

## Working State
### Dirty Files
working tree clean

### Uncommitted Changes Summary
no uncommitted changes

### Recent Conversation
- 用户确认 Step 4 目标：实现八大 Engine Runtime 骨架而非业务逻辑，验证 EngineManager 动态发现、生命周期一致性、Trace Timeline。
- 用户建议先存档 push，再移交；同时提出应在干净分支上开发 V6，避免在 `v5-dev` 上继续产生混淆。
- 已完成 `v6.5.8-alpha` 提交与标签推送，随后切出 `v6-dev` 并更新文档声明 V6 为唯一活跃主线。
- 用户进一步分析 Agent Runtime 中 Memory / Prompt 的本地私有化设计，建议 Step 5 不要立即接八大 Engine 功能，而是先做 Runtime Event Bus + Engine Capability Registry + Runtime Trace Replay。

## Next Steps (AI-Inferred)
1. **Step 5.4 / V6.7：自治 Agent 编排雏形**（当前最高优先级）
   - 基于 Event Bus + Capability Registry + Replay 三大基础，设计 Planner 的事件驱动编排流程。
   - 目标：Planner 不再硬编码 `manager.execute("llm")`，而是通过 Capability Query + EventBus 驱动多 Engine 协作。
2. **Runtime Task 模型完善**
   - 将 `RuntimeContext`、`RuntimeTrace`、`RuntimeMetrics`、`RuntimeResult` 进一步封装为 `RuntimeTask` 工厂产物，同时保持 Context 作为唯一 Public Protocol。
3. **Memory / Prompt 本地私有化预留**
   - 在 `RuntimeContext` 中预留 `agent_id` / `workspace` 等字段；MemoryEngine / PromptEngine 保持接口，底层先用 SQLite / 本地文件，未来通过 Backend 协议切换。
4. **暂不实现八大 Engine 真实业务逻辑**
   - LLM/Tool/Memory 等功能开发应在 Runtime 基础（Event Bus + Capability Registry + Replay + Task Model）稳固后再进行。
5. **未来：真正的 Replay Execution**
   - 待 checkpoint + snapshot + engine sandbox 成熟后，再推进 `replay(task)` 重新执行能力。

## Test Status
- latest: [test:159/159]
- command: `python -m pytest tests/v6/ -q --tb=short`

## Notes
- `v6-dev` 已推送至 origin；当前 HEAD 同时承载公开立项标签 `v6.0.0-alpha`，作为 V6 独立产品线的对外起点。
- `v6.5.8-alpha` 保留为内部迁移标签，指向 `v5-dev` 上的 `76c7871`；它记录 Step 4 在旧线上的最终成果，但不参与 V6 产品线后续演进。
- `v5-dev` 已冻结，其最后一个 V6 相关提交为 `76c7871`。
- 后续所有 V6 版本号（如 `v6.5.9-alpha`、`v6.6.0-alpha`）应在 V6 主线上打标签并推送。
