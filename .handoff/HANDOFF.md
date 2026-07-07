---
generated: 2026-07-07T14:45:00+08:00
agent: Kimi-K2.7-Code
schema_version: 3.1

## Current Development Authority

> **The active development line is `v6-agent` based on `v6.8.0-alpha` (V6 Framework Core Foundation Baseline).**
> **Public baseline: `v6.0.0-alpha`.**

| Item | Value |
|---|---|
| Active branch | `v6-agent` |
| Framework Core baseline | `v6.8.0-alpha` |
| Frozen foundation branch | `v6-core` |
| Service extension branch | `v6-service` |
| Public baseline | `v6.0.0-alpha` |
| Internal migration checkpoint | `v6.5.8-alpha` (historical, on `v5-dev`) |
| Frozen archive | `v5-dev` |
| AI rule | Do not modify `v5-dev`. Framework Core (`v6-core`) only accepts bug fixes. Service work goes to `v6-service`. Agent work goes to `v6-agent`. |

See [`PROJECT_LINEAGE.md`](../PROJECT_LINEAGE.md) for the full V5 / V6 identity map.

## Mission
基于 `v6.8.0-alpha`（V6 Framework Core Foundation Baseline）在 `v6-agent` 分支上执行 **V6.8.0-alpha Baseline Validation**：构建一个最小真实 Agent 产品实例 `demo_agent/`，验证 Framework Core 能否承载完整端到端链路（Desktop UI → UIController → RuntimeAdapter → AgentRuntime → Orchestrator → PlannerLoop → Engine → Trace/Replay）。目标不是扩展 Runtime 能力，而是证明基座可用。

## Current Architecture State

> **V6 Framework Core Foundation 已闭环。**

### Runtime Communication Layer
**READY** — `v6/runtime/event_bus.py` 已升级为 Runtime Event Bus。

### Capability Discovery Layer
**READY** — `v6/runtime/capability_registry.py` 已落地。

### Runtime Replay Layer
**READY** — `v6/runtime/replay.py` 已落地（Deterministic Trace Replay Foundation）。

### Runtime Orchestration Layer
**READY** — `v6/runtime/orchestrator.py` 已落地（Runtime Orchestration Foundation）。

### Runtime Decision Layer
**READY** — `v6/runtime/planner_loop.py` / `decision.py` / `decision_policy.py` 已落地，补齐调度决策机制。

**重要边界**：
- `PlannerLoop`：Runtime 决策机制（Runtime decision mechanism）。
  - 输入：`RuntimeContext`
  - 输出：`Decision`
  - 事件驱动，通过 EventBus 发布决策事件。
  - 第一版无 LLM 依赖，使用 `RuleBasedDecisionPolicy`。
- `PlannerEngine`：八大 Engine 之一的能力组件（Engine capability）。
  - 未来职责：计划生成（plan generation）。
  - 当前为空壳，位于 `v6/runtime/engines/planner.py`。
- **二者刻意分离**，后续 Agent 接手时不应合并或混淆。

### Decision Flow
```
Orchestrator
  |
  v
PlannerLoop
  |
  v
Decision
  |
  v
CapabilityRegistry
  |
  v
EngineManager.execute(name, ctx)
```

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
  +------> Orchestrator
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

## V6 Branch Strategy

`v6.8.0-alpha` 起，V6 拆为三条垂直支线：

```
v6-dev
  |
  v6.8.0-alpha  ← Framework Core Foundation Baseline
      |
      +---- v6-core   (Runtime Kernel — bug fixes only)
      |
      +---- v6-service (Runtime Service Architecture)
      |
      +---- v6-agent   (Agent Application — current active)
```

**合并方向（强制单向）**：

```
v6-core  ──merge──►  v6-service  ──merge──►  v6-agent
```

- `v6-core` 的 bug fix 向下合并到 `v6-service` 和 `v6-agent`。
- `v6-service` 的能力向下合并到 `v6-agent`。
- **禁止反向合并**：`v6-agent`、`v6-service` 不得反向合并入 `v6-core`；`v6-agent` 不得反向合并入 `v6-service`。

