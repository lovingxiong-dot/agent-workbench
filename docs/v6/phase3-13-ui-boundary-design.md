# Phase 3.13 — UI Boundary Design

> **Status**: DESIGN DRAFT v0.1
> **Date**: 2026-07-25
> **Phase**: 3.13
> **Depends on**: ADR-017 (Observation Presentation Boundary)

---

## 1. Purpose

定义 Phase 3.13 的 UI 集成点与边界，确认为 Read-only Panel 且不修改 v6/presentation/ 已 frozen 部分。

---

## 2. v6/presentation/ 现状

```
v6/presentation/  (Frozen Phase 3.10)
├── __init__.py
├── models.py                    # Frozen (TracePresentationModel 等)
├── contracts/                   # Frozen
│   ├── adapter_contract.py
│   ├── model_contract.py
│   └── renderer_contract.py
├── adapters/                    # 允许通过此处扩展
│   ├── composite_renderer.py
│   ├── console_renderer.py
│   ├── event_adapter.py
│   ├── runtime_adapter.py
│   └── session_adapter.py
├── renderers/                   # Frozen
├── design/                      # Frozen
├── demo_provider.py
├── design_tokens.py
├── golden_path_demo.py
└── renderer_registry.py
```

**关键**：v6/presentation/ 已 frozen（Phase 3.10 验证）。Phase 3.13 **不修改** v6/presentation/ 任何 frozen 文件。

---

## 3. Phase 3.13 UI 集成策略

### 3.1 主位置：`tools/presentation/`

```
tools/presentation/  (Phase 3.13 主位置)
├── __init__.py
├── view_models/                # Frozen ViewModel
│   ├── __init__.py
│   ├── observation_view_model.py
│   ├── runtime_status_view.py
│   ├── performance_view.py
│   ├── resource_view.py
│   └── lifecycle_view.py
├── adapters/                   # Observation → ViewModel
│   ├── __init__.py
│   └── observation_to_view_model.py
├── exports/                    # JSON / Markdown / Snapshot
│   ├── __init__.py
│   ├── json_export.py
│   ├── markdown_export.py
│   └── snapshot_export.py
└── README.md
```

### 3.2 UI 集成点：`v6/presentation/observation/`

```
v6/presentation/observation/  (NEW Phase 3.13 UI 集成)
├── __init__.py
├── observation_panel.py        # Read-only UI Component
├── observation_renderer.py     # 渲染器
└── README.md
```

**注意**：`v6/presentation/observation/` 是 **新增** 子目录（非修改 frozen `v6/presentation/models.py`）。

### 3.3 集成数据流

```
ObservationReport (Phase 3.12 Frozen ADR-016)
        |
        | tools/presentation/adapters/observation_to_view_model.py
        v
ObservationViewModel (frozen, tools/presentation/view_models/)
        |
        | v6/presentation/observation/observation_renderer.py
        v
UI Component (Read-only Display)
        |
        v
Workbench UI
```

---

## 4. Read-Only Panel 设计

### 4.1 Runtime Observation Panel

```python
# v6/presentation/observation/observation_panel.py

class RuntimeObservationPanel:
    """Read-only UI Panel for Observation Data.

    边界 (ADR-017 Decision 8):
    - 不注册 EventBus publish
    - 不修改 Runtime 状态
    - 不持有 Orchestrator / EngineManager 引用
    - 不启动 Worker / Polling
    """
    def __init__(self, view_model: ObservationViewModel) -> None:
        self._vm = view_model  # frozen

    def render(self) -> UIComponent:
        """渲染 Read-only Display。"""
        return UIComponent(
            runtime_status=self._vm.runtime_status,
            performance=self._vm.performance,
            resource=self._vm.resource,
            lifecycle=self._vm.lifecycle,
        )
```

### 4.2 4 组 View（继承自 ObservationViewModel）

| View Section | 数据源 | UI 元素 |
|--------------|--------|---------|
| RuntimeStatusView | ObservationReport.data_sources + 事件流 | active / completed / failed counts |
| PerformanceView | ObservationReport.metrics | duration / throughput |
| ResourceView | ObservationReport.registry_footprint | entries / depth / memory |
| LifecycleView | ObservationReport.metrics | cancellation / deadline |

### 4.3 用户交互（仅 Read-only Data Flow）

- ✅ 点击 Export → 触发 Export 模块（不修改 Runtime）
- ✅ 切换 View → 切换不同 ViewModel
- ❌ 不允许任何修改 Runtime 的操作
- ❌ 不允许任何启动 Worker 的操作

---

## 5. UI Boundary 验证

### 5.1 静态 import 检查（继承 ADR-016 + 新增）

```python
# tests/tools/presentation/test_boundary_compliance.py

PHASE_3_13_FORBIDDEN = (
    # 继承 ADR-016
    "v6.runtime.orchestrator",
    "v6.runtime.engine_manager",
    "v6.runtime.planner_loop",
    "v6.runtime.capability_router",
    "agent_workbench.runtime.capability",
    "agent_workbench.runtime.decision",
    "agent_workbench.runtime.capability_registry",
    "agent_workbench.runtime.capability_router",
    "agent_workbench.runtime.decision_dispatcher",
    # Phase 3.13 新增
    "v6.presentation.models",     # 禁止修改 frozen
    "v6.presentation.contracts",  # 禁止修改 frozen
)
```

### 5.2 v6/presentation 零修改验证

Phase 3.13 实现后：
- v6/presentation/models.py: **0 modification**（git diff 必须无改动）
- v6/presentation/contracts/: **0 modification**
- v6/presentation/renderers/: **0 modification**
- v6/presentation/design/: **0 modification**
- v6/presentation/observation/: **NEW**（仅新增）

---

## 6. UI Boundary 不变量

| 不变量 | 验证 |
|--------|------|
| `v6/presentation/models.py` 零修改 | git diff |
| Panel 不持有 Runtime 引用 | Static import check |
| Panel 不 subscribe write event | Runtime event hook check |
| ViewModel 是 frozen dataclass | @dataclass(frozen=True) |
| Adapter 单向数据流 | code review |
| Export schema = observation.v0.1 | 单元测试 |

---

## 7. 与 Phase 3.14 边界

| 类别 | Phase 3.13 | Phase 3.14+ |
|------|-----------|------------|
| Human UI Panel | ✅ Read-only Panel | ⏳ Dashboard |
| Agent Consumption | ❌ 禁止 | ⏳ Agent-readable |
| Persistence | ❌ File write only | ⏳ DB / Storage |
| Multi-Observation | ❌ Single observation | ⏳ Aggregation |
| Alerting | ❌ 禁止 | ⏳ 需新 ADR |

---

## 8. References

- [Phase 3.13 Scope Definition](phase3-13-presentation-consumption-design.md)
- [ADR-017 Observation Presentation Boundary](../../.project/decisions/ADR-017-observation-presentation-boundary.md)
- [ADR-016 Observation Layer Contract](../../.project/decisions/ADR-016-observation-layer-contract.md)
- v6/presentation/ (Frozen Phase 3.10)