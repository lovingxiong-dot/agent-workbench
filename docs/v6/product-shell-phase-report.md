# Phase 2-D Product Shell Integration — Final Report

> **Date**: 2026-07-24
> **Status**: CLOSED
> **Phase**: 2-D.6 Product Shell Closure
> **Scope**: Application Layer — CLI / GUI Shell Boundary & Controller Contract

---

## 1. Shell Architecture

```
                 Presentation Shells

        CLI              GUI              Web
         |                |                |
         └────────────────┼────────────────┘
                          |
                          ↓

              Workbench Control Layer
            (WorkbenchController)
                          |
                          ↓

              WorkbenchInteractionLayer
                          |
                          ↓

                  RuntimeRequest
                          |
                          ↓

                  Agent Runtime
                          |
                          ↓

              Capability / Provider Layer
```

CLI（`app.py::run_cli()`）和 GUI（`V6UIApplication`）共享同一 `WorkbenchController` 实例，不分别实现业务逻辑。

---

## 2. Controller Contract

### 冻结的公共 API Surface

| 方法 | 用途 | 消费者 |
|------|------|--------|
| `start()` / `stop()` | 生命周期 | CLI / GUI |
| `chat(text)` | 对话入口 | CLI / GUI |
| `submit_request(request)` | 非阻塞提交 | CLI / GUI / MCP |
| `submit_task(task)` | Task 提交 | Internal |
| `switch_agent(id)` | Agent 切换 | CLI / GUI |
| `switch_provider(name)` | Provider 切换 | CLI / GUI |
| `switch_model(name)` | 模型切换 | CLI / GUI |
| `list_agents()` | Agent 列表 | CLI / GUI |
| `list_providers()` | Provider 列表 | CLI / GUI |
| `list_models()` | 模型列表 | CLI / GUI |
| `get_active_agent()` | 当前 Agent | CLI / GUI |
| `get_active_agent_name()` | 当前 Agent 名 | CLI / GUI |
| `get_current_provider()` | 当前 Provider | CLI / GUI |
| `get_current_model()` | 当前模型 | CLI / GUI |
| `get_agent_name()` | 工作台名称 | CLI |
| `get_session_info()` | Session 摘要 | CLI |
| `get_status()` | Runtime 状态 | CLI |
| `get_config_summary()` | 配置摘要 | CLI |
| `preflight_check()` | Provider 就绪 | CLI / GUI |
| `get_state()` | 会话状态 | GUI |
| `get_overview()` | Overview 面板 | GUI |
| `get_module_metadata(ns)` | Capability Metadata | GUI |
| `apply_config_change(ns)` | 配置热更新 | GUI |
| `get_config_value(path)` | 配置读取 | CLI / GUI |
| `set_config_value(path, value)` | 配置写入 | CLI / GUI |
| `trace_timeline(task_id)` | Trace 查询 | GUI |
| `get_system_prompt()` | System Prompt | GUI |

### 访问规则

| 规则 | 说明 |
|------|------|
| Shell 只能访问 Controller 公共 API | 禁止直接访问 `controller.runtime` |
| Shell 只能访问 `controller.interaction_layer` | 通过 Interaction Boundary 提交请求 |
| Shell 禁止直接访问 `runtime.module_registry` | 所有 Module 访问通过 Controller 方法 |
| Shell 禁止直接调用 `runtime.decision_manager` | Decision 必须经过 Interaction Layer |
| 新 Shell 接入必须使用 Controller 或 Interaction Layer | 禁止直接访问 Runtime 内部 |

---

## 3. Interaction Boundary

```
User Input
    │
    ▼
RuntimeRequest
    │
    ▼
WorkbenchInteractionLayer
    │
    ├── submit_request() → AgentWorkbenchRuntime.submit_request()
    │   └── 非阻塞，返回 request_id
    │
    ├── execute_request() → DecisionManager.decide() → Runtime
    │   └── 阻塞，返回 RuntimeContext
    │
    └── EventBus 订阅 → RuntimeEvent → InteractionEvent → UIEventRenderer
```

### 冻结协议

| 协议 | 文件 | 状态 |
|------|------|------|
| `RuntimeRequest` | `runtime/interaction/request.py` | Frozen |
| `InteractionEvent` | `presentation/protocols/interaction/event.py` | Frozen |
| `UIEventRenderer` | `presentation/protocols/interaction/renderer.py` | Frozen |
| `WorkbenchInteractionLayer` | `runtime/interaction/layer.py` | Frozen |