### Guarantees
- Engine 不直接访问 `RuntimeTrace`；生命周期事件通过 `RuntimeEventBus` 路由。
- Engine 间通信使用标准 `RuntimeEvent`，禁止直接互相调用。
- `EngineManager` 负责 Engine 生命周期；`EventBus` 负责运行时通信；`CapabilityRegistry` 负责 Engine 选择；`ReplayService` 负责执行轨迹记录与回放基础；`Orchestrator` 负责任务编排与生命周期；`PlannerLoop` 负责 Runtime 决策；六者职责分离。
- `ReplayService` 不是 Engine，不替代 `EngineManager` 或 `EventBus`。
- `PlannerLoop` 是 Runtime 决策机制，`PlannerEngine` 是 Engine 能力组件，二者刻意分离。
- `Orchestrator` 是编排入口；`PlannerLoop` 只是其可调度的决策能力之一。
- 调用者不再硬编码 Engine 名称，而是描述能力需求。
- 第一版 Replay 只做轨迹记录、导出、查看，不重新执行 LLM/Tool/Memory。
- 第一版 Orchestrator / PlannerLoop 只做单次决策 + 线性执行，不做 LLM 决策与自治循环。
- 保持 Engine 单入口：`EngineManager.execute(name, ctx)` 继续作为 Runtime 调用 Engine 的唯一入口。

## Progress
- [x] Step 3 已归档：`v6/runtime/engine_state.py` 定义 `EngineState`；`v6/runtime/engines/protocol.py` 定义 `Engine` Protocol、`EngineDescriptor`、`EngineNotReadyError`；`EngineManager` 支持完整生命周期；标签 `v6.5.7-alpha`。
- [x] Step 4 已归档：新增 `BaseEngine` 与八大 Engine 空壳（LLM/Tool/Memory/Planner/Workflow/Code/Vision/Knowledge），Runtime Kernel 集成测试通过；标签 `v6.5.8-alpha`（内部迁移）。
- [x] V6 独立产品线立项：新增 `PROJECT_LINEAGE.md` 与 `Current Development Authority` 认知层；标签 `v6.0.0-alpha`（公开 baseline）。
- [x] Step 5.1 已归档：`v6/runtime/event_bus.py` 升级为 Runtime Event Bus Foundation；标签 `v6.6.0-alpha`。
- [x] Step 5.2 已归档：新增 `CapabilityRegistry`，八大 Engine 声明 capabilities；`EngineManager` 支持按能力选择；标签 `v6.6.1-alpha`。
- [x] Step 5.3 已归档：新增 `ReplayRecord` / `ReplayLog` / `ReplayService`，Runtime Execution Replay Foundation 落地；标签 `v6.6.2-alpha`。
- [x] Step 5.4 已归档：新增 `Orchestrator` 与 Task Lifecycle State Machine，AgentRuntime 持有 Orchestrator；标签 `v6.7.0-alpha`。
- [x] Step 5.5 / V6.8.0-alpha **Framework Core Foundation Baseline established**：新增 `PlannerLoop` / `Decision` / `DecisionPolicy`，Orchestrator 按决策选择 Engine；与前面四层共同构成 V6 Framework Core Foundation，作为后续 Service / Agent 开发的公共基线；标签 `v6.8.0-alpha`。
- [ ] **V6.8.0-alpha Baseline Validation**（基于 `v6-agent` 分支）：构建最小真实 Agent 产品实例 `demo_agent/`，验证 Framework Core 端到端可用性。通过后再进入 `v6-service` 的 Memory / Prompt / Model Adapter 等扩展。

## Step 5.5 / V6.8.0-alpha Details
- [x] 新增 `v6/runtime/decision.py`：定义 `DecisionAction` 枚举与 `Decision` 数据类，含工厂方法 `execute()` / `complete()` / `fail()` / `wait()`。
- [x] 新增 `v6/runtime/decision_policy.py`：定义 `DecisionPolicy` 基类与 `RuleBasedDecisionPolicy`，基于规则推断能力并选择 Engine。
- [x] 新增 `v6/runtime/planner_loop.py`：定义 `Observation` 与 `PlannerLoop`，包含 `observe()` / `decide()` / `evaluate()` / `plan()` / `on_event()`。
- [x] 升级 `v6/runtime/orchestrator.py`：
  - 构造函数支持注入 `PlannerLoop`。
  - `_execute_task()` 通过 `_make_decision()` 获取 `Decision` 并执行。
  - `_ensure_context()` 自动从 `ChatTask` 提取 `task_type` 与 `messages`。
  - `_on_task_started()` 增加 `CREATED` 状态防护，避免重入。
- [x] 升级 `v6/runtime/runtime.py`：
  - `AgentRuntime` 默认构造 `PlannerLoop` 并注入 `Orchestrator`。
  - 新增 `planner_loop` 属性。
- [x] 升级 `v6/runtime/engine_manager.py`：
  - 新增 `capability_registry` 只读属性。
- [x] 新增 `tests/v6/test_v6_planner_loop.py` 共 10 个测试。
- [x] V6 全量测试 `pytest tests/v6/` **175/175 通过**。

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

11. **决策**：新增独立的 `Orchestrator` 层，不让 Planner 成为 Runtime 大脑。
   - 排除：直接在 AgentRuntime 中调用 Planner 决策所有步骤——会把 Planner 与 Runtime 强耦合，无法替换 Rule Planner / Human Approval Planner 等。
   - 状态：已执行。

