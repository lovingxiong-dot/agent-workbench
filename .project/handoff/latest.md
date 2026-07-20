# Handoff Snapshot — Agent Workbench OS

> **会话 ID**: `6a5c85036d28e0576cc4cd51`
> **移交类型**: SAVE
> **移交日期**: 2026-07-19
> **接替日期**: 2026-07-20
> **移交 Agent**: DeepSeek-V4-Pro @ Trae IDE
> **接替 Agent**: DeepSeek-V4-Pro @ Trae IDE
> **当前进度**: v6.14 Dogfooding Phase 全部完成

---

## 1. 项目状态

| 项目 | 值 |
|------|-----|
| 项目名称 | agent-workbench |
| 当前版本 | v6.14.0-alpha |
| 阶段 | Dogfooding Phase — 全部完成 |
| Runtime 基线 | v6.9.6-foundation |
| 活跃分支 | `v6-agent` |
| 移交提交 | `0518302` |
| 工作区状态 | 干净 |
| 远程仓库 | `github.com:lovingxiong-dot/agent-workbench.git` |

---

## 2. v6.13 架构冻结总结

### 2.1 P0 架构修复（4/4 已完成）

| ID | 修复内容 | 状态 |
|----|---------|------|
| P0-1 | 统一入口 | ✅ |
| P0-2 | ConfigStore 解耦 PySide6 | ✅ |
| P0-3 | 流式事件走 Interaction Boundary | ✅ |
| P0-4 | SessionModule 消息存储 | ✅ |

### 2.2 Frozen Zone（19 个文件，禁止修改）

```
v6/runtime/orchestrator.py
v6/runtime/context.py
v6/runtime/event_bus.py
v6/runtime/runtime.py
v6/runtime/enums.py
v6/runtime/types.py
agent_workbench/runtime/capability/model.py
agent_workbench/runtime/capability/state.py
agent_workbench/runtime/capability/graph.py
agent_workbench/runtime/capability/chain.py
agent_workbench/runtime/interaction/request.py
agent_workbench/runtime/interaction/event.py
agent_workbench/runtime/interaction/renderer.py
agent_workbench/runtime/interaction/mapper.py
agent_workbench/runtime/interaction/layer.py
agent_workbench/runtime/config_store.py
agent_workbench/runtime/manager/decision_manager.py
agent_workbench/package/loader.py
agent_workbench/package/registry.py
```

### 2.3 四项禁止事项（永久生效）

1. Skill 不得进入 Runtime Kernel
2. Memory 不得进入 Capability
3. AgentIdentityRegistry 不负责执行
4. PackageRegistry 不保存运行状态

### 2.4 五个 Extension Point（允许新增）

- Module: `agent_workbench/runtime/modules/`
- Capability: `agent_workbench/runtime/capability/`
- Engine: `agent_workbench/engines/`
- Provider: `agent_workbench/services/`
- Package: `packages/`

---

## 3. v6.14 Dogfooding Phase — 全部完成

| # | 任务 | 优先级 | 状态 |
|---|------|--------|------|
| D0 | 修复 latest.md + 同步状态 | P0 | ✅ |
| D1 | CLI 流式输出 | P0 | ✅ |
| D2 | Session 持久化 | P0 | ✅ |
| D3 | 多轮上下文验证 | P0 | ✅ |
| D4 | Provider 运行时切换 | P1 | ✅ |
| D5 | Agent 选择器 | P1 | ✅ |

---

## 4. 完成记录

### D1: CLI 流式输出
- 新增: `agent_workbench/runtime/interaction/cli_renderer.py`
- 修改: `agent_workbench/app.py`
- 提交: `244cacd`

### D2: Session 持久化
- 修改: `session_module.py`, `controller.py`, `app.py`
- 提交: `0e31e77`

### D3: 多轮上下文验证
- 新增: `tests/v6/test_v6_multi_turn.py` (14 tests)
- 提交: `e64e3c9`

### D4: Provider 运行时切换
- 修改: `model_module.py`, `controller.py`
- 新增: `tests/v6/test_v6_provider_switch.py` (10 tests)
- 提交: `e745125`

### D5: Agent 选择器
- 新增: `packages/{personal,coding,research}_agent/manifest.yaml`
- 新增: `agent_workbench/runtime/modules/agent_module.py`
- 新增: `tests/v6/test_v6_agent.py` (10 tests)
- 修改: `agent_runtime.py`, `controller.py`, `app.py`

---

## 5. 测试基线

| 套件 | 结果 |
|------|------|
| 总计 | 381/388 PASS |
| 预存失败 | 7 (api_key is empty) |
| 新增测试 | 34 (D3: 14 + D4: 10 + D5: 10) |

---

## 6. CLI 命令参考

| 命令 | 功能 |
|------|------|
| `/agents` | 查看可用 Agent 列表 |
| `/agent <id>` | 切换到指定 Agent (personal_agent/coding_agent/research_agent) |
| `/agent` | 查看当前 Agent |
| `/model <name>` | 切换模型 |
| `/model` | 查看当前模型 |
| `/provider <name>` | 切换 Provider |
| `/provider` | 查看当前 Provider |

---

## 7. 架构文档

| 文档 | 路径 |
|------|------|
| 架构边界文档 | `docs/v6/architecture-boundaries.md` |
| 冻结报告 | `.project/architecture/v6.13-freeze-report.md` |