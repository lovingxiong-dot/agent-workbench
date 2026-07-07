---
generated: 2026-07-07T14:45:00+08:00
agent: Kimi-K2.7-Code
schema_version: 3.1

## Mission
完成 V6 Step 4：建立八大 Engine Runtime 骨架（BaseEngine + LLM/Tool/Memory/Planner/Workflow/Code/Vision/Knowledge），验证 EngineManager 动态发现、统一生命周期、Runtime Trace Timeline 与 Planner 编排能力；随后从 `v5-dev` 切出干净的 V6 主线，并以 `v6.0.0-alpha` 作为 V6 独立 Runtime 架构线的公开立项标签。

## Progress
- [x] Step 3 已归档：`v6/runtime/engine_state.py` 定义 `EngineState`；`v6/runtime/engines/protocol.py` 定义 `Engine` Protocol、`EngineDescriptor`、`EngineNotReadyError`；`EngineManager` 支持完整生命周期；标签 `v6.5.7-alpha`。
- [x] 新增 `v6/runtime/engines/base.py`：`BaseEngine` 抽象基类，内置统一 `EngineState` 状态机与默认生命周期。
- [x] 新增八大 Engine 空壳：
  - `llm.py` — LLM Engine
  - `tool.py` — Tool Engine
  - `memory.py` — Memory Engine
  - `planner.py` — Planner Engine（注入 `EngineManager`，编排 LLM/Tool）
  - `workflow.py` — Workflow Engine
  - `code.py` — Code Engine
  - `vision.py` — Vision Engine
  - `knowledge.py` — Knowledge Engine
- [x] 所有 Engine 统一接口：`load()` / `initialize(ctx)` / `health_check()` / `execute(ctx)` / `shutdown()`；`execute(ctx)` 返回 `RuntimeResult(status="placeholder")`。
- [x] 清理旧 Engine 实现（Context/Prompt/Inference/Metrics/Phase/Policy）及不兼容测试 `tests/v6/test_v6_engines.py`。
- [x] 新增 `tests/v6/test_v6_runtime_kernel.py` 验证：EngineManager 动态发现、生命周期一致性、Trace 记录、Planner 编排 LLM/Tool。
- [x] V6 全量测试 `pytest tests/v6/` **130/130 通过**。
- [x] 在 `v5-dev` 提交并推送标签 `v6.5.8-alpha`（内部迁移标签）。
- [x] 从 `v6.5.8-alpha` 切出干净分支 `v6-dev` 并推送。
- [x] 更新 `README.md` 与 `PROJECT_BLUEPRINT.md`，添加「V6 全新主线声明」，明确 `v6-dev` 为唯一活跃分支，`v5-dev` 已冻结归档。
- [x] 在 V6 主线上新增公开立项标签 `v6.0.0-alpha`，声明 **V6.0.0-alpha marks the beginning of the independent V6 Runtime architecture line.**
- [x] `v6.5.8-alpha` 保留为内部迁移标签，仅作历史追溯；`v6.0.0-alpha` 作为 V6 产品线对外起点。

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

## Key Files
- `v6/runtime/engines/base.py` — `BaseEngine` 统一生命周期与占位结果。
- `v6/runtime/engines/{llm,tool,memory,planner,workflow,code,vision,knowledge}.py` — 八大 Engine 空壳。
- `v6/runtime/engines/__init__.py` — 统一导出八大 Engine。
- `v6/runtime/engine_manager.py` — Engine 注册、生命周期、执行入口与 Trace 自动记录。
- `v6/runtime/engine_state.py` — `EngineState` 枚举（CREATED → ... → STOPPED）。
- `v6/runtime/engines/protocol.py` — `Engine` Protocol、`EngineDescriptor`、`EngineNotReadyError`。
- `tests/v6/test_v6_runtime_kernel.py` — Runtime Kernel 集成测试（发现 / 生命周期 / Trace / Planner 编排）。
- `tests/v6/test_v6_engine_manager.py` — EngineManager 生命周期测试。
- `tests/v6/test_engine_protocol.py` — Engine Protocol、Descriptor、异常测试。
- `README.md` / `PROJECT_BLUEPRINT.md` — V6 主线声明与项目状态。
- `docs/v6/SPEC.md` — V6 架构 SPEC（Runtime Interface Principle、Adapter Boundary 等）。

## Error Log
No error.

## Environment Snapshot
- branch: v6-dev
- python: Python 3.14.6
- venv: none
- last_commit: 2496313 docs: V6 全新主线声明，README 与 PROJECT_BLUEPRINT 同步 v6-dev 分支 [test:130/130] [hint:v6,mainline,branch,declaration] (by AI-Kimi-K2.7-Code)

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
1. **Step 5 优先建立 Runtime Event Bus**：让 Engine、Service、Adapter 之间通过事件总线异步通信，减少直接调用耦合。
2. **Engine Capability Registry**：让 EngineManager 能按能力（capabilities）发现和调度 Engine，而非只按名称。
3. **Runtime Trace Replay**：扩展 `ReplayPlayer`，支持按 `Task → Phase → Engine → Service → Tool` 全链路重放。
4. **Memory / Prompt 本地私有化预留**：在 `RuntimeContext` 中预留 `agent_id` / `workspace` 等字段；MemoryEngine / PromptEngine 保持接口，底层先用 SQLite / 本地文件，未来通过 Backend 协议切换。
5. **暂不实现八大 Engine 真实业务逻辑**：LLM/Tool/Memory 等功能开发应在 Event Bus + Capability Registry + Replay 基础稳固后再进行。

## Test Status
- latest: [test:130/130]
- command: `python -m pytest tests/v6/ -q --tb=short`

## Notes
- `v6-dev` 已推送至 origin；当前 HEAD 同时承载公开立项标签 `v6.0.0-alpha`，作为 V6 独立产品线的对外起点。
- `v6.5.8-alpha` 保留为内部迁移标签，指向 `v5-dev` 上的 `76c7871`；它记录 Step 4 在旧线上的最终成果，但不参与 V6 产品线后续演进。
- `v5-dev` 已冻结，其最后一个 V6 相关提交为 `76c7871`。
- 后续所有 V6 版本号（如 `v6.5.9-alpha`、`v6.6.0-alpha`）应在 V6 主线上打标签并推送。