12. **决策**：Step 5.4 只做 Task Lifecycle State Machine + EventBus 驱动，不做 LLM 决策与自治循环。
   - 排除：立即实现 Observe → Reason → Plan → Act → Evaluate → Repeat 循环——基础状态机尚未稳定，且会引入不可控的复杂性。
   - 状态：已执行。

13. **决策**：Step 5.5 定义为 Planner Decision Loop Foundation，而非 Planner Engine 业务实现或自治 Agent 循环。
   - 排除：引入 LangChain Agent / ReAct / OpenAI function calling / MCP / Prompt Chain——会污染 Runtime 层。
   - 状态：已执行。

14. **决策**：`PlannerLoop` 与 `PlannerEngine` 刻意分离。
   - `PlannerLoop` 是 Runtime 决策机制（输入 `RuntimeContext`，输出 `Decision`，事件驱动）。
   - `PlannerEngine` 是八大 Engine 之一，未来负责计划生成（plan generation）。
   - 排除：把 `PlannerEngine` 提升为 Runtime 大脑——会造成 Runtime 与具体 Engine 强耦合，无法替换决策策略。
   - 状态：已执行。

15. **决策**：保持 `EngineManager.execute(name, ctx)` 作为 Runtime 调用 Engine 的唯一入口。
   - 排除：因 PlannerLoop 出现而改为 `planner.execute(task)` 等高阶抽象——会使 Runtime Kernel 退化为 Agent Framework。
   - 状态：已执行。

## Key Files
- `v6/runtime/planner_loop.py` — Runtime Decision Layer（PlannerLoop / Observation）。
- `v6/runtime/decision.py` — `DecisionAction` / `Decision` 模型。
- `v6/runtime/decision_policy.py` — `DecisionPolicy` 基类 + `RuleBasedDecisionPolicy`。
- `v6/runtime/orchestrator.py` — Runtime Orchestration Foundation（Task Lifecycle + EventBus 驱动 + PlannerLoop 集成）。
- `v6/runtime/runtime.py` — AgentRuntime（持有 Orchestrator / PlannerLoop / EngineManager / EventBus）。
- `v6/runtime/replay.py` — Runtime Execution Replay Foundation（ReplayRecord / ReplayLog / ReplayService）。
- `v6/runtime/event_bus.py` — Runtime Event Bus（神经系统）。
- `v6/runtime/capability_registry.py` — Engine 能力注册表（Capability Discovery）。
- `v6/runtime/engine_manager.py` — Engine 生命周期管理 + Capability 选择桥接。
- `v6/runtime/engines/base.py` — `BaseEngine` 统一生命周期与占位结果。
- `v6/runtime/engines/{llm,tool,memory,planner,workflow,code,vision,knowledge}.py` — 八大 Engine 空壳。
- `v6/runtime/engines/__init__.py` — 统一导出八大 Engine。
- `v6/runtime/engine_state.py` — `EngineState` 枚举（CREATED → ... → STOPPED）。
- `v6/runtime/engines/protocol.py` — `Engine` Protocol、`EngineDescriptor`、`EngineNotReadyError`。
- `tests/v6/test_v6_planner_loop.py` — Planner Decision Loop 测试。
- `tests/v6/test_v6_orchestrator.py` — Orchestrator 测试。
- `tests/v6/test_v6_runtime_kernel.py` — Runtime Kernel 集成测试（发现 / 生命周期 / Trace / Planner 编排）。
- `tests/v6/test_v6_engine_manager.py` — EngineManager 生命周期测试。
- `tests/v6/test_v6_capability_registry.py` — Capability Registry 测试。
- `tests/v6/test_v6_replay.py` — Replay Foundation 测试。
- `tests/v6/test_engine_protocol.py` — Engine Protocol、Descriptor、异常测试。
- `README.md` / `PROJECT_BLUEPRINT.md` / `PROJECT_LINEAGE.md` — V6 主线声明与项目状态。
- `docs/v6/SPEC.md` — V6 架构 SPEC（Runtime Interface Principle、Adapter Boundary 等）。

## Error Log
No error.

## Environment Snapshot
- branch: v6-dev
- python: Python 3.14.6
- venv: none
- last_commit: 7c9a276 feat(runtime): Step 5.4 Runtime Orchestration Foundation

## Working State
### Dirty Files
v6/runtime/decision.py
v6/runtime/decision_policy.py
v6/runtime/engine_manager.py
v6/runtime/orchestrator.py
v6/runtime/planner_loop.py
v6/runtime/runtime.py
tests/v6/test_v6_planner_loop.py
CHANGELOG.md
PROJECT_BLUEPRINT.md
.handoff/HANDOFF.md