---

## 4. Gate Results

### Gate 2 — Runtime Path Test

| Case | 描述 | 结果 |
|------|------|------|
| Case A | CLI → Controller → Runtime → Provider → Success | **PASS** |
| Case B | Provider Missing Credential → Friendly Error → No Task Failure | **PASS** |
| Case C | Switch Provider → Runtime uses new Provider | **PASS** |

### Gate 3 — Multi Shell Test

| Test | 描述 | 结果 |
|------|------|------|
| API Consistency | 同一 Controller 对 CLI/GUI 返回一致结果 | **PASS** |
| API Surface | 公共 API 面稳定，新增方法不破坏现有接口 | **PASS** |
| Interaction Layer | CLI/GUI 都通过 InteractionLayer 访问 Runtime | **PASS** |

### Gate 4 — Boundary Integrity Test

| Test | 描述 | 结果 |
|------|------|------|
| chat() → RuntimeRequest | chat() 通过 RuntimeRequest → InteractionLayer | **PASS** |
| No Direct Decision | chat() 不直接访问 DecisionManager | **PASS** |
| submit_request() → IL | submit_request() 通过 InteractionLayer | **PASS** |
| No DecisionManager API | Controller 公共 API 不暴露 decide/resolve | **PASS** |
| No module_registry | Controller 不暴露 module_registry 属性 | **PASS** |
| Legacy Bypass Known | execute_agent_action 标记为已知债务 | **PASS** |

### Gate 4 (追加) — Regression Test

| 套件 | 结果 |
|------|------|
| v6-core (tests/v6/) | **310/310 PASS, 7 SKIP (openai), 4 FAIL (pre-existing host_contract)** |
| Interaction Layer (tests/interaction/) | **30/30 PASS** |
| Product Shell Integration (tests/v6_10/) | **17/17 PASS** |
| Controller Interaction | **4/4 PASS + 1 SKIP (openai env)** |

> 注：4 个 host_contract 失败（`NavigatorHost.session_selected`、`set_sessions_expanded`、`InspectorHost.set_schema`、`StatusBarHost.set_runtime_status`）为 pre-existing v6/ui 架构问题，不在 Phase 2-D 范围内。Phase 2-D 期间 v6/ui 目录零变更。

---

## 5. Known Debt

| # | 项目 | 等级 | 记录 |
|----|------|------|------|
| 1 | `execute_agent_action` 绕过 Runtime | R1 | [ADR-010](file:///e:/Development/workbench/agent_workbench/.project/decisions/ADR-010-package-action-execution-boundary.md) |
| 2 | Controller 职责膨胀 | R1 | [ADR-011](file:///e:/Development/workbench/agent_workbench/.project/decisions/ADR-011-controller-api-surface-freeze.md) |
| 3 | `run_gui_v6()` 命名 | R2 | 未来 Phase 3 重命名 `run_desktop()` |
| 4 | v6/ui 仍属 Runtime namespace | R1 | 未来迁移至 `presentation/desktop/` |
| 5 | openai 包未安装 | 低 | 环境依赖，`pytest.mark.skipif` 已标记 |

---

## 6. Do Not Touch — Frozen Zone

以下文件在 Phase 2-D 期间**零修改**：

| 文件 | 说明 |
|------|------|
| `v6/runtime/context.py` | RuntimeContext Contract |
| `v6/runtime/event_bus.py` | RuntimeEvent Protocol |
| `v6/runtime/enums.py` | RuntimeState / RuntimePhase |
| `runtime/interaction/request.py` | RuntimeRequest Protocol |
| `presentation/protocols/interaction/event.py` | InteractionEvent Protocol |
| `runtime/agent_runtime.py` | AgentWorkbenchRuntime（未修改核心逻辑） |
| `v6/runtime/` 下所有文件 | Runtime Kernel |
| `v6/ui/` 下所有文件 | v6/ui Presentation Foundation |

---

## 7. Next Milestone

**Phase 3 — Capability Expansion**

建立在已冻结的 Shell Boundary 上：

- MCP Capability
- Browser Capability
- Workflow Runtime
- Skill Layer
- PackageCapabilityAdapter（替代 PackageExecutor Legacy Bypass）