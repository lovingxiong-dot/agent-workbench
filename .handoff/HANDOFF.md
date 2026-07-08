---
generated: 2026-07-08T15:30:00+08:00
agent: Kimi-K2.7-Code
schema_version: 3.1

## Mission

完成 v6.9.3-alpha "Multi-Capability Runtime & Manager Routing" 的规划、存档与交接，确保后续实施者能无缝从 Commit 0 开始，按顺序执行 Commit 0~5，不并行、不提前做 UI。

## Progress

- [x] v6.9.2-alpha 已作为 Single Agent Runtime Foundation 封板并移交（tag: `v6.9.2-alpha`）。
- [x] v6.9.3-alpha 实施计划已制定，并经架构反馈调整后定稿。
- [x] 计划文件已强制纳入版本控制：`.trae/documents/v6.9.3_multi_capability_runtime_plan.md`。
- [x] `PROJECT_BLUEPRINT.md` 已更新：版本号 `v6.9.3-alpha`、存档次数 `39`、项目概要、当前任务、开发约束。
- [x] `CHANGELOG.md` 已新增 `v6.9.3-alpha (Planning Approved)` 条目。
- [x] 已提交并打标签 `v6.9.3-alpha`，已推送分支 `v6-agent` 与标签到 Gitee 远程。
- [ ] Commit 0 ~ Commit 5 待后续实施者按顺序执行。

## Blocker

无技术卡点。当前处于**规划已批准、等待实施**状态。

## Decision Log

1. **决策：Capability Registry 放在 `agent_workbench/runtime/capability/` 而非 `services/`**
   - 原因：Capability 承担 Runtime 能力发现、Routing、Graph、Execution Mapping，属于 Runtime Domain Model，不是 Application Service。放到 Runtime 层可避免 `runtime -> services -> runtime` 的依赖倒置。
   - 排除：最初计划放在 `agent_workbench/services/capability_registry.py`，因位置偏 Service 而被调整。
   - 状态：已执行。

2. **决策：Capability Graph 第一版实际实现为 Tree**
   - 原因：v6.9.3 不做 DAG、图搜索、权重传播、自动规划。Tree（parent_id + children + lineage）已足够支撑能力层次与路径。
   - 排除：直接实现 Capability Graph 复杂算法。
   - 状态：已执行。

3. **决策：Task 五字段保持不变，所有扩展进 metadata/payload**
   - 原因：Task 是 Runtime Contract，膨胀后会破坏 Foundation。metadata 类比 HTTP Headers，扩展空间足够。
   - 排除：在 Task 上新增 `chain`、`persona`、`routing`、`provider` 等字段。
   - 状态：已执行。

4. **决策：ManagerRuntime 成为默认 Manager，AgentManager 保留为 Legacy Adapter**
   - 原因：实现真正的 Runtime 解耦，同时避免旧测试大面积震荡。
   - 排除：直接删除 `AgentManager` 或同时保留两个默认 Manager。
   - 状态：已执行。

5. **决策：Capability Chain 第一版仅静态链，不控制 Engine/Provider/Policy/Retry**
   - 原因：防止 Chain 变成第二套 Planner。
   - 排除：允许链动态扩展、链内切换 Provider、链内重试。
   - 状态：已执行。

6. **决策：UI Bridge 第一版只读，且默认可关闭**
   - 原因：v6.9.3 前半段主要验证 CLI/Test Runtime Path，后半段再打开 UI；避免 UI 反向污染 Runtime。
   - 排除：v6.9.3 一开始就双向交互。
   - 状态：已执行。

7. **决策：能力树根节点使用 `assistant` 而非 `manager`**
   - 原因：Manager 是调度器，不是能力；避免 `Manager → Manager Capability` 语义混淆。
   - 排除：根节点叫 `manager` 或 `capability.root`。
   - 状态：已执行。

## Key Files