### Uncommitted Changes Summary
新增 Planner Decision Loop Foundation：Decision 模型、规则决策策略、PlannerLoop、Orchestrator 集成、AgentRuntime 初始化、10 个测试；更新文档与日志。

### Recent Conversation
- 用户确认当前方向：V6 已形成 Runtime Kernel 雏形，不建议继续堆功能，应先归档 v6.8.0-alpha。
- 用户强调：v6.8.0-alpha 语义为 "V6 Runtime Autonomous Decision Foundation"，不是 Planner Engine。
- 用户明确 `PlannerLoop`（Runtime 决策机制）与 `PlannerEngine`（Engine 能力组件）必须分离。
- 用户建议 HANDOFF 增加 Decision Layer READY 与分离声明，避免后续 Agent 混淆。
- 用户建议下一步进入 Step 6 Runtime Service Architecture（Memory / Prompt / Model Adapter / Tool Adapter / Knowledge Adapter），而非自治循环。

## Next Steps (AI-Inferred)
1. **V6.8.0-alpha Baseline Validation**（当前最高优先级，基于 `v6-agent` 分支）
   - 目标：用最小真实 Agent 产品实例 `demo_agent/` 验证 Framework Core 能否承载完整端到端链路。
   - 结构：
     ```
     demo_agent/
     ├── ui/              # Desktop UI（Agent 产品层，非 Runtime Core）
     ├── app.py           # 应用入口
     ├── controller.py    # UIController
     ├── adapter.py       # RuntimeAdapter（Application Boundary）
     ├── config/          # agent 配置、prompt 工程、memory 工程
     └── tests/           # 端到端冒烟测试
     ```
   - 验证项：
     - 单 Agent 生命周期（submit → planning → executing → completed/failed）。
     - GUI 调用链（Desktop UI → UIController → RuntimeAdapter → AgentRuntime）。
     - LLM Engine 调用（占位或真实 OpenAI adapter，不污染 Core）。
     - Tool Engine 调用。
     - Trace 记录与 Replay 查看。
     - 配置加载。
     - 打包启动（PyInstaller）。
   - 不进入：用户权限系统、动态 UI Builder、MCP、Admin Panel、Memory Service、Prompt Service；这些属于后续 `v6-service` 或更远期 `v6-agent` 产品化工作。
2. **Step 6 / V6.9+：Runtime Service Architecture**（Baseline Validation 通过后，回到 `v6-service` 分支）
   - 目标：为 Runtime Kernel 接入真实世界能力层。
   - 候选服务：Memory Service、Prompt Service、Model Adapter、Tool Adapter、Knowledge Adapter。
   - 原则：Service 属于 Runtime 能力接入层，不是 Engine 业务逻辑；保持 `RuntimeContext` 作为唯一 Public Protocol。
3. **Runtime Task 模型完善**
   - 将 `RuntimeContext`、`RuntimeTrace`、`RuntimeMetrics`、`RuntimeResult` 进一步封装为 `RuntimeTask` 工厂产物，同时保持 Context 作为唯一 Public Protocol。
4. **未来：真正的 Replay Execution**
   - 待 checkpoint + snapshot + engine sandbox 成熟后，再推进 `replay(task)` 重新执行能力。
5. **未来：自治 Agent 循环（更远期）**
   - 不做 `observe → think → act → repeat` 式的 ReAct 循环；待 Service Architecture 与真实 Adapter 稳定后再评估是否需要多轮决策循环。

## Test Status
- latest: [test:175/175]
- command: `python -m pytest tests/v6/ -q --tb=short`

## Notes
- `v6-agent` 是当前活跃开发分支，已推送至 origin；`v6-dev` 作为 Framework Core Foundation 演进历史的母线保留。
- `v6.8.0-alpha` 是 **V6 Framework Core Foundation Baseline**（共享核心框架基座），不是普通功能版本，也不是 archive。它标志着 V6 Runtime 七要素（统一入口、统一协议、统一通信、能力发现、执行追踪、任务编排、调度决策）完整闭环，是后续 Agent / Service / Adapter 开发的长期依赖基线。
- 三条垂直支线：`v6-core`（冻结，只修 bug）→ `v6-service`（Runtime Service Architecture）→ `v6-agent`（Agent Application）。合并方向强制单向，禁止反向合并。
- `v6.5.8-alpha` 保留为内部迁移标签，指向 `v5-dev` 上的 `76c7871`；它记录 Step 4 在旧线上的最终成果，但不参与 V6 产品线后续演进。
- `v5-dev` 已冻结归档，其最后一个 V6 相关提交为 `76c7871`。
- 当前任务：在 `v6-agent` 上完成 **V6.8.0-alpha Baseline Validation**，通过后再回到 `v6-service` 推进 Memory / Prompt / Model Adapter 等扩展。
