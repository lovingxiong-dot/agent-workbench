# ADR-011 — Controller API Surface Freeze

> **Status**: ACCEPTED
> **Date**: 2026-07-24
> **Supersedes**: None
> **Scope**: Application Layer — WorkbenchController public API boundary

---

## 1. Purpose

定义 `WorkbenchController` 的公共 API 面冻结规则，作为 Application Facade 的稳定契约。

---

## 2. Context

`WorkbenchController` 是 CLI / GUI / MCP / Remote Agent 的统一入口。当前约 300+ 行，职责覆盖：

```
Session API
Provider API
Model API
Agent API
Config API
Trace API
Package API
CLI API
Runtime Status API
```

短期需要冻结 API Surface，防止未来多 Shell 接入时出现不一致。

---

## 3. Decision

### 3.1 API Surface 冻结

以下方法为 `WorkbenchController` 的稳定公共 API，**不修改签名、不删除**：

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

### 3.2 访问规则

| 规则 | 说明 |
|------|------|
| Shell 只能访问 Controller 公共 API | 禁止直接访问 `controller.runtime` |
| Shell 只能访问 `controller.interaction_layer` | 通过 Interaction Boundary 提交请求 |
| Shell 禁止直接访问 `runtime.module_registry` | 所有 Module 访问通过 Controller 方法 |
| Shell 禁止直接调用 `runtime.decision_manager` | Decision 必须经过 Interaction Layer |
| 新 Shell 接入必须使用 Controller 或 Interaction Layer | 禁止直接访问 Runtime 内部 |

### 3.3 未来演进

Controller 职责膨胀时，可拆分为 Facade 模式：

```
WorkbenchController
        |
        +-- SessionFacade
        +-- ModelFacade
        +-- AgentFacade
        +-- PackageFacade
```

但当前阶段冻结，不提前拆分。

---

## 4. Consequences

- 所有 Shell 接入点统一，避免 API 漂移
- 新 Shell 开发者有明确的 API 边界
- Controller 膨胀风险已知，但推迟到下一阶段处理
- 修改 Controller 公共方法签名需要 ADR