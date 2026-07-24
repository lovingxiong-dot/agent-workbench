# ADR-010 — Package Action Execution Boundary

> **Status**: ACCEPTED (Temporary Debt)
> **Date**: 2026-07-24
> **Supersedes**: None
> **Scope**: Application Layer → Runtime boundary for Package Action execution

---

## 1. Purpose

记录 `WorkbenchController.execute_agent_action()` 当前绕过 Runtime 的已知架构债务，并明确未来演进路径。

---

## 2. Context

当前链路：

```
UI
 |
Controller
 |
PackageExecutor  ← 直接执行，绕过 Runtime
 |
Action
```

期望链路：

```
UI
 |
Controller
 |
RuntimeRequest
 |
InteractionLayer
 |
DecisionManager
 |
CapabilityResolver
 |
Task
 |
Engine
 |
PackageCapabilityAdapter
```

---

## 3. Decision

### 当前阶段（Product Shell Demo）

`execute_agent_action()` 直接调用 `PackageExecutor` **暂时允许**。

理由：
- Product Shell 阶段需要可观测的 Package Action 执行
- 完整链路（RuntimeRequest → Orchestrator → Tool Engine）尚未建立
- 方法注释已明确标记为过渡实现

### 风险等级

**R1** — 不破坏 Runtime Boundary，但绕过了 DecisionManager 和 Capability Resolver。

### 保护措施

- `execute_agent_action()` 通过 EventBus 发布 `TASK_STARTED` / `TASK_COMPLETED` 事件，使 Trace Workspace 可观测
- 该方法不直接调用 Provider API，不绕过 ModelModule
- 不创建 Runtime 对象，不操作 Capability 注册表

---

## 4. Future

下一阶段（Capability Expansion）应：

1. 建立 `PackageCapabilityAdapter` 替代 `PackageExecutor`
2. Package 注册为 `Capability Provider`
3. Package Action 通过 `RuntimeRequest → DecisionManager → Engine` 完整链路执行

届时 `execute_agent_action()` 应重构为：

```python
def execute_agent_action(self, package_id: str, action_id: str) -> Dict[str, Any]:
    request = RuntimeRequest(
        source=RuntimeRequestSource.WORKSPACE_ACTION,
        action_id="package_action",
        metadata={"package_id": package_id, "action_id": action_id},
    )
    return self._interaction.execute_request(request)
```

---

## 5. Consequences

- Product Shell 可运行 Package Action 预览
- 下一阶段必须重构，不可永久保留
- 新 Package Action 不应复制此模式