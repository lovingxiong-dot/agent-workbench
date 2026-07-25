# Phase 3.12-A — Validation Plan

> **Status**: PLAN — v0.1
> **Date**: 2026-07-25
> **Phase**: 3.12-A.5
> **Depends on**: 3.12-A.1 / A.2 / A.3 / A.4

---

## 1. Purpose

定义 Phase 3.12-A 实现的 Validation Strategy：
- Pure Function（Metric Algorithm）测试
- Tool 端到端（Adapter + Collector）测试
- Frozen Contract Boundary 验证
- Without Patching Runtime Layer 的不变量验证

---

## 2. 测试分层（60/40，继承 Phase 3.11-D Review）

### 60% Primitive Tests（Pure Functions）

#### Metric 1 — Execution Latency

```python
def test_latency_normal_completion():
    """TASK_STARTED (t=0), TASK_COMPLETED (t=1.5) → 1500ms."""

def test_latency_no_start_returns_none():
    events = [make_event(TASK_COMPLETED, t=1.0)]
    assert execution_latency_ms(events, "task-1") is None

def test_latency_no_terminal_returns_none():
    events = [make_event(TASK_STARTED, t=0)]
    assert execution_latency_ms(events, "task-1") is None

def test_latency_invalid_order_returns_none():
    events = [
        make_event(TASK_COMPLETED, t=0.5),
        make_event(TASK_STARTED, t=1.0),
    ]
    assert execution_latency_ms(events, "task-1") is None

def test_latency_failed_uses_failed_as_terminal():
    """TASK_STARTED (t=0), TASK_FAILED (t=2) → 2000ms."""

def test_latency_cancelled_uses_cancelled_as_terminal():
    """TASK_STARTED (t=0), TASK_CANCELLED (t=3) → 3000ms."""
```

#### Metric 2 — Cancellation Propagation Latency

```python
def test_cancellation_propagation_user_request():
    event = make_cancel_event(
        initiated_at="2026-07-25T10:00:00+00:00",
        timestamp=time.time() + 0.05,  # 50ms 后
    )
    delta = cancellation_propagation_ms(event)
    assert 0 < delta < 100  # 在毫秒级精度内

def test_cancellation_propagation_no_initiated_at():
    event = make_event(TASK_CANCELLED, payload={"reason": "x"})
    assert cancellation_propagation_ms(event) is None

def test_cancellation_propagation_invalid_format():
    event = make_event(TASK_CANCELLED, payload={"initiated_at": "garbage"})
    assert cancellation_propagation_ms(event) is None
```

#### Metric 3 — Deadline Accuracy

```python
def test_deadline_error_late():
    """deadline_at = now - 1s, terminal at now → +1000ms."""

def test_deadline_error_early():
    """deadline_at = now + 1s, terminal at now → -1000ms."""

def test_deadline_error_no_deadline_returns_none():
    metadata = ExecutionMetadata(task_id="t1")  # 无 deadline
    assert deadline_error_ms(events, metadata, "task-1") is None

def test_deadline_error_no_terminal_returns_none():
    metadata = ExecutionMetadata(task_id="t1", deadline_at=now())
    events = [make_event(TASK_STARTED)]
    assert deadline_error_ms(events, metadata, "task-1") is None
```

#### Metric 4 — Event Throughput

```python
def test_throughput_10_events_per_second():
    """10 events 在 1 秒窗口 → 10 events/sec."""

def test_throughput_zero_window_returns_none():
    """window 大小为 0 → None（避免除零）."""

def test_throughput_empty_events_returns_none():
    assert event_throughput([]) is None
```

#### Metric 5 — Registry Footprint

```python
def test_footprint_empty_registry():
    footprint = registry_footprint(ExecutionRegistry(), known_ids=[])
    assert footprint.entries == 0
    assert footprint.active_entries == 0

def test_footprint_with_active_and_terminal():
    registry = ExecutionRegistry()
    registry.register("exec-1", "t1", None)
    registry.mark_terminated("exec-1")
    registry.register("exec-2", "t2", "exec-1")
    # exec-1 terminal + active reference 保留
    # exec-2 active
    footprint = registry_footprint(
        registry,
        known_execution_ids=["exec-1", "exec-2"]
    )
    assert footprint.entries == 2
    assert footprint.active_entries == 1
    assert footprint.terminal_entries == 1
```

### 40% Integration Tests（Tool 端到端）

```python
def test_evidence_collector_with_runtime_eventbus(bus, orch):
    """从 RuntimeEventBus + ExecutionRegistry 生成完整 ObservationReport."""

def test_evidence_collector_handles_no_events(bus, orch):
    """无任务执行时返回 metrics 都是 None."""

def test_observation_report_to_dict_is_serializable():
    """ObservationReport.to_dict() 输出可被 json.dumps()."""
    report = ObservationReport(...)
    payload = json.dumps(report.to_dict())
    assert payload is not None
```