- `.trae/documents/v6.9.3_multi_capability_runtime_plan.md` — v6.9.3 完整实施计划（已提交到版本库）。
- `PROJECT_BLUEPRINT.md` — 已更新当前版本为 `v6.9.3-alpha`，记录实施目标与开发约束。
- `CHANGELOG.md` — 已新增 `v6.9.3-alpha (Planning Approved)` 条目。
- `agent_workbench/runtime/capability/` — 待创建：model.py / graph.py / chain.py。
- `agent_workbench/runtime/manager/runtime.py` — 待创建：`ManagerRuntime`。
- `agent_workbench/runtime/capability_router.py` — 待升级接入 `CapabilityRegistry`。
- `agent_workbench/runtime/agent_runtime.py` — 待实例化 `CapabilityRegistry` 并注入。
- `agent_workbench/controller.py` — 待默认注入 `ManagerRuntime`。
- `v6/runtime/orchestrator.py` — 待支持 `capability_chain` 静态链执行。
- `v6/runtime/event_bus.py` — 待新增 Manager 级事件类型。
- `agent_workbench/services/manager.py` — 保留为 Legacy Adapter，不删除。
- `agent_workbench/ui/workbench_runtime_bridge.py` — Commit 5 待创建。

## Error Log

无错误。工作区干净。

## Environment Snapshot

- branch: `v6-agent`
- python: `Python 3.14.6`
- venv: `none`
- last_commit: `c3e599d docs(plan): v6.9.3-alpha Multi-Capability Runtime and Manager Routing implementation plan [test:210/210] [hint:v6.9.3-alpha plan] (by AI-Kimi-K2.7-Code)`
- last_tag: `v6.9.3-alpha`

## Working State

### Dirty Files

working tree clean

### Uncommitted Changes Summary

no uncommitted changes

### Recent Conversation

- 用户提供 v6.9.3-alpha 详细架构设想，强调 Multi-Capability 而非 Multi-Agent，明确 Manager / Capability Registry / Capability Graph / Capability Chain / Manager Policy 五阶段。
- 我进入 Plan Mode 制定实施计划，用户反馈 6 条微调和 5 条开发约束，特别要求先存档 push + 移交所有内容。
- 用户选择「强制添加计划文件」到版本控制。
- 我更新计划、PROJECT_BLUEPRINT.md、CHANGELOG.md，提交并打标签 `v6.9.3-alpha`，推送完成。

## Next Steps (AI-Inferred)

1. **执行 Commit 0 Runtime Contract**：创建 `agent_workbench/runtime/capability/model.py` / `chain.py` / `graph.py`（空壳）/ `agent_workbench/runtime/manager/runtime.py`（空壳），在 `v6/runtime/event_bus.py` 新增 Manager 事件类型，新增对应测试并验证通过。
2. **执行 Commit 1 Capability Runtime**：实现能力树 `CapabilityRegistry`，新增 `tests/v6/runtime/test_capability_registry.py`，验证通过。
3. **执行 Commit 2 Manager Routing**：实现 `ManagerRuntime`，`WorkbenchController` 默认注入，`AgentManager` 保留；新增 `tests/v6/runtime/test_manager.py`。
4. **执行 Commit 3 Capability Resolution**：升级 `CapabilityRouter`，新增 `tests/v6/runtime/test_router.py`。
5. **执行 Commit 4 Capability Chain**：升级 `Orchestrator`，新增 `tests/v6/runtime/test_capability_chain.py`。
6. **执行 Commit 5 Workbench Runtime Bridge**：新增只读 Bridge，默认可关闭，补充 UI 测试。
7. **最终验收**：全量测试 260~280 passed；验证「分析这个 Python 项目并修复 bug」生成 coding 能力链并顺序执行。

## Test Status

- latest: `[test:210/210]`（来自最新提交 message）
- command: `$env:PYTHONPATH="."; pytest tests/v6/ agent_workbench/tests/ -q`

## Notes

- 计划文件路径 `.trae/documents/v6.9.3_multi_capability_runtime_plan.md` 原本在 `.gitignore` 中，本次已强制提交，确保交接时计划本身随仓库一起传递。
- v6.9.3 的核心价值是第一次把 Capability 从「属性」提升为 Runtime 一级对象。这一步完成后，Agent Identity、多专家 Agent、AgentBus 才有稳定承载层。
- 不要并行执行 Commit，尤其不要先做 UI。