---

## 3. Frozen Contract Boundary Validation

### 3.1 不变量验证

```python
def test_observation_does_not_modify_event_bus(bus):
    """Observation Tool 启动后，EventBus._subscribers 集合不变."""
    bus.subscribe(RuntimeEventType.TASK_STARTED, observer_callback)
    initial_subscribers = dict(bus._subscribers)
    # 触发 Observation Tool 运行
    collector = EvidenceCollector(bus=bus)
    collector.collect_observation("task-1", window=timedelta(seconds=1))
    # 验证未污染
    assert dict(bus._subscribers) == initial_subscribers

def test_observation_does_not_modify_registry(orch):
    """Observation Tool 不修改 ExecutionRegistry 状态."""
    initial_count = len([n for n in orch.execution_registry._nodes.values()])
    collector = EvidenceCollector(registry=orch.execution_registry)
    collector.collect_observation("task-1", window=timedelta(seconds=1))
    final_count = len([n for n in orch.execution_registry._nodes.values()])
    assert initial_count == final_count

def test_observation_does_not_publish_runtime_events(bus):
    """Observation Tool 不通过 EventBus.publish() 发布新事件."""
    publish_count_before = bus.metrics.total_published  # 假设有 metrics
    collector = EvidenceCollector(bus=bus)
    collector.collect_observation(...)
    publish_count_after = bus.metrics.total_published
    assert publish_count_before == publish_count_after

def test_observation_tools_have_no_runtime_write_imports():
    """静态检查：tools/observation/ 禁止 import Runtime 写模块."""
    # 检查 import 链：禁止 import Orchestrator / EngineManager / PlannerLoop
    # 允许 import: RuntimeEvent / RuntimeState / ExecutionMetadata / ExecutionRegistry
```

### 3.2 边界依赖图检查

```
tools/observation/
  ├─ adapters/  → v6.runtime.event_bus (read-only types)
  ├─ derived/   → no Runtime imports (pure functions)
  ├─ reports/   → no Runtime imports (data classes)
  └─ collectors/ → adapters + derived (orchestration only)
```

依赖方向：
```
v6.runtime.* (frozen) ← tools/observation/* (read)
```

禁止反向：
```
tools/observation/* → v6.runtime.Orchestrator (read-and-execute)
```

---

## 4. Do Not Touch Verification（运行时自动检查）

```python
# tests/v6/observation/test_boundary_compliance.py

import ast
import pathlib
import pytest


OBSERVATION_TOOL_DIR = pathlib.Path("tools/observation")

FORBIDDEN_IMPORTS = {
    # Runtime Component（不允许 import）
    "v6.runtime.orchestrator",
    "v6.runtime.engine_manager",
    "v6.runtime.planner_loop",
    "v6.runtime.capability_router",
    # AgentWorkbench Contract（不允许写）
    "agent_workbench.runtime.decision",
    "agent_workbench.runtime.capability",
    # CapabilityRegistry（v6.9.6 冻结）
    "agent_workbench.runtime.capability_registry",
}

# Allowed Runtime reads
ALLOWED_IMPORTS = {
    "v6.runtime.event_bus",
    "v6.runtime.enums",
    "v6.runtime.execution_metadata",
    "v6.runtime.execution_registry",
    "v6.runtime.cancellation_propagation",
    "v6.runtime.trace",
}


def test_no_forbidden_imports():
    """静态检查 Observation Tool 不 import Runtime 写模块."""
    for py_file in OBSERVATION_TOOL_DIR.rglob("*.py"):
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for forbidden in FORBIDDEN_IMPORTS:
                    if module.startswith(forbidden):
                        pytest.fail(
                            f"{py_file} imports forbidden module {module}"
                        )
```

---

## 5. Coverage Targets

| 类别 | 目标覆盖率 |
|------|-----------|
| Primitive Tests | 100%（Pure Functions 无副作用，可全面覆盖） |
| Integration Tests | 80%+（依赖 Frozen Runtime 的部分） |
| Boundary Tests | 100%（静态 import 检查） |

---

## 6. Status

| Plan | 内容 | 状态 |
|------|------|------|
| 3.12-A.1 | Design Document | ✅ APPROVED |
| 3.12-A.2 | Observation Contract | 🟡 Pending Review |
| 3.12-A.3 | Evidence Collection | 🟡 Pending Review |
| 3.12-A.4 | Derived Metrics Spec | 🟡 Pending Review |
| 3.12-A.4 | ObservationReport Schema | 🟡 Pending Review |
| 3.12-A.5 | Validation Plan（本） | 🟡 Pending Review |
| 3.12-A.6 | Tool Implementation | ⏳ Pending |
| 3.12-A.7 | Validation Report | ⏳ Pending |